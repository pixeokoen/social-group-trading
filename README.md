# Trade Signal Filter & IBKR Execution App

A web application that receives WhatsApp group messages via WHAPI, filters out trade signals (U.S. stock buy/sell signals), and executes confirmed trades via Interactive Brokers (IBKR) API.

## 🚀 Quick Start

### For detailed deployment instructions, see:
- 📖 **[DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)** - Complete step-by-step deployment guide
- 🔧 **[ENV_VARIABLES.md](ENV_VARIABLES.md)** - Environment variables reference
- 🔄 **[HOW_SYNC_WORKS.md](HOW_SYNC_WORKS.md)** - Simple explanation of trade sync

### Quick setup scripts:
- **Windows**: Run `quick-start.bat`
- **Mac/Linux**: Run `chmod +x quick-start.sh && ./quick-start.sh`

## Features

- **WhatsApp Integration**: Automatically receives and parses trading signals from WhatsApp groups via WHAPI webhook
- **Signal Filtering**: Intelligent parsing of trade signals from WhatsApp messages with noise filtering
- **Signal Management**: Approve/reject pending signals before execution
- **Automated Trade Execution**: Execute approved trades directly through IBKR integration
- **Trade Management**: Track all trades with real-time floating P&L and close positions
- **Analytics Dashboard**: Comprehensive trading statistics and performance metrics
- **Secure Authentication**: JWT-based authentication system
- **Mobile Responsive**: Works seamlessly on Windows desktop and iPhone
- **Advanced signal parsing with AI analysis**
- **Multi-broker support (currently Alpaca, IBKR coming soon)**
- **WhatsApp integration for signal reception**
- **Real-time trade synchronization with broker**
- **Multi-account management**

## Tech Stack

### Backend
- **FastAPI**: Modern Python web framework
- **PostgreSQL**: Database for storing messages, signals, and trades
- **ib_insync**: IBKR API integration
- **Signal Parser**: Custom regex-based parser for WhatsApp messages
- **JWT**: Authentication with python-jose

### Frontend
- **Vue 3**: Progressive JavaScript framework
- **Tailwind CSS**: Utility-first CSS framework
- **Vite**: Fast build tool
- **TypeScript**: Type-safe development
- **Pinia**: State management
- **Axios**: HTTP client with centralized configuration

## Prerequisites

- Python 3.8+
- Node.js 16+ and npm
- PostgreSQL database
- Interactive Brokers TWS or IB Gateway
- WHAPI account for WhatsApp integration

## Quick Local Setup

1. **Initial setup**:
   ```bash
   # If you haven't created a GitHub repo yet:
   # 1. Go to github.com/new and create a new repository
   # 2. Then in your local project:
   git init
   git add .
   git commit -m "Initial commit"
   git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git
   git push -u origin main
   
   # Run quick start script
   # Windows: quick-start.bat
   # Mac/Linux: ./quick-start.sh
   ```

2. **Configure environment**:
   ```bash
   # Backend
   cd backend
   cp env.template .env  # Windows: copy env.template .env
   # Edit .env with your values
   
   # Frontend
   cd ../frontend
   cp env.template .env.local  # Windows: copy env.template .env.local
   ```

3. **Start services**:
   ```bash
   # Terminal 1 - Backend
   cd backend
   python main.py
   
   # Terminal 2 - Frontend
   cd frontend
   npm run dev
   ```

4. **Access application**: http://localhost:5173

## Deployment

See [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) for detailed instructions on:
- Local development setup
- Render deployment with PostgreSQL
- WHAPI webhook configuration
- IBKR connection setup
- Troubleshooting

## Usage

### Setting Up WhatsApp Integration

1. Configure WHAPI with your WhatsApp Business account
2. Set webhook URL pointing to your backend
3. Messages from configured groups will be automatically processed

### Signal Processing Flow

1. **Automatic Detection**: WhatsApp messages are received via webhook
2. **Signal Parsing**: Messages are parsed for trading signals (BUY/SELL SYMBOL @ PRICE)
3. **Pending Signals**: Detected signals appear in pending state
4. **Manual Approval**: Review and approve/reject signals
5. **Trade Execution**: Approved signals can be executed with one click
6. **Trade Management**: Monitor open trades and close when needed

### Supported Signal Formats

The parser recognizes various formats:
- `BUY AAPL @ 150, SL: 145, TP: 160`
- `TSLA: SELL at 220`
- `🚀 MSFT BUY 380 🎯 400 ⛔ 370`
- `Entry: GOOGL 140, Stop: 135, Target: 150`
- `LONG NVDA 500`

## Project Structure

```
social-group-trading/
├── backend/
│   ├── main.py           # FastAPI application
│   ├── models.py         # Pydantic models
│   ├── db.py            # Database connection
│   ├── auth.py          # Authentication
│   ├── ibkr.py          # IBKR integration
│   ├── signal_parser.py # WhatsApp signal parser
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/  # Vue components
│   │   ├── views/       # Page components
│   │   ├── stores/      # Pinia stores
│   │   └── plugins/     # Axios config
│   └── package.json
├── render.yaml          # Render deployment config
├── setup.py            # Database setup script
└── README.md
```

## API Documentation

Once the backend is running, access the interactive API documentation:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Security Considerations

- Use strong passwords and secure `.env` files
- Never commit `.env` files to version control
- Use HTTPS in production
- Webhook endpoint is protected by signature verification
- Regularly update dependencies
- Be cautious with IBKR credentials

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License.

## Support

For issues and questions:
- Check [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) troubleshooting section
- Review [ENV_VARIABLES.md](ENV_VARIABLES.md) for configuration issues
- Open an issue on GitHub 

### 2. Run the Backend

```bash
cd backend
python main.py
```

The API will be available at `http://localhost:8000`

**Note**: Trade sync runs automatically! No extra services needed. The app syncs with Alpaca every 30 seconds in the background.

## 📊 Trade Synchronization

The system includes **automatic trade synchronization** built right into the main app:

1. **Automatic Background Sync**
   - Updates every 30 seconds automatically
   - No extra services or setup required
   - Runs whenever the API is running

2. **Manual Sync Button**
   - Click "Sync with Broker" for immediate updates
   - Import existing positions with "Import from Broker"

3. **Visual Indicators**
   - "Last sync" timestamp shows sync status
   - Trade updates highlight briefly when changed

### Why Keep It Simple?

- ✅ **One service** = Easy deployment on Render, Heroku, etc.
- ✅ **30-second updates** = Good enough for most trading
- ✅ **Manual sync available** = Instant updates when needed
- ✅ **Lower costs** = No extra background workers required

For advanced real-time options, see [REALTIME_SYNC_GUIDE.md](REALTIME_SYNC_GUIDE.md) (not recommended for most users). 