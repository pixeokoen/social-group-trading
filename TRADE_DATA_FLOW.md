# Trade Data Flow Explained

## The Short Answer

**Trades are ALWAYS loaded from your local database**, not directly from the broker.

## How It Works

```
┌─────────────┐     Display      ┌──────────────┐
│   Frontend  │ ←───────────────  │   Local DB   │
└─────────────┘                   └──────┬───────┘
                                         │ ↑
                                         │ │ Updates
                                         │ │
                                         ↓ │
                                   ┌─────────────┐
                                   │   Alpaca    │
                                   │   Broker    │
                                   └─────────────┘
```

### 1. When You View Trades

```javascript
// Frontend: "Show me trades"
GET /api/trades

// Backend: "Here's what's in the database"
SELECT * FROM trades WHERE user_id = ? AND account_id = ?
```

The trades come from your **local PostgreSQL database**, not Alpaca.

### 2. When Sync Runs (Every 30 Seconds)

```python
# Background task checks with Alpaca
order_status = await alpaca.get_order_status(order_id)

# Updates local database
UPDATE trades SET status = 'filled', entry_price = 150.25
```

The sync **updates your local database** with the latest from Alpaca.

### 3. When You Click "Sync with Broker"

Same as automatic sync - it updates the local database, then the frontend reloads from the database.

## Why This Design?

### ✅ **Speed**
- Database queries: ~1ms
- Alpaca API calls: ~100-500ms
- Page loads are instant!

### ✅ **Reliability**
- Works even if Alpaca is down
- No API rate limits on viewing
- Your data is always accessible

### ✅ **Consistency**
- All users see the same data
- No conflicting information
- Single source of truth (your DB)

### ✅ **History**
- Keep records of all trades
- Track your performance
- Alpaca might only show recent trades

## Data Sources

| Action | Data Source | Why |
|--------|-------------|-----|
| View Trades | Local DB | Fast, always available |
| Place Trade | Alpaca → Then DB | Execute with broker first |
| Sync Status | Alpaca → Update DB | Get latest status |
| Analytics | Local DB | Historical data |

## Example Flow

1. **You execute a trade**
   - Sent to Alpaca
   - Order ID saved in local DB
   - Status: "pending"

2. **Background sync runs**
   - Checks order status with Alpaca
   - Alpaca says: "filled at $150.25"
   - Updates local DB: status = "open", price = 150.25

3. **You refresh the page**
   - Loads from local DB
   - Shows: "open" with fill price
   - No waiting for Alpaca API

## The Trade-Off

**Pros:**
- ⚡ Lightning fast page loads
- 🛡️ Works offline
- 📊 Complete history
- 🔒 Your data, your control

**Cons:**
- ⏱️ Up to 30-second delay for updates
- 💾 Need to maintain database
- 🔄 Requires sync process

## Manual Sync Available

Don't want to wait 30 seconds? Click "Sync with Broker" for immediate update.

## Summary

Your local database is the **display source**, while Alpaca is the **truth source**. The sync process keeps them aligned. This gives you the best of both worlds: fast access and accurate data. 