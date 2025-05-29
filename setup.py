#!/usr/bin/env python
"""
Initial setup script for Trade Signal Filter & IBKR Execution App
"""
import os
import sys
import getpass
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent / "backend"))

from db import init_db, test_connection
from auth import create_user

def main():
    print("=== Trade Signal Filter & IBKR Execution App Setup ===\n")
    
    # Check database connection
    print("Testing database connection...")
    if not test_connection():
        print("\nERROR: Could not connect to database.")
        print("Please ensure PostgreSQL is running and .env is configured correctly.")
        return 1
    
    # Initialize database
    print("\nInitializing database tables...")
    try:
        init_db()
        print("Database initialized successfully!")
    except Exception as e:
        print(f"ERROR initializing database: {e}")
        return 1
    
    # Create initial user
    print("\n=== Create Initial User ===")
    print("This user will be able to log in and manage signals/trades.\n")
    
    username = input("Username: ").strip()
    email = input("Email: ").strip()
    password = getpass.getpass("Password: ")
    password_confirm = getpass.getpass("Confirm Password: ")
    
    if password != password_confirm:
        print("ERROR: Passwords do not match!")
        return 1
    
    if not username or not email or not password:
        print("ERROR: All fields are required!")
        return 1
    
    # Create user
    try:
        user = create_user(username, email, password)
        if user:
            print(f"\nUser '{username}' created successfully!")
        else:
            print("ERROR: Failed to create user. User might already exist.")
            return 1
    except Exception as e:
        print(f"ERROR creating user: {e}")
        return 1
    
    print("\n=== Setup Complete! ===")
    print("\nNext steps:")
    print("1. Configure WHAPI webhook URL in your WHAPI dashboard")
    print("2. Ensure IBKR TWS/Gateway is running")
    print("3. Start the backend: cd backend && python main.py")
    print("4. Start the frontend: cd frontend && npm run dev")
    print("5. Login with the user you just created")
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 