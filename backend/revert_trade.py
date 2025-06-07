from db import get_db_connection

conn = get_db_connection()
cursor = conn.cursor()

# Revert Trade 70 status back to 'closed'
cursor.execute("UPDATE trades SET status = 'closed' WHERE id = 70")
conn.commit()
print('Reverted Trade 70 status back to closed')

# Verify the change
cursor.execute("SELECT id, symbol, status FROM trades WHERE id = 70")
trade = cursor.fetchone()
print(f'Trade {trade[0]} ({trade[1]}): {trade[2]}')

conn.close() 