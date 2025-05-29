import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

# Database schema
schema = """
-- Users table
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Accounts table (trading accounts)
CREATE TABLE IF NOT EXISTS accounts (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    account_type VARCHAR(20) NOT NULL,
    broker VARCHAR(50) NOT NULL,
    api_key VARCHAR(255),
    api_secret VARCHAR(255),
    base_url VARCHAR(255),
    is_active BOOLEAN DEFAULT true,
    is_default BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- User sessions table
CREATE TABLE IF NOT EXISTS user_sessions (
    user_id INTEGER PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    active_account_id INTEGER REFERENCES accounts(id) ON DELETE SET NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Signal sources table
CREATE TABLE IF NOT EXISTS signal_sources (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    source_type VARCHAR(50) NOT NULL,
    source_identifier VARCHAR(255),
    name VARCHAR(100) NOT NULL,
    description TEXT,
    is_active BOOLEAN DEFAULT true,
    filter_config JSONB DEFAULT '{}',
    webhook_token VARCHAR(255) UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Source-account mappings
CREATE TABLE IF NOT EXISTS source_accounts (
    id SERIAL PRIMARY KEY,
    source_id INTEGER REFERENCES signal_sources(id) ON DELETE CASCADE,
    account_id INTEGER REFERENCES accounts(id) ON DELETE CASCADE,
    auto_approve BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(source_id, account_id)
);

-- WhatsApp messages table
CREATE TABLE IF NOT EXISTS whatsapp_messages (
    id SERIAL PRIMARY KEY,
    raw_message TEXT,
    sender VARCHAR(255),
    group_name VARCHAR(255),
    timestamp TIMESTAMP,
    instance_id VARCHAR(255),
    is_signal BOOLEAN DEFAULT false,
    processed BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Signals table
CREATE TABLE IF NOT EXISTS signals (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    account_id INTEGER REFERENCES accounts(id) ON DELETE SET NULL,
    whatsapp_message_id INTEGER REFERENCES whatsapp_messages(id) ON DELETE SET NULL,
    symbol VARCHAR(20) NOT NULL,
    action VARCHAR(10) NOT NULL,
    quantity DECIMAL(10, 2),
    price DECIMAL(10, 2),
    stop_loss DECIMAL(10, 2),
    take_profit DECIMAL(10, 2),
    source VARCHAR(50),
    source_id INTEGER REFERENCES signal_sources(id) ON DELETE SET NULL,
    original_message TEXT,
    remarks TEXT,
    analysis_notes TEXT,
    status VARCHAR(20) DEFAULT 'pending',
    approved_by INTEGER REFERENCES users(id),
    approved_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Trades table
CREATE TABLE IF NOT EXISTS trades (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    account_id INTEGER REFERENCES accounts(id) ON DELETE SET NULL,
    signal_id INTEGER REFERENCES signals(id) ON DELETE SET NULL,
    symbol VARCHAR(20) NOT NULL,
    action VARCHAR(10) NOT NULL,
    quantity DECIMAL(10, 4) NOT NULL,
    entry_price DECIMAL(10, 2),
    exit_price DECIMAL(10, 2),
    current_price DECIMAL(10, 2),
    stop_loss DECIMAL(10, 2),
    take_profit DECIMAL(10, 2),
    pnl DECIMAL(10, 2),
    floating_pnl DECIMAL(10, 2),
    status VARCHAR(20) DEFAULT 'pending',
    broker_order_id VARCHAR(255),
    broker_fill_price DECIMAL(10, 2),
    opened_at TIMESTAMP,
    closed_at TIMESTAMP,
    close_reason VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Webhook logs table
CREATE TABLE IF NOT EXISTS webhook_logs (
    id SERIAL PRIMARY KEY,
    instance_id VARCHAR(255),
    event_type VARCHAR(50),
    payload JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Trade notifications table
CREATE TABLE IF NOT EXISTS trade_notifications (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    type VARCHAR(50),
    data JSONB,
    read BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""

def init_database():
    """Initialize database with all required tables"""
    try:
        # Connect to database
        conn = psycopg2.connect(os.getenv('DATABASE_URL'))
        cursor = conn.cursor()
        
        # Create all tables
        cursor.execute(schema)
        
        # Commit changes
        conn.commit()
        print("Database initialized successfully!")
        
        # Check if admin user exists
        cursor.execute("SELECT COUNT(*) FROM users WHERE username = 'admin'")
        if cursor.fetchone()[0] == 0:
            print("\nNo admin user found. Please create one using the register endpoint.")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"Error initializing database: {e}")

if __name__ == "__main__":
    init_database() 