#!/usr/bin/env python3
"""
Test if level monitoring is working for trade 74
"""
from db import get_db_connection

def test_monitoring():
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        
        print("🔍 Testing level monitoring for trade 74...")
        
        # Check if the monitor query would find trade 74's TP levels
        cursor.execute("""
            SELECT tp.id, tp.trade_id, tp.level_number, tp.price, tp.shares_quantity, 
                   t.symbol, t.status as trade_status, tp.status as tp_status
            FROM take_profit_levels tp
            JOIN trades t ON tp.trade_id = t.id
            JOIN accounts a ON t.account_id = a.id
            WHERE t.id = 74
            AND t.status IN ('filled', 'closed')
            AND tp.status = 'pending'
            AND a.is_active = TRUE
            ORDER BY tp.level_number
        """)
        
        levels = cursor.fetchall()
        
        if levels:
            print(f"✅ Level monitor WILL find {len(levels)} TP levels for trade 74:")
            for level in levels:
                level_id, trade_id, level_num, price, quantity, symbol, trade_status, tp_status = level
                print(f"  - Level {level_num}: ${price} ({quantity} shares) - {tp_status}")
            
            print(f"\nTrade status: {levels[0][6]}")
            print("✅ The level monitor should now be processing these levels!")
            
        else:
            print("❌ Level monitor will NOT find any levels for trade 74")
            
            # Debug why not
            cursor.execute("""
                SELECT t.status, tp.status, a.is_active
                FROM take_profit_levels tp
                JOIN trades t ON tp.trade_id = t.id
                JOIN accounts a ON t.account_id = a.id
                WHERE t.id = 74
                LIMIT 1
            """)
            debug = cursor.fetchone()
            if debug:
                print(f"Debug - Trade status: {debug[0]}, TP status: {debug[1]}, Account active: {debug[2]}")
        
        # Check current EYEN price to see if any levels should be triggered
        print(f"\n📊 Current TP levels vs price check:")
        print("To test execution, you would need to check current EYEN price against:")
        for level in levels:
            print(f"  - Level {level[2]}: ${level[3]} (should execute if EYEN >= ${level[3]})")
        
    finally:
        conn.close()

if __name__ == "__main__":
    test_monitoring() 