#!/usr/bin/env python3
"""
Add monitoring tables for take profit and stop loss levels
"""
import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from db import get_db_connection

def add_monitoring_tables():
    """Add take_profit_levels and stop_loss_levels tables"""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        
        print("Adding take_profit_levels table...")
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
        
        print("Adding stop_loss_levels table...")
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
        
        print("Adding indexes...")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_take_profit_levels_trade_id ON take_profit_levels(trade_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_take_profit_levels_status ON take_profit_levels(status)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_stop_loss_levels_trade_id ON stop_loss_levels(trade_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_stop_loss_levels_status ON stop_loss_levels(status)")
        
        conn.commit()
        print("✅ Monitoring tables added successfully!")
        
        # Verify tables exist
        cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' AND table_name IN ('take_profit_levels', 'stop_loss_levels')")
        tables = cursor.fetchall()
        print(f"✅ Verified tables exist: {[t[0] for t in tables]}")
        
    except Exception as e:
        print(f"❌ Error adding monitoring tables: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    add_monitoring_tables() 