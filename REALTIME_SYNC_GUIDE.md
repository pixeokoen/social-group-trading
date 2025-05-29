# Real-Time Trade Synchronization Guide

This guide explains the real-time synchronization options for keeping your trades constantly updated with Alpaca.

## Overview

The system now provides multiple real-time synchronization methods:

1. **WebSocket Streaming** - Real-time push updates from Alpaca
2. **Trade Notifications** - Database-backed notification system
3. **Frontend WebSocket** - Real-time updates to the UI (coming soon)
4. **Polling Fallback** - Auto-sync every 30 seconds

## Architecture

```
┌─────────────┐     WebSocket      ┌────────────────┐     DB Updates    ┌──────────┐
│   Alpaca    │ ─────────────────> │ Stream Bridge  │ ───────────────> │ Database │
│   Broker    │                    │    Service     │                   └──────────┘
└─────────────┘                    └────────────────┘                         │
                                           │                                   │
                                           │ Notifications                     │
                                           ▼                                   ▼
                                    ┌──────────────┐      API Calls     ┌──────────┐
                                    │ Notification │ <───────────────── │ Frontend │
                                    │    Table     │                    └──────────┘
                                    └──────────────┘
```

## Real-Time Streaming Service

### What It Does

The streaming service (`stream_bridge.py`) provides:
- **Instant Updates**: Receives trade events within milliseconds
- **Automatic Sync**: No manual refresh needed
- **Event Types**:
  - Order accepted
  - Order filled (partial or complete)
  - Order cancelled
  - Order rejected
  - Order expired

### How to Run

```bash
cd backend

# Run the streaming service
python stream_bridge.py
```

### Benefits

1. **Real-Time Updates**: Get notified the moment an order fills
2. **No Polling**: Efficient push-based updates
3. **Reliable**: Automatic reconnection on disconnect
4. **Multi-Account**: Streams all accounts simultaneously

## Trade Notifications

When trade events occur, the system creates notifications that include:

```json
{
  "trade_id": 123,
  "symbol": "AAPL",
  "action": "BUY",
  "type": "order_filled",
  "status": "open",
  "message": "Order filled at $150.25",
  "fill_price": 150.25,
  "quantity": 100,
  "account": "My Trading Account",
  "timestamp": "2024-01-10T15:30:00Z"
}
```

### Notification Types

- `order_accepted` - Broker accepted the order
- `order_filled` - Order completely filled
- `order_partial_fill` - Order partially filled
- `order_cancelled` - Order was cancelled
- `order_rejected` - Broker rejected the order
- `order_expired` - Order expired (e.g., day order after market close)

### API Endpoints

```bash
# Get recent notifications
GET /api/notifications/trades?limit=20&unread_only=true

# Mark notification as read
POST /api/notifications/trades/{id}/read
```

## Frontend Integration

### Option 1: Polling Notifications (Simple)

```javascript
// Poll for new notifications every 5 seconds
setInterval(async () => {
  const response = await axios.get('/api/notifications/trades?unread_only=true')
  const notifications = response.data
  
  notifications.forEach(notification => {
    // Show toast/alert
    showNotification(notification.data.message)
    
    // Update trades list
    if (notification.data.type === 'order_filled') {
      refreshTrades()
    }
    
    // Mark as read
    axios.post(`/api/notifications/trades/${notification.id}/read`)
  })
}, 5000)
```

### Option 2: WebSocket Connection (Advanced)

```javascript
// Connect to WebSocket for real-time updates
const token = localStorage.getItem('token')
const ws = new WebSocket(`ws://localhost:8000/ws/${token}`)

ws.onmessage = (event) => {
  const data = JSON.parse(event.data)
  
  if (data.type === 'trade_update') {
    // Update UI immediately
    updateTradeInList(data.data)
    showNotification(data.data.message)
  }
}

// Keep connection alive
setInterval(() => {
  if (ws.readyState === WebSocket.OPEN) {
    ws.send('ping')
  }
}, 30000)
```

## Comparison of Methods

| Method | Latency | Complexity | Resources | Best For |
|--------|---------|------------|-----------|----------|
| WebSocket Streaming | <100ms | High | Low | Production systems |
| Notification Polling | 1-5s | Low | Medium | Simple implementations |
| Frontend WebSocket | <100ms | Medium | Low | Real-time UI |
| Sync Polling | 30s | Low | High | Fallback/backup |

## Best Practices

### 1. Run the Stream Bridge

For production, always run the stream bridge service:

```bash
# Run as a service/daemon
nohup python stream_bridge.py > stream.log 2>&1 &

# Or with systemd
sudo systemctl start alpaca-stream
```

### 2. Handle Notifications

```javascript
// In your frontend
async function checkNotifications() {
  try {
    const { data } = await axios.get('/api/notifications/trades?unread_only=true')
    
    for (const notification of data) {
      // Process based on type
      switch(notification.data.type) {
        case 'order_filled':
          // Update trade status
          updateTradeStatus(notification.data.trade_id, 'open')
          break
        case 'order_cancelled':
        case 'order_rejected':
          // Remove from pending
          removeFromPending(notification.data.trade_id)
          break
      }
      
      // Mark as read
      await axios.post(`/api/notifications/trades/${notification.id}/read`)
    }
  } catch (error) {
    console.error('Failed to check notifications:', error)
  }
}

// Check every 3 seconds
setInterval(checkNotifications, 3000)
```

### 3. Graceful Degradation

Always have a fallback sync mechanism:

```javascript
// Primary: Check notifications
checkNotifications()

// Fallback: Full sync every 30 seconds
setInterval(() => {
  syncTrades()
}, 30000)
```

## Implementation Steps

1. **Start the Stream Bridge**
   ```bash
   cd backend
   python stream_bridge.py
   ```

2. **Monitor Notifications**
   - Check the `trade_notifications` table
   - Use the API endpoints to fetch updates

3. **Update Frontend**
   - Add notification polling
   - Show real-time updates
   - Remove manual sync dependency

## Troubleshooting

### Stream Not Connecting
- Check Alpaca API credentials
- Verify network connectivity
- Check if market is open (paper trading works 24/7)

### Notifications Not Appearing
- Verify stream bridge is running
- Check database connection
- Look at stream bridge logs

### Updates Delayed
- Stream bridge might have disconnected
- Check for errors in logs
- Restart the service

## Example: Complete Setup

```bash
# Terminal 1: Run main app
cd backend
python main.py

# Terminal 2: Run stream bridge
cd backend
python stream_bridge.py

# Terminal 3: Run frontend
cd frontend
npm run dev
```

## Benefits of Real-Time Sync

1. **Instant Feedback**: Know immediately when orders fill
2. **Accurate Prices**: Get actual fill prices, not estimates
3. **Better UX**: No need for manual refresh
4. **Reduced API Calls**: Push updates instead of polling
5. **Multi-Account**: All accounts stay synchronized

## Future Enhancements

1. **Mobile Push Notifications**
2. **Email Alerts** for important events
3. **Webhook Forwarding** to external services
4. **Trade Analytics** based on real-time data
5. **Alpaca Webhooks** when they become available

## Summary

The real-time sync system ensures your trades are always up-to-date without manual intervention. By running the stream bridge service, you get instant updates for all trade events, providing a professional trading experience with minimal latency. 