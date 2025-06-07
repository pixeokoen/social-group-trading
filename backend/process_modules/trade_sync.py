"""
Trade Sync Process Module

Handles synchronization of trade data with Alpaca broker.
Consolidates all trade-related syncing into a single, manageable process.
"""

import asyncio
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timedelta

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db import get_db_connection
from alpaca_client import AlpacaClient

logger = logging.getLogger(__name__)

async def sync_trades_process():
    """
    Consolidated trade sync process that handles:
    - Order status updates
    - Trade fills
    - Level processing
    - Position updates
    """
    
    api_calls_made = 0
    conn = None
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get all active accounts
        cursor.execute("""
            SELECT DISTINCT a.id, a.api_key, a.api_secret, a.account_type
            FROM accounts a
            JOIN trades t ON a.id = t.account_id
            WHERE a.is_active = TRUE 
            AND a.broker = 'alpaca'
            AND t.status IN ('pending', 'open', 'filled')
        """)
        
        accounts = cursor.fetchall()
        logger.debug(f"Found {len(accounts)} active accounts to sync")
        
        for account in accounts:
            try:
                account_id, api_key, api_secret, account_type = account
                
                # Get broker client
                client = AlpacaClient(
                    api_key=api_key,
                    secret_key=api_secret,
                    paper=(account_type == 'paper')
                )
                
                # Sync pending trades
                await sync_pending_trades(cursor, client, account_id)
                api_calls_made += 3  # Estimated API calls for pending trades
                
                # Update current prices for open positions
                await update_position_prices(cursor, client, account_id)
                api_calls_made += 2  # Estimated API calls for price updates
                
            except Exception as e:
                logger.error(f"Error syncing account {account_id}: {e}")
                continue
        
        conn.commit()
        
        # Track API usage (will be handled by script manager when integrated)
        
        logger.debug(f"Trade sync completed - made {api_calls_made} API calls")
        
    except Exception as e:
        logger.error(f"Error in trade sync process: {e}")
        if conn:
            conn.rollback()
    
    finally:
        if conn:
            conn.close()

async def sync_pending_trades(cursor, client: AlpacaClient, account_id: int):
    """Sync pending trades for a specific account"""
    
    # Get pending trades
    cursor.execute("""
        SELECT id, broker_order_id, symbol, status
        FROM trades 
        WHERE account_id = %s 
        AND status = 'pending'
        AND broker_order_id IS NOT NULL
    """, (account_id,))
    
    pending_trades = cursor.fetchall()
    
    for trade in pending_trades:
        try:
            trade_id, broker_order_id, symbol, current_status = trade
            
            # Get order status from broker
            order_status = await client.get_order_status(broker_order_id)
            
            if order_status and order_status['status'] == 'filled':
                # Order filled - update trade
                fill_price = float(order_status.get('filled_avg_price', 0))
                filled_qty = float(order_status.get('filled_qty', 0))
                
                cursor.execute("""
                    UPDATE trades 
                    SET status = 'filled',
                        broker_fill_price = %s,
                        entry_price = %s,
                        quantity = %s,
                        opened_at = %s
                    WHERE id = %s
                """, (
                    fill_price,
                    fill_price,
                    filled_qty,
                    order_status.get('filled_at'),
                    trade_id
                ))
                
                logger.info(f"✅ Trade {symbol} filled at ${fill_price} - {filled_qty} shares")
                
                # Process take profit and stop loss levels
                await process_trade_levels_if_needed(cursor, trade_id, fill_price, filled_qty)
                
            elif order_status and order_status['status'] in ['cancelled', 'rejected']:
                # Order cancelled/rejected
                cursor.execute("""
                    UPDATE trades 
                    SET status = 'cancelled',
                        close_reason = %s
                    WHERE id = %s
                """, (order_status.get('status', 'cancelled'), trade_id))
                
                logger.info(f"❌ Trade {symbol} {order_status['status']}")
                
        except Exception as e:
            logger.error(f"Error syncing trade {trade_id}: {e}")
            continue

async def update_position_prices(cursor, client: AlpacaClient, account_id: int):
    """Update current prices for open positions"""
    
    # Get open trades that need price updates
    cursor.execute("""
        SELECT id, symbol, entry_price, quantity, action
        FROM trades 
        WHERE account_id = %s 
        AND status IN ('filled', 'open')
        AND current_price IS NULL
    """, (account_id,))
    
    open_trades = cursor.fetchall()
    
    if not open_trades:
        return
    
    # Get unique symbols
    symbols = list(set(trade[1] for trade in open_trades))
    
    try:
        # Batch get current prices
        current_prices = await client.get_current_prices(symbols)
        
        # Update each trade
        for trade in open_trades:
            trade_id, symbol, entry_price, quantity, action = trade
            
            if symbol in current_prices:
                current_price = current_prices[symbol]
                
                # Calculate floating P&L
                if action.upper() == 'BUY':
                    floating_pnl = (current_price - entry_price) * quantity
                else:
                    floating_pnl = (entry_price - current_price) * quantity
                
                cursor.execute("""
                    UPDATE trades 
                    SET current_price = %s,
                        floating_pnl = %s
                    WHERE id = %s
                """, (current_price, floating_pnl, trade_id))
                
        logger.debug(f"Updated prices for {len(open_trades)} positions")
        
    except Exception as e:
        logger.error(f"Error updating position prices: {e}")

async def process_trade_levels_if_needed(cursor, trade_id: int, fill_price: float, filled_qty: float):
    """Process take profit and stop loss levels if not already done"""
    
    # Check if levels already exist
    cursor.execute("""
        SELECT 
            (SELECT COUNT(*) FROM take_profit_levels WHERE trade_id = %s) as tp_count,
            (SELECT COUNT(*) FROM stop_loss_levels WHERE trade_id = %s) as sl_count
    """, (trade_id, trade_id))
    
    result = cursor.fetchone()
    tp_count, sl_count = result if result else (0, 0)
    
    # Skip if levels already processed
    if tp_count > 0 or sl_count > 0:
        return
    
    try:
        # Get signal data
        cursor.execute("""
            SELECT s.* FROM signals s
            JOIN trades t ON t.signal_id = s.id
            WHERE t.id = %s
        """, (trade_id,))
        
        signal_data = cursor.fetchone()
        
        if signal_data:
            # Convert to dict
            signal_dict = dict(zip([desc[0] for desc in cursor.description], signal_data))
            
            # Check for custom levels
            cursor.execute("""
                SELECT data FROM trade_notifications 
                WHERE trade_id = %s AND data->>'notification_type' = 'custom_levels_pending'
                ORDER BY created_at DESC LIMIT 1
            """, (trade_id,))
            
            custom_levels_row = cursor.fetchone()
            custom_levels = None
            
            if custom_levels_row:
                notification_data = custom_levels_row[0]
                custom_levels = notification_data.get('custom_levels')
            
            # Import and call the existing process_trade_levels function
            from main import process_trade_levels
            await process_trade_levels(trade_id, signal_dict, filled_qty, fill_price, cursor, custom_levels)
            
            logger.info(f"✅ Processed levels for trade {trade_id}")
            
    except Exception as e:
        logger.error(f"Error processing levels for trade {trade_id}: {e}")

# Function decorator to mark API calls
def api_calls(count: int):
    """Decorator to mark function's API call count"""
    def decorator(func):
        func._api_calls = count
        return func
    return decorator

# Apply decorator after function definition
sync_trades_process._api_calls = 5 