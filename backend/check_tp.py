from db import get_db_connection

conn = get_db_connection()
cursor = conn.cursor()

cursor.execute('SELECT COUNT(*) FROM take_profit_levels')
tp_count = cursor.fetchone()[0]
print(f'Total take profit levels: {tp_count}')

if tp_count > 0:
    cursor.execute('''
        SELECT tp.trade_id, t.symbol, tp.level_number, tp.price, tp.status, t.status as trade_status
        FROM take_profit_levels tp 
        JOIN trades t ON tp.trade_id = t.id 
        ORDER BY tp.trade_id, tp.level_number
        LIMIT 10
    ''')
    print('\nSample take profit levels:')
    for row in cursor.fetchall():
        print(f'Trade {row[0]} ({row[1]}, {row[5]}): Level {row[2]}, ${row[3]}, {row[4]}')

# Check open trades specifically
cursor.execute('''
    SELECT t.id, t.symbol, t.status,
           (SELECT COUNT(*) FROM take_profit_levels WHERE trade_id = t.id) as tp_count
    FROM trades t 
    WHERE t.status IN ('open', 'filled')
    ORDER BY t.id DESC
    LIMIT 10
''')
print('\nOpen/filled trades:')
for row in cursor.fetchall():
    print(f'Trade {row[0]} ({row[1]}, {row[2]}): {row[3]} TP levels')

conn.close() 