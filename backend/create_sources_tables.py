"""
Create tables for managing signal sources and their account mappings
"""
import psycopg2
from psycopg2.extras import RealDictCursor
import os
from dotenv import load_dotenv

load_dotenv()

def create_sources_tables():
    """Create tables for signal sources management"""
    conn = psycopg2.connect(
        host=os.getenv('DB_HOST'),
        database=os.getenv('DB_NAME'),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD'),
        port=os.getenv('DB_PORT', 5432)
    )
    
    try:
        cursor = conn.cursor()
        
        # Create signal_sources table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS signal_sources (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                source_type VARCHAR(50) NOT NULL, -- 'whapi', 'telegram', 'discord', etc.
                source_identifier VARCHAR(255) NOT NULL, -- descriptive name for the channel/instance
                name VARCHAR(255) NOT NULL, -- User-friendly display name
                description TEXT,
                is_active BOOLEAN DEFAULT TRUE,
                filter_config JSONB DEFAULT '{}', -- includes chat_id and other filters
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id, source_type, source_identifier)
            )
        """)
        
        # Create source_accounts mapping table (many-to-many)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS source_accounts (
                id SERIAL PRIMARY KEY,
                source_id INTEGER NOT NULL REFERENCES signal_sources(id) ON DELETE CASCADE,
                account_id INTEGER NOT NULL REFERENCES accounts(id) ON DELETE CASCADE,
                auto_approve BOOLEAN DEFAULT FALSE, -- Auto-approve signals from this source
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(source_id, account_id)
            )
        """)
        
        # Add source_id to signals table to track which configured source generated it
        cursor.execute("""
            ALTER TABLE signals 
            ADD COLUMN IF NOT EXISTS source_id INTEGER REFERENCES signal_sources(id) ON DELETE SET NULL
        """)
        
        # Add instance_id to whatsapp_messages for source identification
        cursor.execute("""
            ALTER TABLE whatsapp_messages 
            ADD COLUMN IF NOT EXISTS instance_id VARCHAR(255)
        """)
        
        # Create indexes for better performance
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_signal_sources_user ON signal_sources(user_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_signal_sources_type ON signal_sources(source_type)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_source_accounts_source ON source_accounts(source_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_source_accounts_account ON source_accounts(account_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_signals_source ON signals(source_id)")
        
        conn.commit()
        print("✅ Created signal sources tables successfully")
        
    except Exception as e:
        conn.rollback()
        print(f"❌ Error creating tables: {e}")
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    create_sources_tables() 