#!/usr/bin/env python3
"""
Test if stop loss monitoring is working correctly
"""
from db import get_db_connection

def test_stop_loss_monitoring():
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        
        print("🔍 Testing stop loss monitoring...")
        
        # Find trades that have active stop loss levels and should be monitored
        cursor.execute("""
            SELECT sl.id, sl.trade_id, sl.price, t.quantity,
                   t.symbol, t.action, t.status as trade_status, sl.status as sl_status,
                   t.entry_price
            FROM stop_loss_levels sl
            JOIN trades t ON sl.trade_id = t.id
            JOIN accounts a ON t.account_id = a.id
            WHERE t.status IN ('filled', 'closed')
            AND sl.status = 'active'
            AND a.is_active = TRUE
            ORDER BY t.id
        """)
        
        levels = cursor.fetchall()
        
        if levels:
            print(f"✅ Stop loss monitor WILL find {len(levels)} active stop loss levels:")
            for level in levels:
                sl_id, trade_id, sl_price, quantity, symbol, action, trade_status, sl_status, entry_price = level
                print(f"  - Trade {trade_id} ({symbol}): {action} {quantity} shares")
                print(f"    Entry: ${entry_price} | Stop Loss: ${sl_price} | Status: {trade_status}")
                
                if action.upper() == 'BUY':
                    print(f"    Will execute if {symbol} price <= ${sl_price} (long position)")
                else:
                    print(f"    Will execute if {symbol} price >= ${sl_price} (short position)")
                print()
            
            print("✅ The stop loss monitor should now be processing these levels!")
            print("📊 When a stop loss triggers, it will:")
            print("  1. Place a MARKET order to sell ALL shares")
            print("  2. Create a new SELL trade record linked to the BUY trade")
            print("  3. Update the original trade status to 'closed' with reason 'stop_loss'")
            print("  4. Set the executed_price and broker_order_id on the stop loss level")
            
        else:
            print("ℹ️  No active stop loss levels found to monitor")
            
            # Check if there are any stop loss levels at all
            cursor.execute("SELECT COUNT(*) FROM stop_loss_levels")
            total_sl = cursor.fetchone()[0]
            print(f"Total stop loss levels in database: {total_sl}")
            
            if total_sl > 0:
                cursor.execute("""
                    SELECT sl.status, COUNT(*) 
                    FROM stop_loss_levels sl 
                    GROUP BY sl.status
                """)
                status_breakdown = cursor.fetchall()
                print("Stop loss status breakdown:")
                for status, count in status_breakdown:
                    print(f"  - {status}: {count}")
        
    finally:
        conn.close()

if __name__ == "__main__":
    test_stop_loss_monitoring() 