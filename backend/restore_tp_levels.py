#!/usr/bin/env python3
"""
Restore take profit levels to active status for filled trades
"""
from db import get_db_connection

def restore_tp_levels():
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        
        print("🔧 Restoring take profit levels to active status...")
        
        # Find all trades that were affected by my wrong cancellations
        cursor.execute("""
            SELECT tp.id, tp.trade_id, tp.level_number, t.symbol, t.status, tp.status
            FROM take_profit_levels tp
            JOIN trades t ON tp.trade_id = t.id
            WHERE tp.status = 'cancelled'
            AND tp.executed_at::date = CURRENT_DATE
            AND t.status = 'closed'  -- These are filled trades that should have active TP levels
            ORDER BY tp.trade_id, tp.level_number
        """)
        
        levels_to_restore = cursor.fetchall()
        
        if not levels_to_restore:
            print("No cancelled TP levels found for today")
            return
            
        print(f"Found {len(levels_to_restore)} TP levels to restore:")
        
        trades_affected = {}
        for level in levels_to_restore:
            level_id, trade_id, level_num, symbol, trade_status, tp_status = level
            if trade_id not in trades_affected:
                trades_affected[trade_id] = {'symbol': symbol, 'status': trade_status, 'levels': []}
            trades_affected[trade_id]['levels'].append((level_id, level_num))
            
        for trade_id, info in trades_affected.items():
            print(f"\nTrade {trade_id} ({info['symbol']}) - {len(info['levels'])} levels")
            
            # Restore all levels to 'pending' status (which should trigger monitoring)
            for level_id, level_num in info['levels']:
                cursor.execute("""
                    UPDATE take_profit_levels 
                    SET status = 'pending',
                        executed_at = NULL
                    WHERE id = %s
                """, (level_id,))
                print(f"  ✅ Restored TP Level {level_num} to pending")
        
        conn.commit()
        print(f"\n🎉 Successfully restored TP levels for {len(trades_affected)} trades")
        
        # Show the current status
        print("\n📊 Current status after restore:")
        for trade_id in trades_affected.keys():
            cursor.execute("""
                SELECT level_number, status FROM take_profit_levels 
                WHERE trade_id = %s ORDER BY level_number
            """, (trade_id,))
            levels = cursor.fetchall()
            print(f"Trade {trade_id}: {[(l[0], l[1]) for l in levels]}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    restore_tp_levels() 