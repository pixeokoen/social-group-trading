"""
Notification Checker Process Module
Monitors trade notifications and triggers alerts.
"""

import logging
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db import get_db_connection

logger = logging.getLogger(__name__)

async def check_notifications_process():
    """Check for new trade notifications and process alerts"""
    
    conn = None
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check for recent notifications (last 24 hours)
        cursor.execute("""
            SELECT id, trade_id, notification_type, data, created_at
            FROM trade_notifications 
            WHERE created_at > NOW() - INTERVAL '24 hours'
            ORDER BY created_at DESC
            LIMIT 20
        """)
        
        notifications = cursor.fetchall()
        
        for notification in notifications:
            try:
                notif_id, trade_id, notif_type, data, created_at = notification
                
                # Process different notification types
                if notif_type in ['take_profit_executed', 'stop_loss_executed', 'order_filled']:
                    # Log the notification (no need to mark as processed for now)
                    logger.debug(f"Found notification: {notif_type} for trade {trade_id}")
                
            except Exception as e:
                logger.error(f"Error processing notification {notif_id}: {e}")
                continue
        
        conn.commit()
        
        if notifications:
            logger.debug(f"Processed {len(notifications)} notifications")
        
    except Exception as e:
        logger.error(f"Error in notification check process: {e}")
        if conn:
            conn.rollback()
    
    finally:
        if conn:
            conn.close()

check_notifications_process._api_calls = 0 