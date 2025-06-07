#!/usr/bin/env python3
"""
Fix all orphaned take profit levels
Find all closed trades that still have pending TP levels and cancel them
"""
from db import get_db_connection
from datetime import datetime

def fix_all_orphaned_levels():
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        
        print("🔍 Searching for orphaned take profit levels...")
        
        # Find all closed trades with pending take profit levels
        cursor.execute("""
            SELECT DISTINCT t.id, t.symbol, t.status, t.close_reason,
                   COUNT(tp.id) as pending_tp_count
            FROM trades t
            JOIN take_profit_levels tp ON t.id = tp.trade_id
            WHERE t.status = 'closed' 
            AND tp.status = 'pending'
            GROUP BY t.id, t.symbol, t.status, t.close_reason
            ORDER BY t.id
        """)
        
        orphaned_trades = cursor.fetchall()
        
        if not orphaned_trades:
            print("✅ No orphaned take profit levels found!")
            return
        
        print(f"Found {len(orphaned_trades)} trades with orphaned levels:")
        
        total_fixed = 0
        
        for trade in orphaned_trades:
            trade_id, symbol, status, close_reason, pending_count = trade
            print(f"\n📊 Trade {trade_id} ({symbol}): {pending_count} pending TP levels")
            
            # Cancel the orphaned levels
            cursor.execute("""
                UPDATE take_profit_levels 
                SET status = 'cancelled',
                    executed_at = %s
                WHERE trade_id = %s AND status = 'pending'
            """, (datetime.utcnow(), trade_id))
            
            updated_count = cursor.rowcount
            total_fixed += updated_count
            
            print(f"   ✅ Cancelled {updated_count} levels")
        
        conn.commit()
        print(f"\n🎉 Successfully fixed {total_fixed} orphaned take profit levels across {len(orphaned_trades)} trades!")
        
        # Show summary of all cancelled levels
        cursor.execute("""
            SELECT t.id, t.symbol, COUNT(tp.id) as cancelled_count
            FROM trades t
            JOIN take_profit_levels tp ON t.id = tp.trade_id
            WHERE t.status = 'closed' 
            AND tp.status = 'cancelled'
            GROUP BY t.id, t.symbol
            ORDER BY t.id
        """)
        
        cancelled_summary = cursor.fetchall()
        
        print("\n📋 Summary of cancelled levels:")
        for trade in cancelled_summary:
            print(f"  - Trade {trade[0]} ({trade[1]}): {trade[2]} cancelled levels")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    fix_all_orphaned_levels() 