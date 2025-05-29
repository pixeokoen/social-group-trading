import psycopg2
from psycopg2.extras import RealDictCursor
import os
from dotenv import load_dotenv
from urllib.parse import urlparse

load_dotenv()

# Database configuration
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': os.getenv('DB_PORT', '5432'),
    'database': os.getenv('DB_NAME', 'social_trading'),
    'user': os.getenv('DB_USER', 'postgres'),
    'password': os.getenv('DB_PASSWORD', 'postgres')
}

def get_db_connection():
    """Create database connection with support for DATABASE_URL"""
    
    # Check for DATABASE_URL first (Render, Heroku, etc.)
    database_url = os.getenv('DATABASE_URL')
    
    if database_url:
        # Parse DATABASE_URL
        # Handle both postgres:// and postgresql:// schemes
        if database_url.startswith('postgres://'):
            database_url = database_url.replace('postgres://', 'postgresql://', 1)
        
        return psycopg2.connect(database_url)
    else:
        # Fall back to individual variables
        return psycopg2.connect(
            host=os.getenv('DB_HOST'),
            database=os.getenv('DB_NAME'),
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD'),
            port=os.getenv('DB_PORT', 5432)
        )

def init_db():
    """Initialize database tables"""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        
        # Create users table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                username VARCHAR(50) UNIQUE NOT NULL,
                email VARCHAR(100) UNIQUE NOT NULL,
                password VARCHAR(255) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_active BOOLEAN DEFAULT TRUE
            )
        """)
        
        # Create whatsapp_messages table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS whatsapp_messages (
                id SERIAL PRIMARY KEY,
                raw_message TEXT NOT NULL,
                sender VARCHAR(255) NOT NULL,
                group_name VARCHAR(255) NOT NULL,
                timestamp TIMESTAMP NOT NULL,
                processed BOOLEAN DEFAULT FALSE,
                is_signal BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create signals table with enhanced fields
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS signals (
                id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                whatsapp_message_id INTEGER REFERENCES whatsapp_messages(id) ON DELETE CASCADE,
                symbol VARCHAR(20) NOT NULL,
                action VARCHAR(10) NOT NULL CHECK (action IN ('BUY', 'SELL')),
                quantity INTEGER,
                price DECIMAL(10, 2),
                stop_loss DECIMAL(10, 2),
                take_profit DECIMAL(10, 2),
                source VARCHAR(20) DEFAULT 'manual' CHECK (source IN ('manual', 'whatsapp')),
                original_message TEXT,
                status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'approved', 'rejected', 'executed')),
                approved_at TIMESTAMP,
                approved_by INTEGER REFERENCES users(id),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create indexes for signals table
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_signals_user_id ON signals(user_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_signals_status ON signals(status)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_signals_created_at ON signals(created_at)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_signals_whatsapp_message_id ON signals(whatsapp_message_id)")
        
        # Create trades table with enhanced fields
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS trades (
                id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                signal_id INTEGER REFERENCES signals(id) ON DELETE SET NULL,
                symbol VARCHAR(20) NOT NULL,
                action VARCHAR(10) NOT NULL CHECK (action IN ('BUY', 'SELL')),
                quantity INTEGER NOT NULL,
                entry_price DECIMAL(10, 2) NOT NULL,
                exit_price DECIMAL(10, 2),
                current_price DECIMAL(10, 2),
                pnl DECIMAL(10, 2),
                floating_pnl DECIMAL(10, 2),
                status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'open', 'closed', 'cancelled')),
                ibkr_order_id VARCHAR(50),
                ibkr_fill_price DECIMAL(10, 2),
                close_reason VARCHAR(255),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                opened_at TIMESTAMP,
                closed_at TIMESTAMP
            )
        """)
        
        # Create indexes for trades table
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_trades_user_id ON trades(user_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_trades_signal_id ON trades(signal_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_trades_status ON trades(status)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_trades_symbol ON trades(symbol)")
        
        # Create webhook_logs table for security and debugging
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS webhook_logs (
                id SERIAL PRIMARY KEY,
                instance_id VARCHAR(255),
                event_type VARCHAR(50),
                payload JSONB,
                processed BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create indexes for webhook_logs
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_webhook_logs_created_at ON webhook_logs(created_at)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_webhook_logs_processed ON webhook_logs(processed)")
        
        conn.commit()
        print("Database tables created successfully!")
        
    except psycopg2.Error as e:
        print(f"Error initializing database: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()

def test_connection():
    """Test database connection"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT version()")
        db_version = cursor.fetchone()
        print(f"Connected to PostgreSQL: {db_version[0]}")
        conn.close()
        return True
    except Exception as e:
        print(f"Database connection failed: {e}")
        return False

if __name__ == "__main__":
    # Test connection and initialize database
    if test_connection():
        init_db() 