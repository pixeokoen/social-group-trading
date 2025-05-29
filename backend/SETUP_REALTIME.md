# Setting Up Real-Time Trade Sync

## Prerequisites

- Working Social Group Trading installation
- Alpaca account with API credentials configured
- Python environment activated

## Setup Steps

### 1. Run Database Migration

Create the notifications table:

```bash
cd backend
python migrations/create_notifications_table.py
```

You should see:
```
Creating trade_notifications table...
✅ Successfully created trade_notifications table
✅ Table verified successfully
```

### 2. Install Dependencies

The required packages should already be installed, but verify:

```bash
pip install alpaca-py aiohttp
```

### 3. Start Services

#### Option A: All-in-One (Recommended)

**PowerShell:**
```powershell
cd backend
.\run_services.ps1
```

**Command Prompt:**
```cmd
cd backend
run_services.bat
```

#### Option B: Manual Start

**Terminal 1 - Main API:**
```bash
cd backend
python main.py
```

**Terminal 2 - Stream Bridge:**
```bash
cd backend
python stream_bridge.py
```

### 4. Verify Setup

1. Open the frontend at http://localhost:5173
2. Navigate to the Trades page
3. Look for the green "Real-time updates active" indicator
4. Execute a test trade
5. Watch for automatic updates without refreshing

## What You Should See

### In the Stream Bridge Console:
```
============================================================
Alpaca Stream Bridge Service
============================================================
Starting bridge streams for 1 accounts...
Starting bridge stream for account 1 (paper)...

[Stream Bridge] TradeEvent.NEW: AAPL BUY 100
[Stream Bridge] TradeEvent.FILL: AAPL BUY 100
  ✓ Order FILLED at $150.25
```

### In the Frontend:
- Green dot with "Real-time updates active"
- Blue notification banner when trades update
- Yellow highlight on updated trade rows
- Automatic status changes from "pending" to "open"

## Troubleshooting

### No Real-Time Updates

1. **Check Stream Bridge is Running**
   - Look for the stream bridge console window
   - Should show "Starting bridge streams..."

2. **Verify Database Migration**
   ```sql
   SELECT * FROM trade_notifications LIMIT 1;
   ```

3. **Check API Credentials**
   - Ensure Alpaca API keys are correct in .env
   - Paper trading keys for paper account

### Connection Issues

1. **Restart Services**
   - Stop all services (Ctrl+C)
   - Run setup script again

2. **Check Logs**
   - Stream bridge shows connection errors
   - Main API logs authentication issues

## Production Deployment

For production use:

1. **Use Process Manager**
   ```bash
   # Install PM2
   npm install -g pm2
   
   # Start services
   pm2 start main.py --name "trading-api"
   pm2 start stream_bridge.py --name "trading-stream"
   
   # Save configuration
   pm2 save
   pm2 startup
   ```

2. **Enable Auto-Restart**
   ```bash
   pm2 restart trading-stream --cron "0 */6 * * *"
   ```

3. **Monitor Logs**
   ```bash
   pm2 logs trading-stream
   ```

## Next Steps

- Test with paper trading first
- Monitor for a full trading day
- Set up alerts for stream disconnections
- Configure backup sync intervals as needed 