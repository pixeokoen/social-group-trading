# How to Run the Application

## Quick Start

### 1. Backend Server
```bash
python -m venv venv
.\venv\Scripts\activate
cd backend
python main.py
```
The backend will start on http://localhost:8000

### 2. Frontend Development Server
```bash
cd C:\_Dev\social-group-trading\frontend
npm run dev
```
The frontend will start on http://localhost:5173

## Alternative Commands

### Using PowerShell
```powershell
# Backend
Set-Location C:\_Dev\social-group-trading\backend
python main.py

# Frontend (new terminal)
Set-Location C:\_Dev\social-group-trading\frontend
npm run dev
```

### Using Python Virtual Environment
```bash
# Activate virtual environment first
C:\_Dev\social-group-trading\.venv\Scripts\activate

# Then run backend
cd backend
python main.py
```

## Common Issues

### "npm is not recognized"
- Make sure you're in the `frontend` directory
- Ensure Node.js is installed

### "python: can't open file"
- Make sure you're in the `backend` directory
- The file is `backend/main.py`, not in the root

### Port Already in Use
- Backend uses port 8000
- Frontend uses port 5173
- Kill existing processes or use different ports

## What You Should See

1. Backend console will show:
   - "Starting background trade sync..."
   - "INFO: Uvicorn running on http://0.0.0.0:8000"

2. Frontend console will show:
   - "VITE ready in X ms"
   - "Local: http://localhost:5173/"

3. Open http://localhost:5173 in your browser

## Dashboard Features

Your dashboard now shows:
- Total Trades (with open/pending count)
- Win Rate (based on closed trades)
- Total P&L (realized gains/losses)
- **Floating P&L** (unrealized gains/losses) ← NEW!
- Pending Signals (awaiting approval)

The dashboard auto-syncs every 30 seconds! 