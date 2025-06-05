#!/usr/bin/env python3
"""
Migration to add trade linking functionality
"""
import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

def add_trade_linking():
    """Add link_group_id to trades table for trade linking"""
    conn = psycopg2.connect(
        host=os.getenv('DB_HOST'),
        database=os.getenv('DB_NAME'),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD'),
        port=os.getenv('DB_PORT', 5432)
    )
    
    try:
        cursor = conn.cursor()
        
        print("Adding link_group_id to trades table...")
        cursor.execute("""
            ALTER TABLE trades 
            ADD COLUMN IF NOT EXISTS link_group_id UUID DEFAULT NULL
        """)
        
        print("Adding index for link_group_id...")
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_trades_link_group_id 
            ON trades(link_group_id) 
            WHERE link_group_id IS NOT NULL
        """)
        
        conn.commit()
        print("✅ Successfully added trade linking support")
        
    except Exception as e:
        print(f"❌ Error adding trade linking: {e}")
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()

if __name__ == '__main__':
    add_trade_linking() 