"""
Test script to debug sync endpoint issues
"""
import asyncio
from alpaca_client import AlpacaClient

async def test_sync():
    """Test the sync functionality"""
    print("=== Testing Alpaca Sync Functionality ===\n")
    
    # Test with paper account
    print("Testing PAPER account...")
    try:
        client = AlpacaClient(
            api_key="PKRDDPSPWVFAM2SF8TU1",
            secret_key="lzRqAagogxdfMUOU6BuRlsbSKlEBOT9fgMuFOmIc",
            paper=True
        )
        
        # Test getting orders
        print("Getting orders...")
        orders = await client.get_orders(status='all', limit=10)
        print(f"✓ Found {len(orders)} orders")
        
        # Test getting positions
        print("Getting positions...")
        positions = await client.get_positions()
        print(f"✓ Found {len(positions)} positions")
        
        # Test getting account info
        print("Getting account info...")
        account_info = await client.get_account_info()
        print(f"✓ Account info retrieved: Buying Power = ${account_info.get('buying_power', 0):,.2f}")
        
    except Exception as e:
        print(f"✗ ERROR: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_sync()) 