"""
Position Sync Process Module
Synchronizes positions with broker.
"""

import logging
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db import get_db_connection
from alpaca_client import AlpacaClient

logger = logging.getLogger(__name__)

async def sync_positions_process():
    """Sync positions with broker"""
    
    api_calls_made = 0
    conn = None
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get active accounts
        cursor.execute("""
            SELECT id, api_key, api_secret, account_type
            FROM accounts 
            WHERE is_active = TRUE AND broker = 'alpaca'
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
                
                # Get positions from broker
                positions = await client.get_positions()
                api_calls_made += 1
                
                logger.debug(f"Synced {len(positions)} positions for account {account_id}")
                
            except Exception as e:
                logger.error(f"Error syncing positions for account {account_id}: {e}")
                continue
        
        conn.commit()
        
        if api_calls_made > 0:
            logger.debug(f"Position sync completed - made {api_calls_made} API calls")
        
    except Exception as e:
        logger.error(f"Error in position sync process: {e}")
        if conn:
            conn.rollback()
    
    finally:
        if conn:
            conn.close()

sync_positions_process._api_calls = 2 