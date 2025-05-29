"""
Bridge service that connects Alpaca streaming updates to WebSocket notifications
This runs alongside the main app and pushes real-time updates to connected clients
"""
import asyncio
import os
import json
from datetime import datetime
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv
from alpaca.trading.stream import TradingStream
from alpaca.trading.enums import TradeEvent
import aiohttp

load_dotenv()

# Internal API endpoint for sending notifications
INTERNAL_API_URL = os.getenv("INTERNAL_API_URL", "http://localhost:8000")

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

class StreamBridge:
    def __init__(self):
        self.streams = {}
        self.session = None
        
    async def setup(self):
        """Setup HTTP session for API calls"""
        self.session = aiohttp.ClientSession()
        
    async def cleanup(self):
        """Cleanup resources"""
        if self.session:
            await self.session.close()
    
    async def notify_frontend(self, user_id: int, trade_data: dict):
        """Send notification to frontend via internal API"""
        try:
            # This would typically call an internal endpoint
            # For now, we'll update the database with a flag that the frontend can poll
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Store notification in a notifications table
            cursor.execute("""
                INSERT INTO trade_notifications (user_id, trade_id, notification_type, data, created_at)
                VALUES (%s, %s, %s, %s, %s)
            """, (
                user_id,
                trade_data.get('trade_id'),
                trade_data.get('type', 'trade_update'),
                json.dumps(trade_data),
                datetime.utcnow()
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            print(f"Error sending notification: {e}")
    
    async def handle_trade_update(self, data):
        """Handle real-time trade updates from Alpaca and notify frontend"""
        try:
            order = data.order
            event = data.event
            
            print(f"\n[Stream Bridge] {event}: {order.symbol} {order.side} {order.qty}")
            
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Find the trade and user
            cursor.execute("""
                SELECT t.id, t.user_id, t.symbol, t.action, t.quantity, t.account_id,
                       a.name as account_name
                FROM trades t
                JOIN accounts a ON t.account_id = a.id
                WHERE t.broker_order_id = %s
            """, (str(order.id),))
            
            trade = cursor.fetchone()
            
            if trade:
                trade_id = trade['id']
                user_id = trade['user_id']
                
                # Prepare notification data
                notification_data = {
                    "trade_id": trade_id,
                    "symbol": trade['symbol'],
                    "action": trade['action'],
                    "quantity": float(order.filled_qty) if order.filled_qty else trade['quantity'],
                    "account": trade['account_name'],
                    "event": str(event),
                    "timestamp": datetime.utcnow().isoformat()
                }
                
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
                    
                    notification_data.update({
                        "type": "order_filled",
                        "status": "open",
                        "message": f"Order filled at ${order.filled_avg_price}",
                        "fill_price": float(order.filled_avg_price) if order.filled_avg_price else 0
                    })
                    
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
                    
                    notification_data.update({
                        "type": "order_partial_fill",
                        "status": "open",
                        "message": f"Partially filled: {order.filled_qty}/{order.qty} shares at ${order.filled_avg_price}",
                        "fill_price": float(order.filled_avg_price) if order.filled_avg_price else 0,
                        "filled_quantity": float(order.filled_qty) if order.filled_qty else 0,
                        "total_quantity": float(order.qty) if order.qty else 0
                    })
                    
                elif event == TradeEvent.CANCELED:
                    # Order cancelled
                    cursor.execute("""
                        UPDATE trades 
                        SET status = 'cancelled',
                            close_reason = 'Order cancelled'
                        WHERE id = %s
                    """, (trade_id,))
                    
                    notification_data.update({
                        "type": "order_cancelled",
                        "status": "cancelled",
                        "message": "Order cancelled"
                    })
                    
                elif event == TradeEvent.REJECTED:
                    # Order rejected
                    cursor.execute("""
                        UPDATE trades 
                        SET status = 'cancelled',
                            close_reason = 'Order rejected by broker'
                        WHERE id = %s
                    """, (trade_id,))
                    
                    notification_data.update({
                        "type": "order_rejected",
                        "status": "cancelled",
                        "message": "Order rejected by broker"
                    })
                    
                elif event == TradeEvent.NEW:
                    notification_data.update({
                        "type": "order_accepted",
                        "status": "pending",
                        "message": "Order accepted by broker"
                    })
                    
                elif event == TradeEvent.EXPIRED:
                    cursor.execute("""
                        UPDATE trades 
                        SET status = 'cancelled',
                            close_reason = 'Order expired'
                        WHERE id = %s
                    """, (trade_id,))
                    
                    notification_data.update({
                        "type": "order_expired",
                        "status": "cancelled",
                        "message": "Order expired"
                    })
                
                conn.commit()
                
                # Send notification to frontend
                await self.notify_frontend(user_id, notification_data)
                
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
            
            print(f"Starting bridge stream for account {account_id} ({'paper' if paper else 'live'})...")
            
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
        
        print(f"Starting bridge streams for {len(accounts)} accounts...")
        
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
    print("Alpaca Stream Bridge Service")
    print("=" * 60)
    print("This service bridges Alpaca trade updates to frontend notifications")
    print("=" * 60)
    
    # Create notifications table if it doesn't exist
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS trade_notifications (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL,
            trade_id INTEGER,
            notification_type VARCHAR(50),
            data JSONB,
            read BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()
    
    bridge = StreamBridge()
    await bridge.setup()
    
    try:
        await bridge.start_all_streams()
    except KeyboardInterrupt:
        print("\nShutting down bridge...")
    except Exception as e:
        print(f"Fatal error: {e}")
    finally:
        await bridge.cleanup()

if __name__ == "__main__":
    asyncio.run(main()) 