#!/bin/bash

# Quick Start Script for Trade Signal Filter & IBKR Execution App
# For Mac/Linux systems

echo "=== Trade Signal Filter & IBKR Execution App - Quick Start ==="
echo ""

# Check prerequisites
echo "Checking prerequisites..."

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.8 or higher."
    exit 1
else
    echo "✅ Python 3 found: $(python3 --version)"
fi

# Check Node
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is not installed. Please install Node.js 16 or higher."
    exit 1
else
    echo "✅ Node.js found: $(node --version)"
fi

# Check PostgreSQL
if ! command -v psql &> /dev/null; then
    echo "❌ PostgreSQL is not installed. Please install PostgreSQL."
    exit 1
else
    echo "✅ PostgreSQL found"
fi

echo ""
echo "=== Setting up Backend ==="

# Navigate to backend
cd backend || exit

# Create virtual environment
if [ ! -d "venv" ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "Installing Python dependencies..."
pip install -r requirements.txt

# Check for .env file
if [ ! -f ".env" ]; then
    echo ""
    echo "⚠️  No .env file found in backend directory!"
    echo "Please create backend/.env with your configuration."
    echo "See ENV_VARIABLES.md for details."
    echo ""
    read -p "Press Enter to continue after creating .env file..."
fi

# Return to root
cd ..

echo ""
echo "=== Setting up Frontend ==="

# Navigate to frontend
cd frontend || exit

# Install dependencies
echo "Installing Node dependencies..."
npm install

# Check for .env.local file
if [ ! -f ".env.local" ]; then
    echo ""
    echo "Creating .env.local with default values..."
    echo "VITE_API_URL=http://localhost:8000" > .env.local
fi

# Return to root
cd ..

echo ""
echo "=== Database Setup ==="
echo ""
echo "Have you already set up the PostgreSQL database? (y/n)"
read -r response

if [[ "$response" =~ ^([nN][oO]|[nN])$ ]]; then
    echo ""
    echo "Please run these commands in PostgreSQL:"
    echo ""
    echo "  CREATE DATABASE social_trading;"
    echo "  CREATE USER social_trading_user WITH PASSWORD 'your_password';"
    echo "  GRANT ALL PRIVILEGES ON DATABASE social_trading TO social_trading_user;"
    echo ""
    echo "Then update your backend/.env file with the database credentials."
    echo ""
    read -p "Press Enter when database is ready..."
fi

echo ""
echo "=== Initializing Database and Creating User ==="
echo ""
echo "Running setup script..."
python3 setup.py

echo ""
echo "=== Setup Complete! ==="
echo ""
echo "To start the application:"
echo ""
echo "1. Backend (in one terminal):"
echo "   cd backend"
echo "   source venv/bin/activate"
echo "   python main.py"
echo ""
echo "2. Frontend (in another terminal):"
echo "   cd frontend"
echo "   npm run dev"
echo ""
echo "Then open http://localhost:5173 in your browser."
echo ""
echo "Happy trading! 🚀" 