# Quick Start: Real-Time Trade Sync

## 🚀 One-Command Start (Windows)

### PowerShell (Recommended)
```powershell
cd backend
.\run_services.ps1
```

### Command Prompt
```cmd
cd backend
run_services.bat
```

### Manual Start
```powershell
# Terminal 1
cd backend
python main.py

# Terminal 2
cd backend
python stream_bridge.py
```

## 🔄 How It Works

1. **Instant Updates**: When you place a trade, the system receives updates within milliseconds
2. **No Manual Refresh**: Trades automatically update when filled, cancelled, or rejected
3. **Visual Feedback**: 
   - Green dot shows real-time connection is active
   - Blue notification banner for trade events
   - Yellow highlight on updated trades

## 📊 What Gets Updated Automatically

- ✅ Order fills (with actual fill price)
- ✅ Partial fills (updates quantity)
- ✅ Order cancellations
- ✅ Order rejections
- ✅ Position prices (every 30 seconds)

## 🎯 Example Flow

1. You execute a trade from the Signals page
2. Order shows as "pending" in Trades
3. When Alpaca fills the order:
   - Trade instantly updates to "open"
   - Shows actual fill price (not estimate)
   - Blue notification appears
   - Trade row highlights yellow briefly

## 🔍 Monitoring

Check if real-time sync is working:
- Look for green "Real-time updates active" indicator
- Watch for blue notification banners
- Check the stream bridge console for live events

## 🚨 Troubleshooting

**No real-time updates?**
1. Make sure stream bridge is running
2. Check Alpaca API credentials
3. Verify internet connection

**Updates delayed?**
- The system falls back to 30-second sync if streaming fails
- Restart the stream bridge service

## 🎉 Benefits

- **No more manual refresh** - Everything updates automatically
- **Accurate fill prices** - See exactly what you paid
- **Instant feedback** - Know immediately when orders execute
- **Works with multiple accounts** - All accounts stay in sync

## 📝 Notes

- Paper trading accounts work 24/7
- Live accounts only update during market hours
- The frontend polls for notifications every 3 seconds
- Full sync runs every 30 seconds as a backup 