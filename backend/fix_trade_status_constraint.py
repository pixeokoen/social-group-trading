#!/usr/bin/env python3
"""
Fix trade status constraint to allow 'filled' status
"""
import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from db import get_db_connection

def fix_trade_status_constraint():
    """Update trades table constraint to allow 'filled' status"""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        
        print("🔄 Fixing trade status constraint...")
        
        # Drop existing constraint
        cursor.execute("""
            ALTER TABLE trades 
            DROP CONSTRAINT IF EXISTS trades_status_check
        """)
        
        # Add new constraint with 'filled' status
        cursor.execute("""
            ALTER TABLE trades 
            ADD CONSTRAINT trades_status_check 
            CHECK (status IN ('pending', 'open', 'closed', 'cancelled', 'filled'))
        """)
        
        conn.commit()
        print("✅ Successfully updated trade status constraint to include 'filled'")
        
        # Verify the change
        cursor.execute("""
            SELECT constraint_name, check_clause 
            FROM information_schema.check_constraints 
            WHERE constraint_name = 'trades_status_check'
        """)
        result = cursor.fetchone()
        if result:
            print(f"📋 New constraint: {result[1]}")
        
    except Exception as e:
        print(f"❌ Error fixing constraint: {e}")
        conn.rollback()
    
    finally:
        conn.close()

if __name__ == "__main__":
    fix_trade_status_constraint() 