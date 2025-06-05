import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

def add_account_metrics():
    """Add realized_pnl, realized_pnl_updated_at, and win_rate columns to accounts table"""
    try:
        # Connect to database
        conn = psycopg2.connect(os.getenv('DATABASE_URL'))
        cursor = conn.cursor()
        
        # Add realized_pnl column
        cursor.execute("""
            ALTER TABLE accounts
            ADD COLUMN IF NOT EXISTS realized_pnl NUMERIC DEFAULT 0
        """)
        print("✅ Added realized_pnl column")
        
        # Add realized_pnl_updated_at column
        cursor.execute("""
            ALTER TABLE accounts
            ADD COLUMN IF NOT EXISTS realized_pnl_updated_at TIMESTAMP
        """)
        print("✅ Added realized_pnl_updated_at column")
        
        # Add win_rate column
        cursor.execute("""
            ALTER TABLE accounts
            ADD COLUMN IF NOT EXISTS win_rate NUMERIC DEFAULT 0
        """)
        print("✅ Added win_rate column")
        
        conn.commit()
        print("\n✅ Account metrics columns added successfully!")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Error adding account metrics columns: {e}")
        if 'conn' in locals():
            conn.rollback()
            conn.close()

if __name__ == "__main__":
    add_account_metrics() 