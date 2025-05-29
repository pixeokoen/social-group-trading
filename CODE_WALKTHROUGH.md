# Code Walkthrough: Trade Data Flow

## Key Endpoints

### 1. GET /api/trades - Loads from Database

```python
@app.get("/api/trades")
async def get_trades(current_user: User = Depends(get_current_user)):
    # Load trades from LOCAL DATABASE
    cursor.execute("""
        SELECT * FROM trades 
        WHERE user_id = %s AND account_id = %s
    """)
    
    # Convert and return
    return trades_list
```

**Source**: PostgreSQL database
**Speed**: ~1-5ms
**When**: Every time you view the Trades page

### 2. GET /api/trades/sync - Updates Database from Alpaca

```python
@app.get("/api/trades/sync")
async def sync_trades_with_broker(current_user: User = Depends(get_current_user)):
    # Get updates from ALPACA
    order_status = await broker_client.get_order_status(order_id)
    
    # UPDATE LOCAL DATABASE with new info
    cursor.execute("""
        UPDATE trades 
        SET status = 'open',
            entry_price = %s
        WHERE id = %s
    """, (fill_price, trade_id))
    
    return {"trades_updated": updated_count}
```

**Source**: Alpaca API → Updates Database
**Speed**: ~200-500ms per trade
**When**: Manual sync button or auto every 30s

### 3. Background Sync Task - Auto Updates

```python
async def auto_sync_trades():
    while True:
        # Check ALPACA for updates
        order_status = await client.get_order_status(trade[1])
        
        # UPDATE DATABASE
        cursor.execute("""
            UPDATE trades 
            SET status = 'open',
                entry_price = %s
        """)
        
        # Wait 30 seconds
        await asyncio.sleep(30)
```

**Source**: Alpaca API → Updates Database
**Speed**: Runs in background
**When**: Every 30 seconds automatically

## The Flow

```
1. You place a trade
   └─> Alpaca API (execute)
   └─> Database (save with status='pending')

2. Background sync runs (30s)
   └─> Check Alpaca API
   └─> Update Database (status='open', price=150.25)

3. You view trades page
   └─> Load from Database
   └─> Display instantly
```

## Why Not Load Directly from Alpaca?

### ❌ Direct from Broker (Not Used)
```python
# This would be slow!
async def get_trades_direct():
    trades = await alpaca.get_all_orders()  # 500ms+
    positions = await alpaca.get_positions()  # 300ms+
    # Total: 800ms+ page load!
```

### ✅ From Database (Actually Used)
```python
# This is fast!
async def get_trades():
    cursor.execute("SELECT * FROM trades")  # 5ms
    # Total: 5ms page load!
```

## Summary

- **View Trades** = Database (fast)
- **Sync Trades** = Alpaca → Database (updates)
- **Result** = Fast page loads + accurate data 