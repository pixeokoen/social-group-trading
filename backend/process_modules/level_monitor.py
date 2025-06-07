"""
Level Monitor Process Module

Monitors and executes take profit and stop loss levels for active trades.
This is the high-priority, fast-execution process for profit/loss management.
"""

import asyncio
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from decimal import Decimal

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db import get_db_connection
from alpaca_client import AlpacaClient

logger = logging.getLogger(__name__)

async def monitor_levels_process() -> int:
    """
    Monitor and execute take profit/stop loss levels.
    This process runs frequently (every 5 seconds) for fast execution.
    Returns the number of API calls made.
    """
    
    api_calls_made = 0
    conn = None
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get all accounts with active levels
        cursor.execute("""
            SELECT DISTINCT a.id, a.api_key, a.api_secret, a.account_type
            FROM accounts a
            WHERE a.is_active = TRUE 
            AND a.broker = 'alpaca'
            AND (
                EXISTS (
                    SELECT 1 FROM take_profit_levels tp 
                    JOIN trades t ON tp.trade_id = t.id 
                    WHERE t.account_id = a.id AND tp.status = 'pending' AND t.status = 'filled'
                )
                OR EXISTS (
                    SELECT 1 FROM stop_loss_levels sl 
                    JOIN trades t ON sl.trade_id = t.id 
                    WHERE t.account_id = a.id AND sl.status = 'active' AND t.status = 'filled'
                )
            )
        """)
        
        active_accounts = cursor.fetchall()
        
        if not active_accounts:
            return 0  # No active levels to monitor
            
        logger.debug(f"Monitoring levels for {len(active_accounts)} accounts")
        
        for account in active_accounts:
            try:
                account_id, api_key, api_secret, account_type = account
                
                # Get broker client
                client = AlpacaClient(
                    api_key=api_key,
                    secret_key=api_secret,
                    paper=(account_type == 'paper')
                )
                
                # Monitor and execute levels for this account
                calls_made = await process_account_levels(cursor, client, account_id)
                api_calls_made += calls_made
                
            except Exception as e:
                logger.error(f"Error monitoring levels for account {account_id}: {e}")
                continue
        
        conn.commit()
        
        # Track API usage (will be handled by script manager when integrated)
        
        if api_calls_made > 0:
            logger.debug(f"Level monitoring completed - made {api_calls_made} API calls")
        
        return api_calls_made  # Return actual API calls for script manager tracking
        
    except Exception as e:
        logger.error(f"Error in level monitor process: {e}")
        if conn:
            conn.rollback()
    
    finally:
        if conn:
            conn.close()
    
    return api_calls_made if 'api_calls_made' in locals() else 0

async def process_account_levels(cursor, client: AlpacaClient, account_id: int) -> int:
    """Process levels for a specific account and return API calls made"""
    
    api_calls_made = 0
    
    # Get all symbols with active levels for batch price fetching
    cursor.execute("""
        SELECT DISTINCT t.symbol
        FROM trades t
        LEFT JOIN take_profit_levels tp ON t.id = tp.trade_id
        LEFT JOIN stop_loss_levels sl ON t.id = sl.trade_id
        WHERE t.account_id = %s 
        AND t.status IN ('filled', 'closed')
        AND (
            (tp.status = 'pending' AND tp.id IS NOT NULL)
            OR (sl.status = 'active' AND sl.id IS NOT NULL)
        )
    """, (account_id,))
    
    symbols_result = cursor.fetchall()
    symbols = [row[0] for row in symbols_result] if symbols_result else []
    
    if not symbols:
        return 0
    
    try:
        # Batch get current prices for all symbols
        current_prices = await client.get_current_prices(symbols)
        api_calls_made += 1
        
        # Process take profit levels
        tp_api_calls = await process_take_profit_levels(cursor, client, account_id, current_prices)
        api_calls_made += tp_api_calls
        
        # Process stop loss levels  
        sl_api_calls = await process_stop_loss_levels(cursor, client, account_id, current_prices)
        api_calls_made += sl_api_calls
        
        # API calls for any executions will be tracked in the execution functions
        
    except Exception as e:
        logger.error(f"Error processing levels for account {account_id}: {e}")
    
    return api_calls_made

async def process_take_profit_levels(cursor, client: AlpacaClient, account_id: int, current_prices: Dict[str, float]) -> int:
    """Process take profit levels for execution and return API calls made"""
    
    api_calls_made = 0
    
    # Get pending take profit levels
    cursor.execute("""
        SELECT tp.id, tp.trade_id, tp.level_number, tp.price, tp.shares_quantity, 
               t.symbol, t.side, t.quantity as total_quantity
        FROM take_profit_levels tp
        JOIN trades t ON tp.trade_id = t.id
        WHERE t.account_id = %s 
        AND t.status IN ('filled', 'closed')
        AND tp.status = 'pending'
        ORDER BY tp.level_number
    """, (account_id,))
    
    levels = cursor.fetchall()
    
    for level in levels:
        try:
            level_id, trade_id, level_number, target_price, quantity, symbol, side, total_quantity = level
            
            if symbol not in current_prices:
                continue
                
            current_price = current_prices[symbol]
            
            # Check if level should be executed
            should_execute = False
            if side.upper() == 'BUY':
                # Long position - take profit when price goes up
                should_execute = current_price >= target_price
            else:
                # Short position - take profit when price goes down
                should_execute = current_price <= target_price
            
            if should_execute:
                # Execute the level
                success = await execute_take_profit_level(
                    cursor, client, level_id, trade_id, symbol, quantity, current_price, level_number
                )
                
                if success:
                    api_calls_made += 1  # Count the place_order API call
                    logger.info(f"🎯 Take profit executed: {symbol} Level {level_number} at ${current_price}")
                
        except Exception as e:
            logger.error(f"Error processing take profit level {level_id}: {e}")
            continue

    return api_calls_made

async def process_stop_loss_levels(cursor, client: AlpacaClient, account_id: int, current_prices: Dict[str, float]) -> int:
    """Process stop loss levels for execution and return API calls made"""
    
    api_calls_made = 0
    
    # Get active stop loss levels
    cursor.execute("""
        SELECT sl.id, sl.trade_id, sl.price, t.quantity,
               t.symbol, t.action, t.quantity as total_quantity
        FROM stop_loss_levels sl
        JOIN trades t ON sl.trade_id = t.id
        WHERE t.account_id = %s 
        AND t.status IN ('filled', 'closed')
        AND sl.status = 'active'
    """, (account_id,))
    
    levels = cursor.fetchall()
    
    for level in levels:
        try:
            level_id, trade_id, stop_price, quantity, symbol, action, total_quantity = level
            
            if symbol not in current_prices:
                continue
                
            current_price = current_prices[symbol]
            
            # Check if stop loss should be executed
            should_execute = False
            if action.upper() == 'BUY':
                # Long position - stop loss when price goes down
                should_execute = current_price <= stop_price
            else:
                # Short position - stop loss when price goes up
                should_execute = current_price >= stop_price
            
            if should_execute:
                # Execute the stop loss
                success = await execute_stop_loss_level(
                    cursor, client, level_id, trade_id, symbol, quantity, current_price
                )
                
                if success:
                    api_calls_made += 1  # Count the place_order API call
                    logger.info(f"🛑 Stop loss executed: {symbol} at ${current_price} (target: ${stop_price})")
                
        except Exception as e:
            logger.error(f"Error processing stop loss level {level_id}: {e}")
            continue

    return api_calls_made

async def execute_take_profit_level(cursor, client: AlpacaClient, level_id: int, trade_id: int, 
                                  symbol: str, quantity: float, current_price: float, level_number: int) -> bool:
    """Execute a take profit level"""
    
    try:
        # Get trade details
        cursor.execute("""
            SELECT action, account_id, user_id FROM trades WHERE id = %s
        """, (trade_id,))
        
        trade_result = cursor.fetchone()
        if not trade_result:
            return False
            
        action, account_id, user_id = trade_result
        
        # Determine order side (opposite of original trade)
        order_side = 'sell' if action.upper() == 'BUY' else 'buy'
        
        # Place market order
        order_result = await client.place_order(
            symbol=symbol,
            action=order_side,  # Fixed: was 'side', should be 'action'
            quantity=quantity,  # Fixed: was 'qty', should be 'quantity'
            order_type='market',  # Fixed: was 'type', should be 'order_type'
            time_in_force='day'
        )
        
        if order_result and 'id' in order_result:
            # Update level status
            cursor.execute("""
                UPDATE take_profit_levels 
                SET status = 'executed',
                    executed_at = NOW(),
                    executed_price = %s,
                    broker_order_id = %s
                WHERE id = %s
            """, (current_price, order_result['id'], level_id))
            
            # Create notification
            import json
            notification_data = {
                'level_number': level_number,
                'executed_price': float(current_price),
                'quantity': float(quantity),
                'symbol': symbol,
                'broker_order_id': order_result['id']
            }
            cursor.execute("""
                INSERT INTO trade_notifications (user_id, trade_id, notification_type, data, created_at)
                VALUES (%s, %s, 'take_profit_executed', %s, NOW())
            """, (user_id, trade_id, json.dumps(notification_data)))
            
            return True
            
    except Exception as e:
        logger.error(f"Error executing take profit level {level_id}: {e}")
        
    return False

async def execute_stop_loss_level(cursor, client: AlpacaClient, level_id: int, trade_id: int, 
                                symbol: str, quantity: float, current_price: float) -> bool:
    """Execute a stop loss level - sell ALL shares in the position"""
    
    try:
        # Get full trade details including total quantity
        cursor.execute("""
            SELECT action, account_id, quantity, user_id, entry_price FROM trades WHERE id = %s
        """, (trade_id,))
        
        trade_result = cursor.fetchone()
        if not trade_result:
            return False
            
        action, account_id, total_quantity, user_id, entry_price = trade_result
        
        # Determine order side (opposite of original trade)
        order_side = 'sell' if action.upper() == 'BUY' else 'buy'
        
        # Place market order for ALL shares (not just level quantity)
        order_result = await client.place_order(
            symbol=symbol,
            action=order_side,  # Fixed: was 'side', should be 'action'
            quantity=total_quantity,  # Fixed: was 'qty', should be 'quantity'
            order_type='market',  # Fixed: was 'type', should be 'order_type'
            time_in_force='day'
        )
        
        if order_result and 'id' in order_result:
            # Update stop loss level status
            cursor.execute("""
                UPDATE stop_loss_levels 
                SET status = 'executed',
                    executed_at = NOW(),
                    executed_price = %s,
                    broker_order_id = %s
                WHERE id = %s
            """, (current_price, order_result['id'], level_id))
            
            # Create a new SELL trade record linked to the original BUY trade
            import uuid
            link_group_uuid = str(uuid.uuid4())
            
            # First update the original trade with the link_group_id
            cursor.execute("""
                UPDATE trades SET link_group_id = %s WHERE id = %s
            """, (link_group_uuid, trade_id))
            
            # Then create the new linked trade
            cursor.execute("""
                INSERT INTO trades (
                    user_id, account_id, symbol, action, quantity, 
                    entry_price, status, broker_order_id, 
                    opened_at, link_group_id, close_reason
                ) VALUES (
                    %s, %s, %s, %s, %s, 
                    %s, 'filled', %s, 
                    NOW(), %s, 'stop_loss'
                )
                RETURNING id
            """, (
                user_id, account_id, symbol, order_side.upper(), total_quantity,
                current_price, order_result['id'], 
                link_group_uuid  # Same UUID for linking
            ))
            
            new_trade_id = cursor.fetchone()[0]
            
            # Update original trade status
            cursor.execute("""
                UPDATE trades 
                SET status = 'closed',
                    close_reason = 'stop_loss',
                    exit_price = %s,
                    closed_at = NOW()
                WHERE id = %s
            """, (current_price, trade_id))
            
            # Cancel pending take profit levels for this trade
            cursor.execute("""
                UPDATE take_profit_levels 
                SET status = 'cancelled',
                    executed_at = NOW()
                WHERE trade_id = %s AND status = 'pending'
            """, (trade_id,))

            # Create notification
            import json
            notification_data = {
                'executed_price': float(current_price),
                'total_quantity': float(total_quantity),
                'symbol': symbol,
                'broker_order_id': order_result['id'],
                'sell_trade_created': True,
                'sell_trade_id': new_trade_id
            }
            cursor.execute("""
                INSERT INTO trade_notifications (user_id, trade_id, notification_type, data, created_at)
                VALUES (%s, %s, 'stop_loss_executed', %s, NOW())
            """, (user_id, trade_id, json.dumps(notification_data)))
            
            return True
            
    except Exception as e:
        logger.error(f"Error executing stop loss level {level_id}: {e}")
        
    return False

# Mark API calls for the main function
monitor_levels_process._api_calls = 3  # More realistic: 1-2 accounts × 1 API call each + buffer 