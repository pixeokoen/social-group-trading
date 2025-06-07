from db import get_db_connection

conn = get_db_connection()
cursor = conn.cursor()

# Update Trade 70 status to 'open'
cursor.execute("UPDATE trades SET status = 'open' WHERE id = 70")
conn.commit()
print('Updated Trade 70 status to open')

# Verify the change
cursor.execute("SELECT id, symbol, status FROM trades WHERE id = 70")
trade = cursor.fetchone()
print(f'Trade {trade[0]} ({trade[1]}): {trade[2]}')

conn.close() 