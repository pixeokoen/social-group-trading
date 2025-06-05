import os
import psycopg2
from passlib.context import CryptContext
from dotenv import load_dotenv

load_dotenv()

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def init_database():
    """Initialize database with all required tables"""
    try:
        # Connect to database
        conn = psycopg2.connect(os.getenv('DATABASE_URL'))
        cursor = conn.cursor()
        
        # Create users table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                username VARCHAR(50) UNIQUE NOT NULL,
                email VARCHAR(100) UNIQUE NOT NULL,
                password VARCHAR(255) NOT NULL,
                is_active BOOLEAN DEFAULT true,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create accounts table
        cursor.execute("""
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
            )
        """)
        
        # Create user_sessions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_sessions (
                user_id INTEGER PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
                active_account_id INTEGER REFERENCES accounts(id) ON DELETE SET NULL,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create signals table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS signals (
                id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES users(id),
                account_id INTEGER REFERENCES accounts(id) ON DELETE SET NULL,
                symbol VARCHAR(20) NOT NULL,
                action VARCHAR(10) NOT NULL,
                quantity DECIMAL(10, 2),
                price DECIMAL(10, 2),
                stop_loss DECIMAL(10, 2),
                take_profit DECIMAL(10, 2),
                source VARCHAR(50),
                original_message TEXT,
                status VARCHAR(20) DEFAULT 'pending',
                approved_by INTEGER REFERENCES users(id),
                approved_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create trades table
        cursor.execute("""
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
            )
        """)
        
        # Create take_profit_levels table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS take_profit_levels (
                id SERIAL PRIMARY KEY,
                trade_id INTEGER REFERENCES trades(id) ON DELETE CASCADE,
                level_number INTEGER NOT NULL,
                price DECIMAL(10, 2) NOT NULL,
                percentage DECIMAL(5, 2) NOT NULL,
                shares_quantity DECIMAL(10, 4) NOT NULL,
                status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'executed', 'cancelled')),
                executed_at TIMESTAMP,
                executed_price DECIMAL(10, 2),
                broker_order_id VARCHAR(255),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create stop_loss_levels table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS stop_loss_levels (
                id SERIAL PRIMARY KEY,
                trade_id INTEGER REFERENCES trades(id) ON DELETE CASCADE,
                price DECIMAL(10, 2) NOT NULL,
                status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'executed', 'cancelled')),
                executed_at TIMESTAMP,
                executed_price DECIMAL(10, 2),
                executed_shares DECIMAL(10, 4),
                broker_order_id VARCHAR(255),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create trade_notifications table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS trade_notifications (
                id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES users(id),
                trade_id INTEGER REFERENCES trades(id) ON DELETE CASCADE,
                notification_type VARCHAR(50),
                data JSONB,
                read BOOLEAN DEFAULT false,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_signals_user_id ON signals(user_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_signals_status ON signals(status)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_trades_user_id ON trades(user_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_trades_status ON trades(status)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_notifications_user_id ON trade_notifications(user_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_notifications_read ON trade_notifications(read)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_take_profit_levels_trade_id ON take_profit_levels(trade_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_take_profit_levels_status ON take_profit_levels(status)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_stop_loss_levels_trade_id ON stop_loss_levels(trade_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_stop_loss_levels_status ON stop_loss_levels(status)")
        
        conn.commit()
        print("✅ Database tables created successfully!")
        
        # Create admin user if it doesn't exist
        cursor.execute("SELECT id FROM users WHERE username = 'admin'")
        if not cursor.fetchone():
            admin_password = os.getenv('ADMIN_PASSWORD', 'admin123')  # Change this in production
            hashed_password = pwd_context.hash(admin_password)
            
            cursor.execute("""
                INSERT INTO users (username, email, password, is_active)
                VALUES (%s, %s, %s, %s)
            """, ('admin', 'admin@example.com', hashed_password, True))
            
            conn.commit()
            print("\n✅ Admin user created successfully!")
            print(f"Username: admin")
            print(f"Password: {admin_password}")
            print("\nIMPORTANT: Please change the admin password in production!")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Error initializing database: {e}")
        if 'conn' in locals():
            conn.rollback()
            conn.close()

if __name__ == "__main__":
    init_database() 