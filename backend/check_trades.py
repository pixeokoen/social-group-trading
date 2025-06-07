from db import get_db_connection

conn = get_db_connection()
cursor = conn.cursor()

cursor.execute("SELECT id, symbol, status FROM trades ORDER BY id DESC LIMIT 10")
print('Recent trades:')
for row in cursor.fetchall():
    print(f'Trade {row[0]} ({row[1]}): {row[2]}')

cursor.execute("SELECT status, COUNT(*) FROM trades GROUP BY status")
print('\nTrade status counts:')
for row in cursor.fetchall():
    print(f'{row[0]}: {row[1]}')

conn.close() 