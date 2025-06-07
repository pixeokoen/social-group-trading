"""
Price Updater Process Module
Batch updates current prices for all open positions.
"""

import logging
from typing import Dict, List
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db import get_db_connection
from alpaca_client import AlpacaClient

logger = logging.getLogger(__name__)

async def update_prices_process():
    """Batch update current prices for all open positions"""
    
    api_calls_made = 0
    conn = None
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get all active accounts with open trades
        cursor.execute("""
            SELECT DISTINCT a.id, a.api_key, a.api_secret, a.account_type
            FROM accounts a
            JOIN trades t ON a.id = t.account_id
            WHERE a.is_active = TRUE 
            AND a.broker = 'alpaca'
            AND t.status IN ('filled', 'open')
        """)
        
        accounts = cursor.fetchall()
        
        for account in accounts:
            try:
                account_id, api_key, api_secret, account_type = account
                
                client = AlpacaClient(
                    api_key=api_key,
                    secret_key=api_secret,
                    paper=(account_type == 'paper')
                )
                
                # Get symbols needing price updates
                cursor.execute("""
                    SELECT DISTINCT symbol FROM trades 
                    WHERE account_id = %s 
                    AND status IN ('filled', 'open')
                    AND current_price IS NULL
                """, (account_id,))
                
                symbols = [row[0] for row in cursor.fetchall()]
                
                if symbols:
                    # Batch get prices
                    prices = await client.get_current_prices(symbols)
                    api_calls_made += 1
                    
                    # Update trades
                    for symbol, price in prices.items():
                        cursor.execute("""
                            UPDATE trades 
                            SET current_price = %s
                            WHERE account_id = %s AND symbol = %s AND status IN ('filled', 'open')
                        """, (price, account_id, symbol))
                
            except Exception as e:
                logger.error(f"Error updating prices for account {account_id}: {e}")
                continue
        
        conn.commit()
        
        if api_calls_made > 0:
            logger.debug(f"Price updates completed - made {api_calls_made} API calls")
        
    except Exception as e:
        logger.error(f"Error in price update process: {e}")
        if conn:
            conn.rollback()
    
    finally:
        if conn:
            conn.close()

update_prices_process._api_calls = 3 