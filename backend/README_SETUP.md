# Backend Setup

## Environment Variables

Create a `.env` file in the backend directory with the following:

```bash
# Database Configuration
DB_HOST=localhost
DB_PORT=5432
DB_NAME=social_trading
DB_USER=postgres
DB_PASSWORD=yourpassword

# Security
SECRET_KEY=your-32-byte-hex-secret-key-here
WHAPI_WEBHOOK_SECRET=your-whapi-secret

# AI Configuration (optional)
OPENAI_API_KEY=sk-your-openai-api-key

# Frontend URL (for CORS)
FRONTEND_URL=http://localhost:5173
```

## Important Notes

1. **Alpaca API Keys**: These are now managed per-account in the application. You don't need to add them to the `.env` file anymore.

2. **Generate SECRET_KEY**: Run this command to generate a secure key:
   ```python
   python -c "import secrets; print(secrets.token_hex(32))"
   ```

3. **First Run**: The application will automatically create the database schema when you run it.

## Running the Backend

```bash
cd backend
python -m venv venv
venv\Scripts\activate  # On Windows
# or
source venv/bin/activate  # On Mac/Linux

pip install -r requirements.txt
python main.py
```

The backend will be available at http://localhost:8000 