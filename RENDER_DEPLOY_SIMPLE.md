# Deploy to Render in 5 Minutes

## The Simple Truth

You only need **ONE service** on Render. The trade sync is built into the main app.

## Step-by-Step

### 1. Push to GitHub

```bash
git add .
git commit -m "Ready for deployment"
git push
```

### 2. Create Render Account

Go to [render.com](https://render.com) and sign up (free).

### 3. Create Database

1. New → PostgreSQL
2. Name: `social-trading-db`
3. Plan: Starter ($7/month)
4. Create Database

### 4. Create Web Service

1. New → Web Service
2. Connect your GitHub repo
3. Settings:
   - Name: `social-trading-api`
   - Runtime: Python
   - Build Command: `pip install -r backend/requirements.txt`
   - Start Command: `cd backend && python main.py`
   - Plan: Free ($0/month)

### 5. Add Environment Variables

In the web service settings, add:

```
SECRET_KEY=<click generate>
ALPACA_API_KEY=your_alpaca_key
ALPACA_API_SECRET=your_alpaca_secret
OPENAI_API_KEY=your_openai_key (optional)
WHAPI_WEBHOOK_SECRET=your_webhook_secret (optional)
```

The `DATABASE_URL` is added automatically when you connect the database.

### 6. Connect Database

1. In web service settings
2. Environment → Add Database
3. Select your `social-trading-db`
4. Save

### 7. Deploy!

Click "Manual Deploy" → "Deploy latest commit"

## That's It! 

Your app is now live with:
- ✅ Automatic trade sync every 30 seconds
- ✅ Manual sync button for instant updates
- ✅ No complex multi-service setup
- ✅ Total cost: $7/month (just the database)

## What Happens Behind the Scenes

When Render starts your app:
1. FastAPI web server starts
2. Background sync task starts automatically
3. Every 30 seconds, it checks and updates trades
4. No extra configuration needed!

## Monitoring

Check your Render logs to see:
```
Starting background trade sync...
INFO:     Application startup complete.
Auto-sync: Trade AAPL filled at $150.25
```

## Frontend Deployment

For the Vue frontend, either:
1. Deploy on Render Static Site (free)
2. Use Netlify/Vercel (easier for SPAs)
3. Update the API URL in frontend `.env`

## Questions?

- Is the sync running? **Yes**, if the API is running
- Do I need background workers? **No**, it's built-in
- What if I need real-time? Use the manual sync button
- Cost? Just $7/month for the database

Simple, right? That's the point! 🎉 