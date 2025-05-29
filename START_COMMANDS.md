# Quick Start Commands

## Starting the Application

### Backend (Terminal 1)
```bash
cd backend
python main.py
```

### Frontend (Terminal 2)
```bash
cd frontend
npm run dev
```

## Common Mistakes

❌ **Wrong:**
```bash
# In root directory
npm run dev  # Error: npm not found
python main.py  # Error: file not found
```

✅ **Correct:**
```bash
# Must cd into subdirectories first!
cd frontend && npm run dev
cd backend && python main.py
```

## One-Line Commands

### Windows PowerShell
```powershell
# Backend
cd backend; python main.py

# Frontend (new terminal)
cd frontend; npm run dev
```

### Windows Command Prompt
```cmd
# Backend
cd backend && python main.py

# Frontend (new terminal)
cd frontend && npm run dev
```

## Verify Everything is Running

1. Backend: http://localhost:8000 (should show API docs)
2. Frontend: http://localhost:5173 (should show login page)
3. Check console for "Starting background trade sync..."

## Note

The trade sync runs automatically when you start the backend. No extra services needed! 