"""
Migration to create trade_notifications table for real-time sync
"""
import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

def create_notifications_table():
    """Create the trade_notifications table if it doesn't exist"""
    conn = psycopg2.connect(
        host=os.getenv('DB_HOST'),
        database=os.getenv('DB_NAME'),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD'),
        port=os.getenv('DB_PORT', 5432)
    )
    
    try:
        cursor = conn.cursor()
        
        # Create trade_notifications table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS trade_notifications (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL,
                trade_id INTEGER,
                notification_type VARCHAR(50),
                data JSONB,
                read BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                
                -- Indexes for performance
                CONSTRAINT fk_user 
                    FOREIGN KEY(user_id) 
                    REFERENCES users(id) 
                    ON DELETE CASCADE,
                    
                CONSTRAINT fk_trade 
                    FOREIGN KEY(trade_id) 
                    REFERENCES trades(id) 
                    ON DELETE CASCADE
            );
            
            -- Create indexes
            CREATE INDEX IF NOT EXISTS idx_notifications_user_id ON trade_notifications(user_id);
            CREATE INDEX IF NOT EXISTS idx_notifications_created_at ON trade_notifications(created_at);
            CREATE INDEX IF NOT EXISTS idx_notifications_read ON trade_notifications(read);
            CREATE INDEX IF NOT EXISTS idx_notifications_user_unread ON trade_notifications(user_id, read) WHERE read = FALSE;
        """)
        
        conn.commit()
        print("✅ Successfully created trade_notifications table")
        
        # Check if table was created
        cursor.execute("""
            SELECT COUNT(*) FROM information_schema.tables 
            WHERE table_name = 'trade_notifications'
        """)
        
        if cursor.fetchone()[0] > 0:
            print("✅ Table verified successfully")
        else:
            print("❌ Table creation failed")
            
    except Exception as e:
        conn.rollback()
        print(f"❌ Error creating table: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    print("Creating trade_notifications table...")
    create_notifications_table() 