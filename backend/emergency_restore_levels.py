#!/usr/bin/env python3
"""
EMERGENCY: Restore take profit levels that were wrongly cancelled
"""
from db import get_db_connection

def restore_cancelled_levels():
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        
        print("🚨 EMERGENCY RESTORE: Finding wrongly cancelled TP levels...")
        
        # Find recently cancelled TP levels (today)
        cursor.execute("""
            SELECT tp.id, tp.trade_id, tp.level_number, t.symbol, t.status,
                   tp.executed_at
            FROM take_profit_levels tp
            JOIN trades t ON tp.trade_id = t.id
            WHERE tp.status = 'cancelled'
            AND tp.executed_at::date = CURRENT_DATE
            AND t.status IN ('open', 'filled')
            ORDER BY tp.trade_id, tp.level_number
        """)
        
        cancelled_levels = cursor.fetchall()
        
        if not cancelled_levels:
            print("No recently cancelled levels found for open trades")
            return
            
        print(f"Found {len(cancelled_levels)} wrongly cancelled levels:")
        
        trades_affected = {}
        for level in cancelled_levels:
            level_id, trade_id, level_num, symbol, trade_status, cancelled_at = level
            if trade_id not in trades_affected:
                trades_affected[trade_id] = {'symbol': symbol, 'status': trade_status, 'levels': []}
            trades_affected[trade_id]['levels'].append((level_id, level_num, cancelled_at))
            
        for trade_id, info in trades_affected.items():
            print(f"\nTrade {trade_id} ({info['symbol']}) - Status: {info['status']}")
            print(f"  Cancelled levels: {len(info['levels'])}")
            
            # Ask user confirmation for each trade
            if trade_id == 74:
                print(f"  -> Skipping trade 74 (this was the original issue)")
                continue
                
            # Restore the levels
            for level_id, level_num, cancelled_at in info['levels']:
                cursor.execute("""
                    UPDATE take_profit_levels 
                    SET status = 'pending',
                        executed_at = NULL
                    WHERE id = %s
                """, (level_id,))
                print(f"  -> Restored Level {level_num}")
        
        conn.commit()
        print(f"\n✅ Restored TP levels for {len(trades_affected)-1} trades (excluding trade 74)")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    restore_cancelled_levels() 