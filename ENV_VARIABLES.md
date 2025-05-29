# Environment Variables Reference

This document lists all environment variables used in the Trade Signal Filter & Alpaca Execution App.

## Backend Environment Variables

### Database Configuration
| Variable | Description | Example | Required |
|----------|-------------|---------|----------|
| `DB_HOST` | PostgreSQL host address | `localhost` or `dpg-xxxxx.render.com` | Yes |
| `DB_PORT` | PostgreSQL port | `5432` | Yes |
| `DB_NAME` | Database name | `social_trading` | Yes |
| `DB_USER` | Database username | `postgres` | Yes |
| `DB_PASSWORD` | Database password | `your_secure_password` | Yes |

### Alpaca Configuration (Optional - for default account)
| Variable | Description | Example | Required |
|----------|-------------|---------|----------|
| `ALPACA_API_KEY` | Alpaca API key (for testing) | `PKXXXXXXXXXXXXXXXX` | No |
| `ALPACA_API_SECRET` | Alpaca API secret | `XXXXXXXXXXXXXXXXXXXXXXXXXXXX` | No |

### Security Configuration
| Variable | Description | Example | Required |
|----------|-------------|---------|----------|
| `SECRET_KEY` | JWT signing key | 32-byte hex string | Yes |
| `WHAPI_WEBHOOK_SECRET` | WHAPI webhook verification | From WHAPI dashboard | Yes |

### AI Configuration
| Variable | Description | Example | Required |
|----------|-------------|---------|----------|
| `OPENAI_API_KEY` | OpenAI API key for message analysis | `sk-...` | No |

### CORS Configuration
| Variable | Description | Example | Required |
|----------|-------------|---------|----------|
| `FRONTEND_URL` | Frontend URL for CORS | `http://localhost:5173` | Yes |

## Frontend Environment Variables

### API Configuration
| Variable | Description | Example | Required |
|----------|-------------|---------|----------|
| `VITE_API_URL` | Backend API URL | `http://localhost:8000` | Yes |

## Local Development (.env files)

### Backend `.env` Example
```env
# Database Configuration
DB_HOST=localhost
DB_PORT=5432
DB_NAME=social_trading
DB_USER=postgres
DB_PASSWORD=yourpassword

# Alpaca Configuration (optional - accounts are managed in the app)
ALPACA_API_KEY=your-alpaca-api-key
ALPACA_API_SECRET=your-alpaca-secret

# Security
SECRET_KEY=your-32-byte-hex-secret-key-here
WHAPI_WEBHOOK_SECRET=your-whapi-secret

# AI Configuration
OPENAI_API_KEY=sk-your-openai-api-key

# Frontend URL (for CORS)
FRONTEND_URL=http://localhost:5173
```

### Frontend `.env.local` Example
```env
VITE_API_URL=http://localhost:8000
```

## Production (Render) Environment Variables

### Backend Service
- All backend variables listed above, but with production values
- Database variables are automatically added when you connect the PostgreSQL database
- `FRONTEND_URL` should be your Render frontend URL

### Frontend Static Site
- `VITE_API_URL` should be your Render backend URL (e.g., `https://social-trading-api.onrender.com`)

## Generating Secure Values

### SECRET_KEY
Generate a secure secret key using one of these methods:

**Python:**
```python
import secrets
print(secrets.token_hex(32))
```

**Command line (Linux/Mac):**
```bash
openssl rand -hex 32
```

**Online:** Use a secure random generator (not recommended for production)

### WHAPI_WEBHOOK_SECRET
This is provided by WHAPI when you configure your webhook endpoint in their dashboard.

## Important Notes

1. **Never commit `.env` files** to version control
2. **Use different SECRET_KEY values** for development and production
3. **Database credentials** should be strong and unique
4. **Alpaca credentials** are now managed per-account in the application settings
5. **Rotate secrets regularly** in production environments

## Multi-Account Trading

The app now supports multiple trading accounts:
- Each user can have multiple Alpaca accounts (paper and live)
- Accounts are configured in the Settings page with their own API credentials
- Switch between accounts using the dropdown in the header
- All data is filtered by the active account

### Getting Alpaca API Keys

1. **Paper Trading (Free)**: 
   - Sign up at https://app.alpaca.markets/signup
   - Go to the paper trading dashboard
   - Generate API keys from the API Keys section

2. **Live Trading**: 
   - Complete account verification
   - Fund your account
   - Generate live API keys (keep these secure!)

## Troubleshooting

### Common Issues

1. **"Database connection failed"**
   - Check `DB_*` variables match your PostgreSQL setup
   - Ensure PostgreSQL is running
   - Verify network connectivity

2. **"CORS error" in browser**
   - Ensure `FRONTEND_URL` in backend matches your frontend URL exactly
   - Include protocol (http:// or https://)

3. **"Alpaca connection failed"**
   - Verify API keys are correct
   - Check if using paper keys for paper account or live keys for live account
   - Ensure your Alpaca account is active

4. **"Invalid webhook signature"**
   - Ensure `WHAPI_WEBHOOK_SECRET` matches exactly what's in WHAPI dashboard
   - No extra spaces or quotes

## Signal Source Types

The application tracks where signals come from:

- **`manual_entry`** - Direct signal creation via the form (no message analysis)
- **`message_paste`** - Message pasted manually and analyzed by AI
- **`whatsapp`** - Message received from WhatsApp webhook and analyzed by AI
- **`telegram`** - (Future) Message from Telegram
- **`discord`** - (Future) Message from Discord

Both `message_paste` and social media sources (WhatsApp, Telegram, etc.) use AI analysis to extract signals from messages.

### Database Configuration

**For Local Development:**
```env
DB_HOST=localhost
DB_PORT=5432
DB_NAME=social_trading
DB_USER=your_db_user
DB_PASSWORD=your_db_password
```

**For Render Deployment:**
```env
# Render provides this automatically when you connect a database
DATABASE_URL=postgresql://user:password@host:port/dbname
```

The app automatically detects and uses `DATABASE_URL` if available (for Render, Heroku, etc.), otherwise falls back to individual DB_ variables. 