from db import get_db_connection

conn = get_db_connection()
cursor = conn.cursor()

print("Trades table columns:")
cursor.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'trades' ORDER BY ordinal_position")
trades_columns = [row[0] for row in cursor.fetchall()]
print(trades_columns)

print("\nTake profit levels table columns:")
cursor.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'take_profit_levels' ORDER BY ordinal_position")
tp_columns = [row[0] for row in cursor.fetchall()]
print(tp_columns)

print("\nSample trades:")
cursor.execute("SELECT * FROM trades LIMIT 3")
sample_trades = cursor.fetchall()
for trade in sample_trades:
    print(trade)

print("\nTake profit levels count:")
cursor.execute("SELECT COUNT(*) FROM take_profit_levels")
tp_count = cursor.fetchone()[0]
print(f"Total: {tp_count}")

if tp_count > 0:
    print("\nSample take profit levels:")
    cursor.execute("SELECT * FROM take_profit_levels LIMIT 5")
    sample_tp = cursor.fetchall()
    for tp in sample_tp:
        print(tp)

conn.close() 