# How Trade Sync Works (The Simple Way)

## No Extra Services Required! 

Everything is built into the main application. Here's what happens:

```
┌─────────────────────────────────────┐
│         python main.py              │
│                                     │
│  ┌─────────────────────────────┐   │
│  │   FastAPI Web Server        │   │
│  │   - Handles API requests    │   │
│  │   - Serves the backend      │   │
│  └─────────────────────────────┘   │
│                                     │
│  ┌─────────────────────────────┐   │
│  │   Background Sync Task      │   │
│  │   - Runs every 30 seconds   │   │
│  │   - Updates trade statuses  │   │
│  │   - No extra setup needed   │   │
│  └─────────────────────────────┘   │
└─────────────────────────────────────┘
```

## Running Locally

```bash
# That's literally it!
cd backend
python main.py
```

When you see this in the console:
```
Starting background trade sync...
INFO:     Started server process [12345]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

The sync is already running! You'll see updates like:
```
Auto-sync: Trade AAPL filled at $150.25
Auto-sync: Trade TSLA filled at $195.50
```

## On Render

Just deploy as a single web service. The sync starts automatically:

```yaml
services:
  - type: web
    name: social-trading-api
    env: python
    buildCommand: "pip install -r requirements.txt"
    startCommand: "python main.py"
```

## What Gets Synced?

Every 30 seconds, the app:
1. Checks all pending trades
2. Gets status from Alpaca
3. Updates filled orders with actual prices
4. Updates the database
5. Frontend sees the changes

## Manual Sync Still Available

The "Sync with Broker" button still works for instant updates when needed.

## Why This is Better

1. **Simpler**: One service instead of multiple
2. **Cheaper**: No extra Render workers needed
3. **Reliable**: If the API is running, sync is running
4. **Easy Deploy**: Works anywhere Python works

## The Trade-Off

- Updates every 30 seconds instead of instant
- For 99% of traders, this is perfectly fine
- If you need faster, just click the manual sync button

That's it! No complex setup, no extra services, just run and trade. 