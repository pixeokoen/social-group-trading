import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

def migrate():
    """Add position tracking fields to trades table"""
    try:
        conn = psycopg2.connect(os.getenv('DATABASE_URL'))
        cursor = conn.cursor()
        
        # Add parent_trade_id to link closing trades to opening trades
        cursor.execute("""
            ALTER TABLE trades 
            ADD COLUMN IF NOT EXISTS parent_trade_id INTEGER REFERENCES trades(id) ON DELETE SET NULL
        """)
        
        # Add remaining_quantity to track partial closes
        cursor.execute("""
            ALTER TABLE trades 
            ADD COLUMN IF NOT EXISTS remaining_quantity DECIMAL(10, 4)
        """)
        
        # Add trade_type to distinguish between opening and closing trades
        cursor.execute("""
            ALTER TABLE trades 
            ADD COLUMN IF NOT EXISTS trade_type VARCHAR(20) DEFAULT 'opening'
        """)
        
        # Update existing trades to set remaining_quantity
        cursor.execute("""
            UPDATE trades 
            SET remaining_quantity = quantity 
            WHERE remaining_quantity IS NULL AND status = 'open'
        """)
        
        # Create index for parent_trade_id
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_trades_parent_trade_id 
            ON trades(parent_trade_id)
        """)
        
        conn.commit()
        print("✅ Position tracking fields added successfully!")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Error adding position tracking fields: {e}")
        if 'conn' in locals():
            conn.rollback()
            conn.close()

if __name__ == "__main__":
    migrate() 