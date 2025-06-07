#!/usr/bin/env python3
"""
Migration: Add sell_all status and override tracking
"""
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db import get_db_connection

def run_migration():
    """Add cancelled_by_sell_all status and override tracking fields"""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        
        print("🔄 Adding cancelled_by_sell_all status to take_profit_levels...")
        cursor.execute("""
            ALTER TABLE take_profit_levels 
            DROP CONSTRAINT IF EXISTS take_profit_levels_status_check
        """)
        
        cursor.execute("""
            ALTER TABLE take_profit_levels 
            ADD CONSTRAINT take_profit_levels_status_check 
            CHECK (status IN ('pending', 'executed', 'cancelled', 'cancelled_by_sell_all'))
        """)
        
        print("🔄 Adding cancelled_by_sell_all status to stop_loss_levels...")
        cursor.execute("""
            ALTER TABLE stop_loss_levels 
            DROP CONSTRAINT IF EXISTS stop_loss_levels_status_check
        """)
        
        cursor.execute("""
            ALTER TABLE stop_loss_levels 
            ADD CONSTRAINT stop_loss_levels_status_check 
            CHECK (status IN ('active', 'executed', 'cancelled', 'cancelled_by_sell_all'))
        """)
        
        print("🔄 Adding override tracking fields...")
        cursor.execute("""
            ALTER TABLE take_profit_levels 
            ADD COLUMN IF NOT EXISTS override_price DECIMAL(10,2),
            ADD COLUMN IF NOT EXISTS override_date TIMESTAMP
        """)
        
        cursor.execute("""
            ALTER TABLE stop_loss_levels 
            ADD COLUMN IF NOT EXISTS override_price DECIMAL(10,2),
            ADD COLUMN IF NOT EXISTS override_date TIMESTAMP
        """)
        
        conn.commit()
        print("✅ Migration completed successfully!")
        
    except Exception as e:
        conn.rollback()
        print(f"❌ Migration failed: {e}")
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    run_migration() 