#!/usr/bin/env python3
"""
Fix orphaned take profit levels for trade 74
Since the trade is closed, all pending TP levels should be cancelled
"""
from db import get_db_connection
from datetime import datetime

def fix_trade_74_levels():
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        
        # Check current status
        cursor.execute("SELECT status, close_reason FROM trades WHERE id = 74")
        trade_result = cursor.fetchone()
        
        if not trade_result:
            print("❌ Trade 74 not found")
            return
            
        trade_status, close_reason = trade_result
        print(f"Trade 74 status: {trade_status}, close_reason: {close_reason}")
        
        # Check pending take profit levels
        cursor.execute("""
            SELECT COUNT(*) FROM take_profit_levels 
            WHERE trade_id = 74 AND status = 'pending'
        """)
        pending_count = cursor.fetchone()[0]
        
        print(f"Found {pending_count} pending take profit levels")
        
        if trade_status == 'closed' and pending_count > 0:
            print("🔧 Fixing orphaned take profit levels...")
            
            # Cancel all pending take profit levels
            cursor.execute("""
                UPDATE take_profit_levels 
                SET status = 'cancelled',
                    executed_at = %s
                WHERE trade_id = 74 AND status = 'pending'
            """, (datetime.utcnow(),))
            
            updated_count = cursor.rowcount
            conn.commit()
            
            print(f"✅ Successfully cancelled {updated_count} take profit levels for trade 74")
            
            # Verify the fix
            cursor.execute("""
                SELECT level_number, status FROM take_profit_levels 
                WHERE trade_id = 74 ORDER BY level_number
            """)
            levels = cursor.fetchall()
            
            print("Updated levels:")
            for level in levels:
                print(f"  - Level {level[0]}: {level[1]}")
                
        else:
            print("No action needed - trade is not closed or no pending levels found")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    fix_trade_74_levels() 