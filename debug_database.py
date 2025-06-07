#!/usr/bin/env python3
"""
Debug script to check what take profit levels and trades exist in the database
"""
import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from backend.db import get_db_connection

def debug_database():
    """Check the current state of trades and take profit levels"""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        
        print("=" * 60)
        print("DEBUGGING DATABASE CONTENT")
        print("=" * 60)
        
        # Check if tables exist
        cursor.execute("""
            SELECT table_name FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name IN ('trades', 'take_profit_levels', 'stop_loss_levels')
            ORDER BY table_name
        """)
        tables = cursor.fetchall()
        print(f"\n📋 Available tables: {[t[0] for t in tables]}")
        
        # Check trades
        cursor.execute("SELECT COUNT(*) FROM trades")
        trade_count = cursor.fetchone()[0]
        print(f"\n📊 Total trades in database: {trade_count}")
        
        if trade_count > 0:
            cursor.execute("""
                SELECT id, symbol, action, quantity, status, entry_price, stop_loss, created_at
                FROM trades 
                ORDER BY created_at DESC 
                LIMIT 10
            """)
            trades = cursor.fetchall()
            print("\n📈 Recent trades:")
            for trade in trades:
                print(f"  - Trade {trade[0]}: {trade[1]} {trade[2]} {trade[3]} shares, status: {trade[4]}, entry: ${trade[5] or 'N/A'}, stop_loss: ${trade[6] or 'N/A'}")
        
        # Check take profit levels
        cursor.execute("SELECT COUNT(*) FROM take_profit_levels")
        tp_count = cursor.fetchone()[0]
        print(f"\n🎯 Total take profit levels in database: {tp_count}")
        
        if tp_count > 0:
            cursor.execute("""
                SELECT tp.id, tp.trade_id, tp.level_number, tp.price, tp.percentage, 
                       tp.shares_quantity, tp.status, t.symbol
                FROM take_profit_levels tp
                JOIN trades t ON tp.trade_id = t.id
                ORDER BY tp.trade_id, tp.level_number
            """)
            tp_levels = cursor.fetchall()
            print("\n🎯 Take profit levels:")
            for tp in tp_levels:
                print(f"  - TP {tp[0]} (Trade {tp[1]} - {tp[7]}): Level {tp[2]}, ${tp[3]}, {tp[4]}%, {tp[5]} shares, status: {tp[6]}")
        
        # Check stop loss levels
        cursor.execute("SELECT COUNT(*) FROM stop_loss_levels")
        sl_count = cursor.fetchone()[0]
        print(f"\n🛑 Total stop loss levels in database: {sl_count}")
        
        if sl_count > 0:
            cursor.execute("""
                SELECT sl.id, sl.trade_id, sl.price, sl.status, t.symbol
                FROM stop_loss_levels sl
                JOIN trades t ON sl.trade_id = t.id
                ORDER BY sl.trade_id
            """)
            sl_levels = cursor.fetchall()
            print("\n🛑 Stop loss levels:")
            for sl in sl_levels:
                print(f"  - SL {sl[0]} (Trade {sl[1]} - {sl[4]}): ${sl[2]}, status: {sl[3]}")
        
        # Check for trades that should have levels but don't
        cursor.execute("""
            SELECT t.id, t.symbol, t.status, 
                   (SELECT COUNT(*) FROM take_profit_levels WHERE trade_id = t.id) as tp_count,
                   (SELECT COUNT(*) FROM stop_loss_levels WHERE trade_id = t.id) as sl_count
            FROM trades t
            WHERE t.status IN ('open', 'filled')
            ORDER BY t.id DESC
            LIMIT 5
        """)
        open_trades = cursor.fetchall()
        print(f"\n🔍 Open/filled trades and their levels:")
        for trade in open_trades:
            print(f"  - Trade {trade[0]} ({trade[1]}, {trade[2]}): {trade[3]} TP levels, {trade[4]} SL levels")
            if trade[3] == 0 and trade[4] == 0:
                print(f"    ⚠️  This trade has no take profit or stop loss levels!")
        
        print("\n" + "=" * 60)
        
    except Exception as e:
        print(f"❌ Error checking database: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    debug_database() 