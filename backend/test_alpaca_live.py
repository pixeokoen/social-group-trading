"""
Test script to verify Alpaca live account credentials
"""
import os
import sys
from dotenv import load_dotenv
from alpaca.trading.client import TradingClient

# Load environment variables
load_dotenv()

def test_alpaca_live():
    # First, let's check what credentials we have
    print("=== Testing Alpaca Live Account ===")
    
    # You'll need to manually set these or get them from your database
    # For security, we won't print the actual keys
    live_api_key = input("Enter your LIVE API Key: ").strip()
    live_api_secret = input("Enter your LIVE API Secret: ").strip()
    
    if not live_api_key or not live_api_secret:
        print("ERROR: API credentials not provided")
        return
    
    print(f"\nAPI Key length: {len(live_api_key)}")
    print(f"API Secret length: {len(live_api_secret)}")
    
    # Test 1: Try with paper=False (live endpoint)
    print("\n--- Test 1: Live endpoint (paper=False) ---")
    try:
        client = TradingClient(
            api_key=live_api_key,
            secret_key=live_api_secret,
            paper=False  # This should use https://api.alpaca.markets
        )
        account = client.get_account()
        print(f"SUCCESS! Account number: {account.account_number}")
        print(f"Buying power: ${account.buying_power}")
        print(f"Cash: ${account.cash}")
        print(f"Portfolio value: ${account.portfolio_value}")
    except Exception as e:
        print(f"FAILED: {type(e).__name__}: {e}")
        if hasattr(e, '__dict__'):
            print(f"Exception details: {e.__dict__}")
    
    # Test 2: Try with paper=True (paper endpoint) - should fail with live credentials
    print("\n--- Test 2: Paper endpoint with live credentials (paper=True) ---")
    try:
        client = TradingClient(
            api_key=live_api_key,
            secret_key=live_api_secret,
            paper=True  # This should use https://paper-api.alpaca.markets
        )
        account = client.get_account()
        print(f"UNEXPECTED SUCCESS! This shouldn't work with live credentials")
        print(f"Account number: {account.account_number}")
    except Exception as e:
        print(f"Expected failure: {type(e).__name__}: {e}")
    
    # Test 3: Try with explicit URL override
    print("\n--- Test 3: Explicit live URL ---")
    try:
        client = TradingClient(
            api_key=live_api_key,
            secret_key=live_api_secret,
            paper=False,
            url_override="https://api.alpaca.markets"
        )
        account = client.get_account()
        print(f"SUCCESS! Account number: {account.account_number}")
    except Exception as e:
        print(f"FAILED: {type(e).__name__}: {e}")

if __name__ == "__main__":
    test_alpaca_live() 