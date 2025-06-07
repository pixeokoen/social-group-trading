from db import get_db_connection

conn = get_db_connection()
cursor = conn.cursor()

trade_id = 70

print(f"Testing API SQL query for Trade {trade_id}:")

# This is the exact query from the API
cursor.execute("""
    SELECT id, level_number, price, percentage, shares_quantity, status, executed_at, executed_price
    FROM take_profit_levels 
    WHERE trade_id = %s 
    ORDER BY level_number
""", (trade_id,))

tp_levels = cursor.fetchall()
print(f"Query returned {len(tp_levels)} levels")

for tp in tp_levels:
    print(f"Level {tp[1]}: ${tp[2]}, {tp[3]}%, {tp[4]} shares, status: {tp[5]}")

# Also test what gets built in the API
trade_dict = {'id': trade_id}
trade_dict['take_profit_levels'] = []

for tp in tp_levels:
    level_data = {
        'id': tp[0],
        'level_number': tp[1],
        'price': float(tp[2]) if tp[2] else 0,
        'percentage': float(tp[3]) if tp[3] else 0,
        'shares_quantity': float(tp[4]) if tp[4] else 0,
        'status': tp[5],
        'executed_at': tp[6],
        'executed_price': float(tp[7]) if tp[7] else None
    }
    trade_dict['take_profit_levels'].append(level_data)

print(f"\nBuilt take_profit_levels array:")
print(f"Length: {len(trade_dict['take_profit_levels'])}")
for level in trade_dict['take_profit_levels']:
    print(f"  {level}")

conn.close() 