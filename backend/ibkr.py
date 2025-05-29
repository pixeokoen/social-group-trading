from ib_insync import IB, Stock, Order, MarketOrder, LimitOrder, StopOrder
import asyncio
from typing import Optional, Dict, Any
import os
from dotenv import load_dotenv
import logging

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class IBKRClient:
    def __init__(self):
        self.ib = IB()
        self.host = os.getenv('IBKR_HOST', '127.0.0.1')
        self.port = int(os.getenv('IBKR_PORT', '7497'))  # 7497 for paper trading, 7496 for live
        self.client_id = int(os.getenv('IBKR_CLIENT_ID', '1'))
        self.connected = False
        
    async def connect(self):
        """Connect to IBKR TWS/Gateway"""
        try:
            await self.ib.connectAsync(self.host, self.port, clientId=self.client_id)
            self.connected = True
            logger.info(f"Connected to IBKR at {self.host}:{self.port}")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to IBKR: {e}")
            self.connected = False
            return False
    
    async def disconnect(self):
        """Disconnect from IBKR"""
        if self.connected:
            self.ib.disconnect()
            self.connected = False
            logger.info("Disconnected from IBKR")
    
    async def ensure_connected(self):
        """Ensure connection is active"""
        if not self.connected or not self.ib.isConnected():
            await self.connect()
    
    async def place_order(
        self,
        symbol: str,
        action: str,
        quantity: int,
        order_type: str = 'MKT',
        limit_price: Optional[float] = None,
        stop_price: Optional[float] = None,
        exchange: str = 'SMART',
        currency: str = 'USD'
    ) -> Optional[str]:
        """Place an order with IBKR"""
        try:
            await self.ensure_connected()
            
            # Create contract
            contract = Stock(symbol, exchange, currency)
            
            # Create order based on type
            if order_type == 'MKT':
                order = MarketOrder(action, quantity)
            elif order_type == 'LMT' and limit_price:
                order = LimitOrder(action, quantity, limit_price)
            elif order_type == 'STP' and stop_price:
                order = StopOrder(action, quantity, stop_price)
            else:
                raise ValueError(f"Invalid order type or missing price: {order_type}")
            
            # Place order
            trade = self.ib.placeOrder(contract, order)
            
            # Wait for order to be placed
            await asyncio.sleep(1)
            
            logger.info(f"Order placed: {trade.order.orderId} - {symbol} {action} {quantity}")
            return str(trade.order.orderId)
            
        except Exception as e:
            logger.error(f"Error placing order: {e}")
            return None
    
    async def get_positions(self) -> Dict[str, Any]:
        """Get current positions"""
        try:
            await self.ensure_connected()
            positions = self.ib.positions()
            
            result = {}
            for pos in positions:
                result[pos.contract.symbol] = {
                    'position': pos.position,
                    'avgCost': pos.avgCost,
                    'marketValue': pos.marketValue,
                    'unrealizedPNL': pos.unrealizedPNL
                }
            
            return result
            
        except Exception as e:
            logger.error(f"Error getting positions: {e}")
            return {}
    
    async def get_account_summary(self) -> Dict[str, Any]:
        """Get account summary"""
        try:
            await self.ensure_connected()
            account_values = self.ib.accountValues()
            
            summary = {}
            for av in account_values:
                if av.tag in ['NetLiquidation', 'TotalCashValue', 'BuyingPower', 'UnrealizedPnL']:
                    summary[av.tag] = float(av.value)
            
            return summary
            
        except Exception as e:
            logger.error(f"Error getting account summary: {e}")
            return {}
    
    async def cancel_order(self, order_id: str) -> bool:
        """Cancel an order"""
        try:
            await self.ensure_connected()
            
            # Find the order
            for trade in self.ib.openTrades():
                if str(trade.order.orderId) == order_id:
                    self.ib.cancelOrder(trade.order)
                    logger.info(f"Order cancelled: {order_id}")
                    return True
            
            logger.warning(f"Order not found: {order_id}")
            return False
            
        except Exception as e:
            logger.error(f"Error cancelling order: {e}")
            return False
    
    async def get_order_status(self, order_id: str) -> Optional[str]:
        """Get status of an order"""
        try:
            await self.ensure_connected()
            
            for trade in self.ib.trades():
                if str(trade.order.orderId) == order_id:
                    return trade.orderStatus.status
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting order status: {e}")
            return None
    
    async def get_market_data(self, symbol: str, exchange: str = 'SMART', currency: str = 'USD') -> Dict[str, Any]:
        """Get market data for a symbol"""
        try:
            await self.ensure_connected()
            
            contract = Stock(symbol, exchange, currency)
            ticker = self.ib.reqMktData(contract)
            
            # Wait for data
            await asyncio.sleep(2)
            
            return {
                'bid': ticker.bid,
                'ask': ticker.ask,
                'last': ticker.last,
                'volume': ticker.volume,
                'high': ticker.high,
                'low': ticker.low,
                'close': ticker.close
            }
            
        except Exception as e:
            logger.error(f"Error getting market data: {e}")
            return {}

# Singleton instance
ibkr_client = IBKRClient()

# Example usage
if __name__ == "__main__":
    async def test():
        client = IBKRClient()
        
        # Connect
        if await client.connect():
            # Get account summary
            summary = await client.get_account_summary()
            print(f"Account Summary: {summary}")
            
            # Get positions
            positions = await client.get_positions()
            print(f"Positions: {positions}")
            
            # Get market data
            market_data = await client.get_market_data("AAPL")
            print(f"AAPL Market Data: {market_data}")
            
            # Disconnect
            await client.disconnect()
    
    asyncio.run(test()) 