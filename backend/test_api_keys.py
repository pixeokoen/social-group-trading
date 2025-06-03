"""
Test script to debug Alpaca API key issues
"""
import os
import sys
from dotenv import load_dotenv
from alpaca.trading.client import TradingClient
from alpaca.common.exceptions import APIError

# Load environment variables
load_dotenv()

def test_api_keys_direct():
    """Test API keys directly without database"""
    print("=== Testing Alpaca API Keys (Direct Input) ===\n")
    
    # Get account type
    account_type = input("Enter account type (paper/live): ").strip().lower()
    if account_type not in ['paper', 'live']:
        print("Invalid account type. Must be 'paper' or 'live'")
        return
    
    # Get API credentials
    api_key = input("Enter your API Key: ").strip()
    api_secret = input("Enter your API Secret: ").strip()
    
    if not api_key or not api_secret:
        print("API credentials cannot be empty")
        return
    
    # Mask credentials for display
    masked_key = f"{api_key[:4]}...{api_key[-4:]}" if len(api_key) > 8 else "***"
    print(f"\nTesting {account_type} account with API Key: {masked_key}")
    
    # Test the credentials
    try:
        # Create client
        client = TradingClient(
            api_key=api_key,
            secret_key=api_secret,
            paper=(account_type == 'paper')
        )
        
        # Try to get account info
        account_info = client.get_account()
        
        print(f"\n✓ SUCCESS: Connected to {account_type} account")
        print(f"  Account Number: {account_info.account_number}")
        print(f"  Buying Power: ${float(account_info.buying_power):,.2f}")
        print(f"  Cash: ${float(account_info.cash):,.2f}")
        print(f"  Portfolio Value: ${float(account_info.portfolio_value):,.2f}")
        print(f"  Pattern Day Trader: {account_info.pattern_day_trader}")
        print(f"  Trading Blocked: {account_info.trading_blocked}")
        print(f"  Account Blocked: {account_info.account_blocked}")
        
    except APIError as e:
        print(f"\n✗ API ERROR: {str(e)}")
        if "forbidden" in str(e).lower():
            print("\n  → This usually means:")
            print("    1. The API key/secret is incorrect")
            print("    2. The API key is for the wrong environment (paper vs live)")
            print("    3. The API key doesn't have the required permissions")
            print("\n  → Make sure you're using:")
            if account_type == 'paper':
                print("    - Paper trading keys from: https://app.alpaca.markets/paper/dashboard/overview")
            else:
                print("    - Live trading keys from: https://app.alpaca.markets/live/dashboard/overview")
                
    except Exception as e:
        print(f"\n✗ ERROR: {type(e).__name__}: {str(e)}")

    print("\n\n=== Next Steps ===")
    print("1. If the test succeeded, update your account in the database with these credentials")
    print("2. If it failed, regenerate your API keys in the Alpaca dashboard")
    print("3. Make sure the API keys have full trading permissions enabled")

if __name__ == "__main__":
    test_api_keys_direct() 