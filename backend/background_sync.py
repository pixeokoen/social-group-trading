"""
Background sync service for keeping trades synchronized with Alpaca
Run this as a separate process for continuous synchronization
"""
import asyncio
import os
import time
from datetime import datetime
from decimal import Decimal
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv
from alpaca_client import AlpacaClient

load_dotenv()

# Sync interval in seconds (default: 30 seconds)
SYNC_INTERVAL = int(os.getenv('SYNC_INTERVAL', 30))

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

async def sync_account_trades(account_id: int, api_key: str, api_secret: str, account_type: str):
    """Sync trades for a specific account"""
    print(f"Syncing account {account_id} ({account_type})...")
    
    # Initialize Alpaca client for this account
    client = AlpacaClient(
        api_key=api_key,
        secret_key=api_secret,
        paper=(account_type == 'paper')
    )
    
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        
        # Get all pending trades for this account
        cursor.execute("""
            SELECT id, broker_order_id, symbol, quantity, action
            FROM trades 
            WHERE account_id = %s 
            AND status IN ('pending', 'open')
            AND broker_order_id IS NOT NULL
        """, (account_id,))
        
        pending_trades = cursor.fetchall()
        updated_count = 0
        
        for trade in pending_trades:
            try:
                # Get order status from Alpaca
                order_status = await client.get_order_status(trade['broker_order_id'])
                
                if order_status:
                    alpaca_status = order_status['status']
                    
                    # Map Alpaca status to our status
                    if alpaca_status == 'filled':
                        # Update trade with fill information
                        cursor.execute("""
                            UPDATE trades 
                            SET status = 'open',
                                broker_fill_price = %s,
                                entry_price = %s,
                                opened_at = %s
                            WHERE id = %s
                        """, (
                            order_status.get('filled_avg_price', 0),
                            order_status.get('filled_avg_price', 0),
                            order_status.get('filled_at'),
                            trade['id']
                        ))
                        updated_count += 1
                        print(f"  - Trade {trade['symbol']} {trade['action']} filled at ${order_status.get('filled_avg_price', 0)}")
                        
                    elif alpaca_status == 'partially_filled':
                        # Update with partial fill info
                        filled_qty = order_status.get('filled_qty', 0)
                        cursor.execute("""
                            UPDATE trades 
                            SET status = 'open',
                                broker_fill_price = %s,
                                entry_price = %s,
                                quantity = %s,
                                opened_at = %s
                            WHERE id = %s
                        """, (
                            order_status.get('filled_avg_price', 0),
                            order_status.get('filled_avg_price', 0),
                            filled_qty,
                            order_status.get('filled_at'),
                            trade['id']
                        ))
                        updated_count += 1
                        print(f"  - Trade {trade['symbol']} {trade['action']} partially filled: {filled_qty} shares")
                        
                    elif alpaca_status in ['canceled', 'expired', 'rejected']:
                        # Mark trade as cancelled
                        cursor.execute("""
                            UPDATE trades 
                            SET status = 'cancelled',
                                close_reason = %s
                            WHERE id = %s
                        """, (f"Order {alpaca_status}", trade['id']))
                        updated_count += 1
                        print(f"  - Trade {trade['symbol']} {trade['action']} {alpaca_status}")
                        
            except Exception as e:
                print(f"  - Error syncing trade {trade['id']}: {e}")
        
        # Also sync current positions from Alpaca
        try:
            positions = await client.get_positions()
            
            # Update current prices for open trades
            for position in positions:
                cursor.execute("""
                    UPDATE trades 
                    SET current_price = %s,
                        floating_pnl = CASE 
                            WHEN action = 'BUY' THEN ((%s - entry_price) * quantity)
                            ELSE ((entry_price - %s) * quantity)
                        END
                    WHERE symbol = %s 
                    AND account_id = %s 
                    AND status = 'open'
                """, (
                    position['current_price'],
                    position['current_price'],
                    position['current_price'],
                    position['symbol'],
                    account_id
                ))
            
            print(f"  - Updated {len(positions)} position prices")
            
        except Exception as e:
            print(f"  - Error updating position prices: {e}")
        
        conn.commit()
        print(f"  - Completed: {updated_count} trades updated")
        
    except Exception as e:
        conn.rollback()
        print(f"Error syncing account {account_id}: {e}")
    finally:
        conn.close()

async def main():
    """Main sync loop"""
    print("Starting background trade sync service...")
    print(f"Sync interval: {SYNC_INTERVAL} seconds")
    
    while True:
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Get all active accounts
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
            
            print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Starting sync cycle for {len(accounts)} accounts...")
            
            # Sync each account
            for account in accounts:
                await sync_account_trades(
                    account['id'],
                    account['api_key'],
                    account['api_secret'],
                    account['account_type']
                )
            
            print("Sync cycle completed. Waiting for next cycle...")
            
        except Exception as e:
            print(f"Error in main sync loop: {e}")
        
        # Wait for next sync cycle
        await asyncio.sleep(SYNC_INTERVAL)

if __name__ == "__main__":
    asyncio.run(main()) 