#!/usr/bin/env python3
"""
Check status of trade 74 and its levels
"""
from db import get_db_connection

def check_trade_74():
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        
        print('=== TRADE 74 STATUS ===')
        cursor.execute("""
            SELECT id, symbol, status, quantity, entry_price, exit_price, 
                   close_reason, closed_at, opened_at
            FROM trades WHERE id = 74
        """)
        trade = cursor.fetchone()
        if trade:
            print(f'Trade ID: {trade[0]}')
            print(f'Symbol: {trade[1]}')
            print(f'Status: {trade[2]}')
            print(f'Quantity: {trade[3]}')
            print(f'Entry Price: ${trade[4]}')
            print(f'Exit Price: ${trade[5]}')
            print(f'Close Reason: {trade[6]}')
            print(f'Closed At: {trade[7]}')
            print(f'Opened At: {trade[8]}')
        else:
            print('Trade 74 not found')
        
        print('\n=== TAKE PROFIT LEVELS FOR TRADE 74 ===')
        cursor.execute("""
            SELECT id, level_number, price, shares_quantity, status, 
                   executed_at, executed_price
            FROM take_profit_levels WHERE trade_id = 74 
            ORDER BY level_number
        """)
        tp_levels = cursor.fetchall()
        for tp in tp_levels:
            print(f'TP Level {tp[1]}: ${tp[2]}, {tp[3]} shares, status: {tp[4]}')
            if tp[5]:
                print(f'  -> Executed at: {tp[5]}, price: ${tp[6]}')
        
        print('\n=== STOP LOSS LEVELS FOR TRADE 74 ===')
        cursor.execute("""
            SELECT id, price, status, executed_at, executed_price, executed_shares
            FROM stop_loss_levels WHERE trade_id = 74
        """)
        sl_levels = cursor.fetchall()
        for sl in sl_levels:
            print(f'SL: ${sl[1]}, status: {sl[2]}')
            if sl[3]:
                print(f'  -> Executed at: {sl[3]}, price: ${sl[4]}, shares: {sl[5]}')
        
        print(f'\nTotal TP levels: {len(tp_levels)}')
        print(f'Total SL levels: {len(sl_levels)}')
        
    finally:
        conn.close()

if __name__ == "__main__":
    check_trade_74() 