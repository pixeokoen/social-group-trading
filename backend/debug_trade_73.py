#!/usr/bin/env python3
"""
Debug why trade 73 (WBUY) stop loss isn't executing
"""
import asyncio
from db import get_db_connection
from alpaca_client import AlpacaClient
import os

async def debug_trade_73():
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        
        print("🔍 DEBUGGING TRADE 73 (WBUY) STOP LOSS EXECUTION")
        print("=" * 60)
        
        # 1. Check trade 73 details
        cursor.execute("""
            SELECT id, symbol, action, quantity, entry_price, status, account_id, user_id
            FROM trades WHERE id = 73
        """)
        trade = cursor.fetchone()
        
        if not trade:
            print("❌ Trade 73 not found!")
            return
            
        trade_id, symbol, action, quantity, entry_price, status, account_id, user_id = trade
        print(f"📊 TRADE 73 DETAILS:")
        print(f"   Symbol: {symbol}")
        print(f"   Action: {action}")
        print(f"   Quantity: {quantity}")
        print(f"   Entry Price: ${entry_price}")
        print(f"   Status: {status}")
        print(f"   Account ID: {account_id}")
        print()
        
        # 2. Check stop loss level
        cursor.execute("""
            SELECT id, price, status, executed_at, executed_price 
            FROM stop_loss_levels 
            WHERE trade_id = 73
        """)
        sl_level = cursor.fetchone()
        
        if not sl_level:
            print("❌ NO STOP LOSS LEVEL FOUND for trade 73!")
            return
            
        sl_id, sl_price, sl_status, executed_at, executed_price = sl_level
        print(f"🛑 STOP LOSS LEVEL:")
        print(f"   Stop Price: ${sl_price}")
        print(f"   Status: {sl_status}")
        print(f"   Executed At: {executed_at}")
        print(f"   Executed Price: {executed_price}")
        print()
        
        # 3. Check if account is active
        cursor.execute("""
            SELECT is_active, name FROM accounts WHERE id = %s
        """, (account_id,))
        account_result = cursor.fetchone()
        
        if account_result:
            is_active, account_name = account_result
            print(f"💼 ACCOUNT STATUS:")
            print(f"   Account: {account_name}")
            print(f"   Active: {is_active}")
        else:
            print("❌ Account not found!")
            return
        print()
        
        # 4. Test the level monitor query
        cursor.execute("""
            SELECT sl.id, sl.trade_id, sl.price, t.quantity,
                   t.symbol, t.action, t.quantity as total_quantity
            FROM stop_loss_levels sl
            JOIN trades t ON sl.trade_id = t.id
            WHERE t.account_id = %s 
            AND t.status IN ('filled', 'closed')
            AND sl.status = 'active'
            AND t.id = 73
        """, (account_id,))
        
        monitor_result = cursor.fetchone()
        
        print(f"🔍 LEVEL MONITOR QUERY RESULT:")
        if monitor_result:
            print(f"   ✅ Trade 73 FOUND by level monitor")
            print(f"   Stop Loss ID: {monitor_result[0]}")
            print(f"   Stop Price: ${monitor_result[2]}")
        else:
            print(f"   ❌ Trade 73 NOT FOUND by level monitor!")
            print(f"   Checking why...")
            
            # Debug why not found
            cursor.execute("SELECT status FROM trades WHERE id = 73")
            trade_status = cursor.fetchone()[0]
            print(f"   - Trade status: {trade_status} (needs to be 'filled' or 'closed')")
            
            cursor.execute("SELECT status FROM stop_loss_levels WHERE trade_id = 73")
            sl_status_check = cursor.fetchone()[0]
            print(f"   - Stop loss status: {sl_status_check} (needs to be 'active')")
            
            cursor.execute("SELECT is_active FROM accounts WHERE id = %s", (account_id,))
            account_active = cursor.fetchone()[0]
            print(f"   - Account active: {account_active} (needs to be true)")
        print()
        
        # 5. Get current WBUY price
        try:
            # Get API credentials for this account
            cursor.execute("""
                SELECT api_key, api_secret, base_url FROM accounts WHERE id = %s
            """, (account_id,))
            creds = cursor.fetchone()
            
            if creds:
                api_key, api_secret, base_url = creds
                client = AlpacaClient(api_key, api_secret, base_url)
                
                current_prices = await client.get_current_prices([symbol])
                current_price = current_prices.get(symbol)
                
                print(f"💰 CURRENT PRICE CHECK:")
                print(f"   {symbol} Current Price: ${current_price}")
                print(f"   Stop Loss Price: ${sl_price}")
                
                if current_price and current_price <= float(sl_price):
                    print(f"   🚨 SHOULD EXECUTE! Price ${current_price} <= Stop ${sl_price}")
                else:
                    print(f"   ✅ No execution needed. Price ${current_price} > Stop ${sl_price}")
                    
            else:
                print("❌ Could not get API credentials for price check")
                
        except Exception as e:
            print(f"❌ Error getting current price: {e}")
        
        print()
        print("🔧 NEXT STEPS:")
        if not monitor_result:
            print("   1. Fix the level monitor query issue")
        if sl_status != 'active':
            print("   2. Set stop loss status to 'active'")
        if status not in ('filled', 'closed'):
            print("   3. Fix trade status")
        if not is_active:
            print("   4. Activate the account")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        conn.close()

if __name__ == "__main__":
    asyncio.run(debug_trade_73()) 