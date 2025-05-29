# Deployment Guide - Trade Signal Filter & IBKR Execution App

## Table of Contents
1. [Local Deployment](#local-deployment)
2. [Render Deployment](#render-deployment)
3. [Post-Deployment Configuration](#post-deployment-configuration)
4. [Troubleshooting](#troubleshooting)

---

## Local Deployment

### Prerequisites
- Python 3.8+ installed
- Node.js 16+ and npm installed
- PostgreSQL installed and running locally
- Git installed
- IBKR TWS or IB Gateway installed

### Step 1: PostgreSQL Setup

1. **Install PostgreSQL** (if not already installed):
   - Windows: Download from https://www.postgresql.org/download/windows/
   - Mac: `brew install postgresql`
   - Linux: `sudo apt-get install postgresql postgresql-contrib`

2. **Start PostgreSQL**:
   - Windows: Should start automatically, or use Services app
   - Mac: `brew services start postgresql`
   - Linux: `sudo systemctl start postgresql`

3. **Create Database and User**:
   ```bash
   # Login to PostgreSQL
   psql -U postgres

   # Create database
   CREATE DATABASE social_trading;

   # Create user (optional, but recommended)
   CREATE USER social_trading_user WITH PASSWORD 'your_secure_password';
   GRANT ALL PRIVILEGES ON DATABASE social_trading TO social_trading_user;

   # Exit
   \q
   ```

### Step 2: Backend Setup

1. **Create GitHub repository and push your code**:
   ```bash
   # First, create a new repository on GitHub (github.com/new)
   # Then, in your local project directory:
   
   git init
   git add .
   git commit -m "Initial commit"
   git branch -M main
   git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git
   git push -u origin main
   ```

2. **Navigate to backend directory**:
   ```bash
   cd backend
   ```

3. **Create backend `.env` file**:
   ```bash
   # Copy the template file
   cp env.template .env
   
   # Or on Windows:
   copy env.template .env
   ```
   
   Then edit `.env` and update:
   - `DB_PASSWORD` - Your PostgreSQL password
   - `SECRET_KEY` - Generate with: `python -c "import secrets; print(secrets.token_hex(32))"`
   - `WHAPI_WEBHOOK_SECRET` - Any secret string for local testing

4. **Set up Python virtual environment**:
   ```bash
   # Windows
   python -m venv venv
   venv\Scripts\activate

   # Mac/Linux
   python -m venv venv
   source venv/bin/activate
   ```

5. **Install Python dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

6. **Initialize database and create user**:
   ```bash
   cd ..  # Go back to project root
   python setup.py
   ```
   Follow the prompts to create your first user account.

7. **Start the backend server**:
   ```bash
   cd backend
   python main.py
   ```
   The API will be running at `http://localhost:8000`

### Step 3: Frontend Setup

1. **Open a new terminal** and navigate to frontend:
   ```bash
   cd frontend
   ```

2. **Install Node dependencies**:
   ```bash
   npm install
   ```

3. **Create frontend `.env.local` file**:
   ```bash
   # Copy the template file
   cp env.template .env.local
   
   # Or on Windows:
   copy env.template .env.local
   ```
   
   For local development, the default value `VITE_API_URL=http://localhost:8000` should work.

4. **Start the frontend development server**:
   ```bash
   npm run dev
   ```
   The app will be running at `http://localhost:5173`

### Step 4: Configure IBKR (Optional for Testing)

1. **Open TWS or IB Gateway**
2. **Configure API Settings**:
   - File → Global Configuration → API → Settings
   - Enable "Enable ActiveX and Socket Clients"
   - Set "Socket port" to 7497 (paper) or 7496 (live)
   - Add "127.0.0.1" to "Trusted IP Addresses"

### Step 5: Test the Application

1. Open browser to `http://localhost:5173`
2. Login with the user you created during setup
3. Try creating a manual signal
4. Test the signal approval workflow

---

## Render Deployment

### Step 1: Prepare Your Code

1. **Ensure all code is committed**:
   ```bash
   git add .
   git commit -m "Prepare for deployment"
   ```

2. **Push to GitHub**:
   ```bash
   git push origin main
   ```

### Step 2: Create PostgreSQL Database on Render

1. **Login to Render** (https://dashboard.render.com)

2. **Create New PostgreSQL**:
   - Click "New +"
   - Select "PostgreSQL"
   - Fill in:
     - Name: `social-trading-db`
     - Database: `social_trading` (optional)
     - User: `social_trading_user` (optional)
     - Region: Oregon (US West)
     - PostgreSQL Version: 15
     - Plan: Free
   - Click "Create Database"

3. **Save Database Credentials**:
   - Once created, go to the database dashboard
   - Copy the "Internal Database URL" for later use

### Step 3: Deploy Backend API

1. **Create New Web Service**:
   - Click "New +"
   - Select "Web Service"
   - Connect your GitHub account if not already connected
   - Select your repository
   - Fill in:
     - Name: `social-trading-api`
     - Region: Oregon (US West)
     - Branch: main
     - Runtime: Python 3
     - Build Command: `cd backend && pip install -r requirements.txt`
     - Start Command: `cd backend && uvicorn main:app --host 0.0.0.0 --port $PORT`
     - Plan: Free

2. **Add Environment Variables**:
   Click "Advanced" and add these environment variables:

   | Key | Value |
   |-----|-------|
   | `SECRET_KEY` | (Generate with: `openssl rand -hex 32`) |
   | `WHAPI_WEBHOOK_SECRET` | (Your WHAPI webhook secret) |
   | `IBKR_HOST` | (Your IBKR host IP) |
   | `IBKR_PORT` | 7497 (or your IBKR port) |
   | `IBKR_CLIENT_ID` | 1 |
   | `FRONTEND_URL` | (Leave empty for now, will update later) |

3. **Connect Database**:
   - In the same environment variables section
   - Click "Add Environment Variable"
   - Choose "Add from database"
   - Select your `social-trading-db`
   - This will automatically add DB_* variables

4. **Click "Create Web Service"**

5. **Wait for deployment** and copy the service URL (e.g., `https://social-trading-api.onrender.com`)

### Step 4: Initialize Database

1. **Access Render Shell**:
   - Go to your backend service dashboard
   - Click "Shell" tab
   - Run:
     ```bash
     cd backend
     python
     ```

2. **Initialize database**:
   ```python
   from db import init_db
   init_db()
   exit()
   ```

3. **Create first user**:
   ```bash
   cd ..
   python setup.py
   ```

### Step 5: Deploy Frontend

1. **Create New Static Site**:
   - Click "New +"
   - Select "Static Site"
   - Connect to your repository
   - Fill in:
     - Name: `social-trading-frontend`
     - Branch: main
     - Build Command: `cd frontend && npm install && npm run build`
     - Publish Directory: `frontend/dist`

2. **Add Environment Variables**:
   | Key | Value |
   |-----|-------|
   | `VITE_API_URL` | Your backend URL (e.g., `https://social-trading-api.onrender.com`) |

3. **Click "Create Static Site"**

4. **Wait for deployment** and copy the frontend URL

### Step 6: Update Backend CORS

1. **Go back to your backend service**
2. **Update environment variable**:
   - `FRONTEND_URL` = Your frontend URL (e.g., `https://social-trading-frontend.onrender.com`)
3. **Manual Deploy** to apply changes

---

## Post-Deployment Configuration

### Configure WHAPI Webhook

1. **Login to WHAPI Dashboard**
2. **Set Webhook URL**:
   ```
   https://your-backend-url.onrender.com/api/webhook/whapi
   ```
3. **Copy Webhook Secret** and update in Render environment variables

### Configure IBKR Connection

1. **Ensure IBKR TWS/Gateway is accessible**:
   - If running on local machine, you'll need to expose it (use ngrok or similar)
   - If using a VPS, ensure firewall allows connection

2. **Update IBKR environment variables** in Render with correct host/port

### Test the Deployment

1. **Visit your frontend URL**
2. **Login** with the user you created
3. **Test signal creation** and execution
4. **Send a test WhatsApp message** to verify webhook

---

## Troubleshooting

### Common Issues

1. **Database Connection Failed**:
   - Check if PostgreSQL is running
   - Verify credentials in `.env`
   - Check firewall settings

2. **CORS Errors**:
   - Ensure `FRONTEND_URL` is set correctly in backend
   - Check browser console for specific errors

3. **IBKR Connection Failed**:
   - Verify TWS/Gateway is running
   - Check API settings in TWS
   - Ensure correct host/port in environment variables

4. **Webhook Not Working**:
   - Verify webhook URL is correct
   - Check webhook secret matches
   - Look at Render logs for errors

### Viewing Logs

- **Local**: Check terminal output
- **Render**: Go to service dashboard → "Logs" tab

### Health Checks

- Backend health: `https://your-backend-url.onrender.com/health`
- API docs: `https://your-backend-url.onrender.com/docs`

---

## Security Checklist

- [ ] Strong database password
- [ ] Secure SECRET_KEY (never reuse or commit)
- [ ] HTTPS enabled (automatic on Render)
- [ ] WHAPI webhook secret configured
- [ ] IBKR credentials secure
- [ ] No sensitive data in git repository
- [ ] Regular dependency updates

---

## Maintenance

### Updating the Application

1. **Make changes locally and test**
2. **Commit and push**:
   ```bash
   git add .
   git commit -m "Update description"
   git push origin main
   ```
3. **Render will auto-deploy** (or manually trigger)

### Database Backups

- Render Free tier: Manual backups only
- Production: Consider upgrading for automatic backups

### Monitoring

- Set up alerts in Render dashboard
- Monitor logs regularly
- Track API usage and performance 