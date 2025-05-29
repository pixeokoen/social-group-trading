"""
Update signal sources table to support unique webhooks and chat filtering
"""
import psycopg2
from psycopg2.extras import RealDictCursor
import os
import secrets
from dotenv import load_dotenv

load_dotenv()

def update_sources_for_webhooks():
    """Update signal sources table for unique webhooks"""
    conn = psycopg2.connect(
        host=os.getenv('DB_HOST'),
        database=os.getenv('DB_NAME'),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD'),
        port=os.getenv('DB_PORT', 5432)
    )
    
    try:
        cursor = conn.cursor()
        
        # Add webhook_token for unique webhook URLs
        cursor.execute("""
            ALTER TABLE signal_sources 
            ADD COLUMN IF NOT EXISTS webhook_token VARCHAR(64) UNIQUE
        """)
        
        # Update filter_config type to ensure it's JSONB
        cursor.execute("""
            ALTER TABLE signal_sources 
            ALTER COLUMN filter_config TYPE JSONB USING filter_config::JSONB
        """)
        
        # Create index on webhook_token for fast lookups
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_signal_sources_webhook_token 
            ON signal_sources(webhook_token) WHERE webhook_token IS NOT NULL
        """)
        
        # Generate webhook tokens for existing sources
        cursor.execute("SELECT id FROM signal_sources WHERE webhook_token IS NULL")
        sources = cursor.fetchall()
        
        for source in sources:
            webhook_token = secrets.token_urlsafe(32)
            cursor.execute(
                "UPDATE signal_sources SET webhook_token = %s WHERE id = %s",
                (webhook_token, source[0])
            )
        
        conn.commit()
        print("✅ Updated signal sources table for webhook support")
        
    except Exception as e:
        conn.rollback()
        print(f"❌ Error updating tables: {e}")
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    update_sources_for_webhooks() 