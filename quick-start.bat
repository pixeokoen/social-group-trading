@echo off
REM Quick Start Script for Trade Signal Filter & IBKR Execution App
REM For Windows systems

echo === Trade Signal Filter ^& IBKR Execution App - Quick Start ===
echo.

REM Check prerequisites
echo Checking prerequisites...

REM Check Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo X Python 3 is not installed. Please install Python 3.8 or higher.
    pause
    exit /b 1
) else (
    echo OK Python 3 found
)

REM Check Node
node --version >nul 2>&1
if %errorlevel% neq 0 (
    echo X Node.js is not installed. Please install Node.js 16 or higher.
    pause
    exit /b 1
) else (
    echo OK Node.js found
)

REM Check PostgreSQL
psql --version >nul 2>&1
if %errorlevel% neq 0 (
    echo X PostgreSQL is not installed. Please install PostgreSQL.
    echo   Note: psql might not be in PATH. If PostgreSQL is installed, continue.
)

echo.
echo === Setting up Backend ===

REM Navigate to backend
cd backend

REM Create virtual environment
if not exist "venv" (
    echo Creating Python virtual environment...
    python -m venv venv
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Install dependencies
echo Installing Python dependencies...
pip install -r requirements.txt

REM Check for .env file
if not exist ".env" (
    echo.
    echo WARNING: No .env file found in backend directory!
    echo Please create backend\.env with your configuration.
    echo See ENV_VARIABLES.md for details.
    echo.
    pause
)

REM Return to root
cd ..

echo.
echo === Setting up Frontend ===

REM Navigate to frontend
cd frontend

REM Install dependencies
echo Installing Node dependencies...
call npm install

REM Check for .env.local file
if not exist ".env.local" (
    echo.
    echo Creating .env.local with default values...
    echo VITE_API_URL=http://localhost:8000 > .env.local
)

REM Return to root
cd ..

echo.
echo === Database Setup ===
echo.
set /p response="Have you already set up the PostgreSQL database? (y/n): "

if /i "%response%"=="n" (
    echo.
    echo Please run these commands in PostgreSQL:
    echo.
    echo   CREATE DATABASE social_trading;
    echo   CREATE USER social_trading_user WITH PASSWORD 'your_password';
    echo   GRANT ALL PRIVILEGES ON DATABASE social_trading TO social_trading_user;
    echo.
    echo Then update your backend\.env file with the database credentials.
    echo.
    pause
)

echo.
echo === Initializing Database and Creating User ===
echo.
echo Running setup script...
python setup.py

echo.
echo === Setup Complete! ===
echo.
echo To start the application:
echo.
echo 1. Backend ^(in one terminal^):
echo    cd backend
echo    venv\Scripts\activate
echo    python main.py
echo.
echo 2. Frontend ^(in another terminal^):
echo    cd frontend
echo    npm run dev
echo.
echo Then open http://localhost:5173 in your browser.
echo.
echo Happy trading! 🚀
pause 