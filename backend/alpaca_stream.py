"""
Alpaca WebSocket streaming service for real-time trade updates
"""
import asyncio
import os
import json
from datetime import datetime
from decimal import Decimal
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv
from alpaca.trading.stream import TradingStream
from alpaca.trading.enums import TradeEvent

load_dotenv()

def get_db_connection():
    """Create database connection"""
    return psycopg2.connect(
        host=os.getenv('DB_HOST'),
        database=os.getenv('DB_NAME'),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD'),
        port=os.getenv('DB_PORT', 5432),
        cursor_factory=RealDictCursor
    )

class AlpacaStreamHandler:
    def __init__(self):
        self.streams = {}  # Store streams by account_id
        
    async def handle_trade_update(self, data):
        """Handle real-time trade updates from Alpaca"""
        try:
            order = data.order
            event = data.event
            
            print(f"\n[Trade Update] {event}: {order.symbol} {order.side} {order.qty} @ {order.order_type}")
            
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Find the trade by broker_order_id
            cursor.execute("""
                SELECT id, account_id FROM trades 
                WHERE broker_order_id = %s
            """, (str(order.id),))
            
            trade = cursor.fetchone()
            
            if trade:
                trade_id = trade['id']
                
                # Handle different event types
                if event == TradeEvent.FILL:
                    # Order fully filled
                    cursor.execute("""
                        UPDATE trades 
                        SET status = 'open',
                            broker_fill_price = %s,
                            entry_price = %s,
                            opened_at = %s,
                            quantity = %s
                        WHERE id = %s
                    """, (
                        float(order.filled_avg_price) if order.filled_avg_price else 0,
                        float(order.filled_avg_price) if order.filled_avg_price else 0,
                        order.filled_at,
                        float(order.filled_qty) if order.filled_qty else 0,
                        trade_id
                    ))
                    print(f"  ✓ Order FILLED at ${order.filled_avg_price}")
                    
                elif event == TradeEvent.PARTIAL_FILL:
                    # Order partially filled
                    cursor.execute("""
                        UPDATE trades 
                        SET status = 'open',
                            broker_fill_price = %s,
                            entry_price = %s,
                            quantity = %s
                        WHERE id = %s
                    """, (
                        float(order.filled_avg_price) if order.filled_avg_price else 0,
                        float(order.filled_avg_price) if order.filled_avg_price else 0,
                        float(order.filled_qty) if order.filled_qty else 0,
                        trade_id
                    ))
                    print(f"  ⚡ Order PARTIALLY FILLED: {order.filled_qty}/{order.qty} shares")
                    
                elif event == TradeEvent.CANCELED:
                    # Order cancelled
                    cursor.execute("""
                        UPDATE trades 
                        SET status = 'cancelled',
                            close_reason = 'Order cancelled'
                        WHERE id = %s
                    """, (trade_id,))
                    print(f"  ✗ Order CANCELLED")
                    
                elif event == TradeEvent.REJECTED:
                    # Order rejected
                    cursor.execute("""
                        UPDATE trades 
                        SET status = 'cancelled',
                            close_reason = 'Order rejected by broker'
                        WHERE id = %s
                    """, (trade_id,))
                    print(f"  ✗ Order REJECTED")
                    
                elif event == TradeEvent.PENDING_NEW:
                    print(f"  ⏳ Order PENDING")
                    
                elif event == TradeEvent.NEW:
                    print(f"  ✓ Order ACCEPTED by broker")
                    
                elif event == TradeEvent.EXPIRED:
                    cursor.execute("""
                        UPDATE trades 
                        SET status = 'cancelled',
                            close_reason = 'Order expired'
                        WHERE id = %s
                    """, (trade_id,))
                    print(f"  ⏰ Order EXPIRED")
                
                conn.commit()
            else:
                print(f"  ⚠️  Trade not found in database for order {order.id}")
                
            conn.close()
            
        except Exception as e:
            print(f"Error handling trade update: {e}")
            if conn:
                conn.rollback()
                conn.close()
    
    async def start_streaming_for_account(self, account_id, api_key, api_secret, paper=True):
        """Start streaming for a specific account"""
        try:
            # Create trading stream for this account
            stream = TradingStream(
                api_key=api_key,
                secret_key=api_secret,
                paper=paper
            )
            
            # Subscribe to trade updates
            stream.subscribe_trade_updates(self.handle_trade_update)
            
            # Store stream reference
            self.streams[account_id] = stream
            
            print(f"Starting stream for account {account_id} ({'paper' if paper else 'live'})...")
            
            # Run the stream
            await stream._run_forever()
            
        except Exception as e:
            print(f"Error in stream for account {account_id}: {e}")
            # Try to reconnect after a delay
            await asyncio.sleep(5)
            await self.start_streaming_for_account(account_id, api_key, api_secret, paper)
    
    async def start_all_streams(self):
        """Start streaming for all active accounts"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get all active Alpaca accounts
        cursor.execute("""
            SELECT id, name, account_type, api_key, api_secret 
            FROM accounts 
            WHERE is_active = TRUE 
            AND broker = 'alpaca'
            AND api_key IS NOT NULL 
            AND api_secret IS NOT NULL
        """)
        
        accounts = cursor.fetchall()
        conn.close()
        
        if not accounts:
            print("No active Alpaca accounts found")
            return
        
        print(f"Starting WebSocket streams for {len(accounts)} accounts...")
        
        # Create tasks for each account stream
        tasks = []
        for account in accounts:
            task = asyncio.create_task(
                self.start_streaming_for_account(
                    account['id'],
                    account['api_key'],
                    account['api_secret'],
                    paper=(account['account_type'] == 'paper')
                )
            )
            tasks.append(task)
        
        # Run all streams concurrently
        await asyncio.gather(*tasks)

async def main():
    """Main entry point"""
    print("=" * 60)
    print("Alpaca Real-Time Trade Streaming Service")
    print("=" * 60)
    print("This service provides real-time updates for:")
    print("- Order fills (partial and complete)")
    print("- Order cancellations")
    print("- Order rejections")
    print("- Order status changes")
    print("=" * 60)
    
    handler = AlpacaStreamHandler()
    
    try:
        await handler.start_all_streams()
    except KeyboardInterrupt:
        print("\nShutting down streams...")
    except Exception as e:
        print(f"Fatal error: {e}")

if __name__ == "__main__":
    asyncio.run(main()) 