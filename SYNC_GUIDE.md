# Trade Synchronization Guide

This guide explains how the trade synchronization system works to keep your local trades in sync with Alpaca.

## Overview

The system provides multiple ways to keep your trades synchronized:

1. **Automatic Frontend Sync** - Every 30 seconds while viewing the Trades page
2. **Manual Sync Button** - Click "Sync with Broker" anytime
3. **Import Positions** - Import existing positions from Alpaca
4. **Background Sync Service** - Continuous sync process (optional)

## Why Synchronization is Important

- **Order Fills**: When you place a limit order, it might fill minutes or hours later
- **Partial Fills**: Orders might be partially filled over time
- **Fill Prices**: Market orders execute at the actual market price, not your estimate
- **Manual Trading**: Trades made directly in Alpaca won't appear without sync
- **Order Cancellations**: Orders might be cancelled or rejected by the market

## Synchronization Features

### 1. Order Status Updates

The sync process checks all pending orders and updates:
- **Filled Orders**: Changes status from "pending" to "open"
- **Fill Prices**: Updates with actual execution price
- **Partial Fills**: Updates quantity with actual filled amount
- **Cancelled Orders**: Marks as cancelled with reason

### 2. Position Price Updates

For all open positions, the sync updates:
- Current market price
- Floating P&L calculations
- Position values

### 3. Import Positions

Use "Import from Broker" to:
- Import positions opened outside the app
- Add manual trades from Alpaca
- Reconcile any missing positions

## How to Use

### Frontend (Automatic)

1. Navigate to the **Trades** page
2. Sync runs automatically every 30 seconds
3. See "Last sync" timestamp in the header
4. Click "Sync with Broker" for immediate sync

### Import Existing Positions

1. Click "Import from Broker" button
2. Confirm the import dialog
3. System will:
   - Fetch all positions from Alpaca
   - Compare with local database
   - Import any missing positions

### Background Sync Service (Optional)

For production environments, run the background sync service:

```bash
cd backend
python background_sync.py
```

This will:
- Sync all accounts every 30 seconds (configurable)
- Run independently of the web app
- Handle multiple accounts automatically

Configure sync interval in `.env`:
```
SYNC_INTERVAL=30  # seconds
```

## What Gets Synced

### From App to Alpaca
- New orders (happens immediately on execution)
- Order cancellations
- Position closures

### From Alpaca to App
- Order status changes
- Fill prices and quantities
- Position prices
- P&L calculations
- New positions (via import)

## Best Practices

1. **Regular Sync**: Keep the Trades page open for automatic updates
2. **After Manual Trading**: Click "Sync with Broker" after trading in Alpaca
3. **First Time Setup**: Use "Import from Broker" to import existing positions
4. **Production**: Run the background sync service for reliable updates

## Troubleshooting

### Orders Stay "Pending"
- Click "Sync with Broker" to force update
- Check if order was cancelled in Alpaca
- Verify market hours for the security

### Missing Positions
- Use "Import from Broker" to add them
- Check if position is in the correct account
- Verify account is active in settings

### Incorrect Prices
- Sync updates prices every 30 seconds
- Click "Update Price" on specific trades
- Check if market is open

## Technical Details

### Sync Endpoint
`GET /api/trades/sync` - Updates all pending trades and positions

### Import Endpoint  
`POST /api/trades/import-positions` - Imports missing positions

### Database Updates
- Order fills update `status`, `broker_fill_price`, `entry_price`
- Position sync updates `current_price`, `floating_pnl`
- Cancelled orders update `status`, `close_reason`

### Performance
- Sync is account-specific (only syncs active account)
- Batched updates for efficiency
- Non-blocking async operations 