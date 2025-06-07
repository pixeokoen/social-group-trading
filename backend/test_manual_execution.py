#!/usr/bin/env python3
"""
Manually test stop loss execution for trade 73
"""
import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from db import get_db_connection
from alpaca_client import AlpacaClient
from process_modules.level_monitor import execute_stop_loss_level

async def test_manual_execution():
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        
        print("🧪 MANUAL STOP LOSS EXECUTION TEST FOR TRADE 73")
        print("=" * 60)
        
        # Get trade 73 details
        cursor.execute("""
            SELECT sl.id, sl.trade_id, sl.price, t.quantity,
                   t.symbol, t.action, t.account_id
            FROM stop_loss_levels sl
            JOIN trades t ON sl.trade_id = t.id
            WHERE t.id = 73 AND sl.status = 'active'
        """)
        
        result = cursor.fetchone()
        if not result:
            print("❌ Trade 73 stop loss not found or not active")
            return
            
        sl_id, trade_id, stop_price, quantity, symbol, action, account_id = result
        
        print(f"📊 EXECUTION DETAILS:")
        print(f"   Stop Loss ID: {sl_id}")
        print(f"   Trade ID: {trade_id}")
        print(f"   Symbol: {symbol}")
        print(f"   Stop Price: ${stop_price}")
        print(f"   Quantity: {quantity}")
        print(f"   Action: {action}")
        print()
        
        # Get API credentials
        cursor.execute("""
            SELECT api_key, api_secret, base_url FROM accounts WHERE id = %s
        """, (account_id,))
        creds = cursor.fetchone()
        
        if not creds:
            print("❌ No API credentials found")
            return
            
        api_key, api_secret, base_url = creds
        client = AlpacaClient(api_key, api_secret, base_url)
        
        # Get current price
        current_prices = await client.get_current_prices([symbol])
        current_price = current_prices.get(symbol, 0)
        
        print(f"💰 PRICE CHECK:")
        print(f"   Current Price: ${current_price}")
        print(f"   Stop Price: ${stop_price}")
        print(f"   Should Execute: {current_price <= float(stop_price)}")
        print()
        
        if current_price <= float(stop_price):
            print(f"🚀 EXECUTING STOP LOSS...")
            
            try:
                # Call the actual execution function
                success = await execute_stop_loss_level(
                    cursor, client, sl_id, trade_id, symbol, quantity, current_price
                )
                
                if success:
                    print("✅ STOP LOSS EXECUTED SUCCESSFULLY!")
                    conn.commit()
                    
                    # Check what happened
                    cursor.execute("""
                        SELECT status, executed_at, executed_price, broker_order_id 
                        FROM stop_loss_levels WHERE id = %s
                    """, (sl_id,))
                    updated_sl = cursor.fetchone()
                    
                    if updated_sl:
                        status, executed_at, executed_price, broker_order_id = updated_sl
                        print(f"📊 UPDATED STOP LOSS:")
                        print(f"   Status: {status}")
                        print(f"   Executed At: {executed_at}")
                        print(f"   Executed Price: ${executed_price}")
                        print(f"   Broker Order ID: {broker_order_id}")
                        
                    # Check trade status
                    cursor.execute("SELECT status, close_reason FROM trades WHERE id = %s", (trade_id,))
                    trade_status = cursor.fetchone()
                    if trade_status:
                        print(f"📊 UPDATED TRADE:")
                        print(f"   Status: {trade_status[0]}")
                        print(f"   Close Reason: {trade_status[1]}")
                        
                else:
                    print("❌ STOP LOSS EXECUTION FAILED!")
                    conn.rollback()
                    
            except Exception as e:
                print(f"❌ ERROR DURING EXECUTION: {e}")
                import traceback
                traceback.print_exc()
                conn.rollback()
        else:
            print("ℹ️  Stop loss should not execute (price above stop)")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        conn.close()

if __name__ == "__main__":
    asyncio.run(test_manual_execution()) 