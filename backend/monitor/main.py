#!/usr/bin/env python3
"""
Live Trade Monitoring Service

This is a standalone service that monitors active take profit and stop loss levels
and executes them when price targets are hit. It runs separately from the main
FastAPI application for better reliability and faster execution.

Usage:
    python main.py

Environment Variables:
    DATABASE_URL - PostgreSQL connection string
    MONITOR_INTERVAL - Seconds between price checks (default: 1)
    LOG_LEVEL - Logging level (default: INFO)
"""

import os
import sys
import asyncio
import logging
import time
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
import json

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db import get_db_connection
from alpaca_client import AlpacaClient

# Configure logging
logging.basicConfig(
    level=getattr(logging, os.getenv('LOG_LEVEL', 'INFO')),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class TradeLevelMonitor:
    """Monitors take profit and stop loss levels and executes them when triggered"""
    
    def __init__(self, check_interval: float = 1.0):
        self.check_interval = check_interval
        self.active_symbols = set()
        self.price_cache = {}
        self.last_price_update = {}
        self.broker_clients = {}  # Cache of broker clients
        logger.info(f"TradeLevelMonitor initialized with {check_interval}s interval")
    
    def get_broker_client(self, account_data: Tuple) -> Optional[AlpacaClient]:
        """Get or create broker client for account"""
        account_id, api_key, api_secret, account_type = account_data
        
        if account_id not in self.broker_clients:
            try:
                client = AlpacaClient(
                    api_key=api_key,
                    secret_key=api_secret,
                    paper=(account_type == 'paper')
                )
                self.broker_clients[account_id] = client
                logger.info(f"Created broker client for account {account_id}")
            except Exception as e:
                logger.error(f"Failed to create broker client for account {account_id}: {e}")
                return None
        
        return self.broker_clients.get(account_id)
    
    async def get_active_levels(self) -> List[Dict]:
        """Get all active take profit and stop loss levels from database"""
        conn = get_db_connection()
        try:
            cursor = conn.cursor()
            
            # Get all pending take profit levels with trade and account info
            cursor.execute("""
                SELECT 
                    tp.id, tp.trade_id, tp.level_number, tp.price, tp.percentage,
                    tp.shares_quantity, tp.status, t.symbol, t.action, t.user_id,
                    a.id as account_id, a.api_key, a.api_secret, a.account_type
                FROM take_profit_levels tp
                JOIN trades t ON tp.trade_id = t.id
                JOIN accounts a ON t.account_id = a.id
                WHERE tp.status = 'pending'
                AND t.status = 'open'
                AND a.is_active = TRUE
                ORDER BY t.symbol, tp.level_number
            """)
            
            tp_levels = cursor.fetchall()
            
            # Get all active stop loss levels
            cursor.execute("""
                SELECT 
                    sl.id, sl.trade_id, sl.price, sl.status, t.symbol, t.action, 
                    t.user_id, t.quantity as total_shares,
                    a.id as account_id, a.api_key, a.api_secret, a.account_type
                FROM stop_loss_levels sl
                JOIN trades t ON sl.trade_id = t.id
                JOIN accounts a ON t.account_id = a.id
                WHERE sl.status = 'active'
                AND t.status = 'open'
                AND a.is_active = TRUE
            """)
            
            sl_levels = cursor.fetchall()
            
            # Convert to list of dicts for easier handling
            levels = []
            
            # Process take profit levels
            for tp in tp_levels:
                levels.append({
                    'type': 'take_profit',
                    'id': tp[0],
                    'trade_id': tp[1],
                    'level_number': tp[2] if len(tp) > 2 else None,
                    'price': float(tp[3]),
                    'shares': float(tp[5]),
                    'symbol': tp[7],
                    'action': tp[8],
                    'user_id': tp[9],
                    'account_data': (tp[10], tp[11], tp[12], tp[13])
                })
            
            # Process stop loss levels
            for sl in sl_levels:
                # Calculate remaining shares (total - executed take profits)
                cursor.execute("""
                    SELECT COALESCE(SUM(shares_quantity), 0) 
                    FROM take_profit_levels 
                    WHERE trade_id = %s AND status = 'executed'
                """, (sl[1],))
                executed_tp_shares = cursor.fetchone()[0] or 0
                remaining_shares = float(sl[7]) - float(executed_tp_shares)
                
                if remaining_shares > 0:
                    levels.append({
                        'type': 'stop_loss',
                        'id': sl[0],
                        'trade_id': sl[1],
                        'price': float(sl[2]),
                        'shares': remaining_shares,
                        'symbol': sl[4],
                        'action': sl[5],
                        'user_id': sl[6],
                        'account_data': (sl[8], sl[9], sl[10], sl[11])
                    })
            
            logger.info(f"Found {len(levels)} active levels to monitor")
            return levels
            
        except Exception as e:
            logger.error(f"Error getting active levels: {e}")
            return []
        finally:
            conn.close()
    
    async def get_current_price(self, symbol: str, client: AlpacaClient) -> Optional[float]:
        """Get current price for symbol"""
        try:
            # Use cached price if recent (within 5 seconds)
            now = time.time()
            if (symbol in self.price_cache and 
                symbol in self.last_price_update and 
                now - self.last_price_update[symbol] < 5):
                return self.price_cache[symbol]
            
            # Get latest price from broker
            price_data = await client.get_latest_price(symbol)
            if price_data and 'price' in price_data:
                price = float(price_data['price'])
                self.price_cache[symbol] = price
                self.last_price_update[symbol] = now
                return price
            
        except Exception as e:
            logger.error(f"Error getting price for {symbol}: {e}")
        
        return None
    
    def should_execute_level(self, level: Dict, current_price: float) -> bool:
        """Check if a level should be executed based on current price"""
        target_price = level['price']
        level_type = level['type']
        action = level['action']
        
        if level_type == 'take_profit':
            # Take profit: sell when price reaches or exceeds target (for long positions)
            # For short positions, buy when price drops to or below target
            if action.upper() == 'BUY':  # Long position
                return current_price >= target_price
            else:  # Short position
                return current_price <= target_price
        
        elif level_type == 'stop_loss':
            # Stop loss: sell when price drops to or below target (for long positions)
            # For short positions, buy when price rises to or above target
            if action.upper() == 'BUY':  # Long position
                return current_price <= target_price
            else:  # Short position
                return current_price >= target_price
        
        return False
    
    async def execute_level(self, level: Dict, current_price: float) -> bool:
        """Execute a take profit or stop loss level"""
        try:
            symbol = level['symbol']
            shares = level['shares']
            level_type = level['type']
            level_id = level['id']
            trade_id = level['trade_id']
            original_action = level['action']
            
            # Get broker client
            client = self.get_broker_client(level['account_data'])
            if not client:
                logger.error(f"No broker client available for level {level_id}")
                return False
            
            # Determine execution action (opposite of original trade)
            execution_action = 'SELL' if original_action.upper() == 'BUY' else 'BUY'
            
            logger.info(f"🎯 Executing {level_type} level {level_id}: {execution_action} {shares} {symbol} at ${current_price}")
            
            # Place market order for immediate execution
            order_result = await client.place_order(
                symbol=symbol,
                qty=shares,
                side=execution_action.lower(),
                type='market',
                time_in_force='day'
            )
            
            if order_result and 'id' in order_result:
                broker_order_id = order_result['id']
                
                # Update database with execution
                await self.mark_level_executed(
                    level_type, level_id, current_price, shares, broker_order_id
                )
                
                # Log successful execution
                logger.info(f"✅ {level_type.title()} executed: {symbol} {shares} shares at ${current_price} (Order: {broker_order_id})")
                
                # TODO: Send notification to user
                return True
            else:
                logger.error(f"❌ Failed to execute {level_type} level {level_id}: Invalid order result")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error executing {level_type} level {level_id}: {e}")
            return False
    
    async def mark_level_executed(self, level_type: str, level_id: int, price: float, shares: float, broker_order_id: str):
        """Mark a level as executed in the database"""
        conn = get_db_connection()
        try:
            cursor = conn.cursor()
            
            if level_type == 'take_profit':
                cursor.execute("""
                    UPDATE take_profit_levels 
                    SET status = 'executed',
                        executed_at = %s,
                        executed_price = %s,
                        broker_order_id = %s
                    WHERE id = %s
                """, (datetime.utcnow(), price, broker_order_id, level_id))
            
            elif level_type == 'stop_loss':
                cursor.execute("""
                    UPDATE stop_loss_levels 
                    SET status = 'executed',
                        executed_at = %s,
                        executed_price = %s,
                        executed_shares = %s,
                        broker_order_id = %s
                    WHERE id = %s
                """, (datetime.utcnow(), price, shares, broker_order_id, level_id))
            
            conn.commit()
            logger.info(f"✅ Database updated: {level_type} level {level_id} marked as executed")
            
        except Exception as e:
            logger.error(f"Error updating database for executed level {level_id}: {e}")
            conn.rollback()
        finally:
            conn.close()
    
    async def run_monitoring_cycle(self):
        """Run one monitoring cycle"""
        try:
            # Get all active levels
            levels = await self.get_active_levels()
            
            if not levels:
                logger.debug("No active levels to monitor")
                return
            
            # Group levels by account to reuse broker clients
            levels_by_account = {}
            for level in levels:
                account_id = level['account_data'][0]
                if account_id not in levels_by_account:
                    levels_by_account[account_id] = []
                levels_by_account[account_id].append(level)
            
            # Monitor each account's levels
            for account_id, account_levels in levels_by_account.items():
                try:
                    # Get broker client for this account
                    first_level = account_levels[0]
                    client = self.get_broker_client(first_level['account_data'])
                    if not client:
                        continue
                    
                    # Group by symbol to minimize API calls
                    symbols = set(level['symbol'] for level in account_levels)
                    
                    for symbol in symbols:
                        # Get current price
                        current_price = await self.get_current_price(symbol, client)
                        if current_price is None:
                            continue
                        
                        # Check levels for this symbol
                        symbol_levels = [l for l in account_levels if l['symbol'] == symbol]
                        
                        for level in symbol_levels:
                            if self.should_execute_level(level, current_price):
                                await self.execute_level(level, current_price)
                
                except Exception as e:
                    logger.error(f"Error monitoring account {account_id}: {e}")
                    continue
        
        except Exception as e:
            logger.error(f"Error in monitoring cycle: {e}")
    
    async def start(self):
        """Start the monitoring service"""
        logger.info("🚀 Starting Live Trade Monitoring Service")
        logger.info(f"📊 Monitoring interval: {self.check_interval} seconds")
        
        while True:
            cycle_start = time.time()
            
            try:
                await self.run_monitoring_cycle()
            except Exception as e:
                logger.error(f"Unexpected error in monitoring cycle: {e}")
            
            # Calculate sleep time to maintain consistent interval
            cycle_duration = time.time() - cycle_start
            sleep_time = max(0, self.check_interval - cycle_duration)
            
            if cycle_duration > self.check_interval:
                logger.warning(f"Monitoring cycle took {cycle_duration:.2f}s (longer than {self.check_interval}s interval)")
            
            await asyncio.sleep(sleep_time)

async def main():
    """Main entry point"""
    # Get configuration from environment
    check_interval = float(os.getenv('MONITOR_INTERVAL', '1.0'))
    
    # Create and start monitor
    monitor = TradeLevelMonitor(check_interval=check_interval)
    
    try:
        await monitor.start()
    except KeyboardInterrupt:
        logger.info("🛑 Monitoring service stopped by user")
    except Exception as e:
        logger.error(f"🚨 Fatal error in monitoring service: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main()) 