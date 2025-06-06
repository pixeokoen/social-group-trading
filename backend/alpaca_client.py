"""
Alpaca Trading Client
Handles all interactions with Alpaca Markets API
"""
import os
from typing import Dict, Optional, List, Any
from decimal import Decimal
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest, LimitOrderRequest, StopOrderRequest, StopLimitOrderRequest, GetOrdersRequest
from alpaca.trading.enums import OrderSide, TimeInForce, OrderStatus
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockLatestQuoteRequest, StockLatestTradeRequest
from alpaca.common.exceptions import APIError
from dotenv import load_dotenv

load_dotenv()

class AlpacaClient:
    def __init__(self, api_key: str = None, secret_key: str = None, base_url: str = None, paper: bool = True):
        """
        Initialize Alpaca client
        
        Args:
            api_key: Alpaca API key
            secret_key: Alpaca API secret
            base_url: Override base URL (optional)
            paper: Use paper trading (default True)
        """
        self.api_key = api_key or os.getenv("ALPACA_API_KEY")
        self.secret_key = secret_key or os.getenv("ALPACA_API_SECRET")
        
        if not self.api_key or not self.secret_key:
            raise ValueError("Alpaca API credentials not provided")
        
        # Log initialization details (mask sensitive data)
        masked_key = f"{self.api_key[:4]}...{self.api_key[-4:]}" if len(self.api_key) > 8 else "***"
        print(f"[AlpacaClient] Initializing - Paper: {paper}, Base URL Override: {base_url}, API Key: {masked_key}")
        
        # Initialize trading client
        self.trading_client = TradingClient(
            api_key=self.api_key,
            secret_key=self.secret_key,
            paper=paper,
            url_override=base_url
        )
        
        # Initialize data client for market data
        self.data_client = StockHistoricalDataClient(
            api_key=self.api_key,
            secret_key=self.secret_key,
            url_override=base_url
        )
        
        self.paper = paper
    
    async def get_account_info(self) -> Dict[str, Any]:
        """Get account information"""
        try:
            print(f"[AlpacaClient] Getting account info - Paper: {self.paper}")
            
            # Log the actual endpoint being used
            if hasattr(self.trading_client, '_base_url'):
                print(f"[AlpacaClient] Using base URL: {self.trading_client._base_url}")
            
            account = self.trading_client.get_account()
            
            # Log successful response for debugging
            print(f"[AlpacaClient] Successfully retrieved account info")
            
            return {
                "buying_power": float(account.buying_power),
                "cash": float(account.cash),
                "portfolio_value": float(account.portfolio_value),
                "account_blocked": account.account_blocked,
                "trading_blocked": account.trading_blocked,
                "transfers_blocked": getattr(account, 'transfers_blocked', False),
                "trade_suspended_by_user": getattr(account, 'trade_suspended_by_user', False),
                "currency": account.currency,
                "pattern_day_trader": account.pattern_day_trader,
                "equity": float(account.equity),
                "last_equity": float(account.last_equity),
                "multiplier": float(account.multiplier),
                "initial_margin": float(account.initial_margin),
                "maintenance_margin": float(account.maintenance_margin),
                "daytrade_count": account.daytrade_count
            }
        except APIError as e:
            print(f"[AlpacaClient] Alpaca API Error: {str(e)}")
            # Check if it's a 403 error
            if "forbidden" in str(e).lower():
                print(f"[AlpacaClient] 403 Forbidden - Check if API key has correct permissions for {self.paper and 'paper' or 'live'} trading")
            raise
        except Exception as e:
            print(f"[AlpacaClient] Unexpected error getting account info: {type(e).__name__}: {str(e)}")
            raise
    
    async def place_order(self, symbol: str, action: str, quantity: float, 
                         order_type: str = "market", limit_price: float = None,
                         stop_price: float = None, time_in_force: str = "day") -> str:
        """Place an order with Alpaca"""
        try:
            # Convert action to OrderSide enum
            side = OrderSide.BUY if action.upper() == "BUY" else OrderSide.SELL
            
            # Convert time_in_force to enum
            tif = TimeInForce.DAY
            if time_in_force.upper() == "GTC":
                tif = TimeInForce.GTC
            elif time_in_force.upper() == "IOC":
                tif = TimeInForce.IOC
            elif time_in_force.upper() == "FOK":
                tif = TimeInForce.FOK
            
            # Check if this is a fractional quantity
            is_fractional = quantity != int(quantity)
            
            print(f"Placing order: {symbol} {action} {quantity} shares, type={order_type}, fractional={is_fractional}")
            
            # Create order request based on type
            if order_type.lower() == "market":
                if is_fractional:
                    # For fractional orders, we can use notional (dollar amount) or qty
                    order_request = MarketOrderRequest(
                        symbol=symbol,
                        qty=quantity,  # Alpaca accepts fractional quantities
                        side=side,
                        time_in_force=tif
                    )
                else:
                    order_request = MarketOrderRequest(
                        symbol=symbol,
                        qty=int(quantity),
                        side=side,
                        time_in_force=tif
                    )
            elif order_type.lower() == "limit":
                # Fractional limit orders are supported by Alpaca
                order_request = LimitOrderRequest(
                    symbol=symbol,
                    qty=quantity if is_fractional else int(quantity),
                    side=side,
                    time_in_force=tif,
                    limit_price=limit_price
                )
            elif order_type.lower() == "stop":
                # Stop order - becomes market order when stop price is reached
                order_request = StopOrderRequest(
                    symbol=symbol,
                    qty=quantity if is_fractional else int(quantity),
                    side=side,
                    time_in_force=tif,
                    stop_price=stop_price
                )
            elif order_type.lower() == "stop_limit":
                # Stop-limit order - becomes limit order when stop price is reached
                order_request = StopLimitOrderRequest(
                    symbol=symbol,
                    qty=quantity if is_fractional else int(quantity),
                    side=side,
                    time_in_force=tif,
                    stop_price=stop_price,
                    limit_price=limit_price
                )
            else:
                raise ValueError(f"Unsupported order type: {order_type}")
            
            # Submit order
            order = self.trading_client.submit_order(order_request)
            order_id = str(order.id)  # Convert UUID to string
            print(f"Order placed successfully: {order_id}")
            return order_id
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            print(f"Error placing order: {e}")
            raise  # Re-raise to get better error messages
    
    async def get_order_status(self, order_id: str) -> Optional[Dict[str, Any]]:
        """Get status of a specific order"""
        try:
            order = self.trading_client.get_order_by_id(order_id)
            return {
                "id": str(order.id),
                "status": order.status.value,
                "symbol": order.symbol,
                "qty": order.qty,
                "filled_qty": order.filled_qty,
                "side": order.side.value,
                "order_type": order.order_type.value,
                "limit_price": float(order.limit_price) if order.limit_price else None,
                "filled_avg_price": float(order.filled_avg_price) if order.filled_avg_price else None,
                "submitted_at": order.submitted_at,
                "filled_at": order.filled_at,
                "canceled_at": order.canceled_at
            }
        except Exception as e:
            print(f"Error getting order status: {e}")
            return None
    
    async def get_orders(self, status: str = 'all', limit: int = 100) -> List[Dict[str, Any]]:
        """Get orders from Alpaca"""
        try:
            # Use string status values as required by Alpaca API
            request = GetOrdersRequest(
                status=status,  # 'all', 'open', or 'closed'
                limit=limit
            )
            orders = self.trading_client.get_orders(filter=request)
            return [
                {
                    "id": str(order.id),
                    "status": order.status.value,
                    "symbol": order.symbol,
                    "qty": float(order.qty) if order.qty else 0,
                    "filled_qty": float(order.filled_qty) if order.filled_qty else 0,
                    "side": order.side.value,
                    "order_type": order.order_type.value,
                    "limit_price": float(order.limit_price) if order.limit_price else None,
                    "filled_avg_price": float(order.filled_avg_price) if order.filled_avg_price else None,
                    "created_at": str(order.created_at) if order.created_at else None,
                    "updated_at": str(order.updated_at) if order.updated_at else None,
                    "submitted_at": str(order.submitted_at) if order.submitted_at else None,
                    "filled_at": str(order.filled_at) if order.filled_at else None,
                    "canceled_at": str(order.canceled_at) if order.canceled_at else None
                }
                for order in orders
            ]
        except Exception as e:
            print(f"Error getting orders: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    async def cancel_order(self, order_id: str) -> bool:
        """Cancel an order"""
        try:
            self.trading_client.cancel_order_by_id(order_id)
            return True
        except Exception as e:
            print(f"Error canceling order: {e}")
            return False
    
    async def get_positions(self) -> List[Dict[str, Any]]:
        """Get all open positions"""
        try:
            positions = self.trading_client.get_all_positions()
            return [
                {
                    "symbol": pos.symbol,
                    "qty": int(pos.qty),
                    "avg_entry_price": float(pos.avg_entry_price),
                    "market_value": float(pos.market_value),
                    "cost_basis": float(pos.cost_basis),
                    "unrealized_pl": float(pos.unrealized_pl),
                    "unrealized_plpc": float(pos.unrealized_plpc),
                    "current_price": float(pos.current_price) if hasattr(pos, 'current_price') else None,
                    "side": pos.side.value
                }
                for pos in positions
            ]
        except Exception as e:
            print(f"Error getting positions: {e}")
            return []
    
    async def close_position(self, symbol: str) -> bool:
        """Close a position"""
        try:
            self.trading_client.close_position(symbol)
            return True
        except Exception as e:
            print(f"Error closing position: {e}")
            return False
    
    async def get_market_data(self, symbol: str) -> dict:
        """Get current market data for a symbol"""
        try:
            # Get quote using the data client
            request = StockLatestQuoteRequest(symbol_or_symbols=symbol)
            quotes = self.data_client.get_stock_latest_quote(request)
            
            # Get trades for last price
            trade_request = StockLatestTradeRequest(symbol_or_symbols=symbol)
            trades = self.data_client.get_stock_latest_trade(trade_request)
            
            # Try to get asset information to check fractional trading
            fractionable = False
            try:
                asset = self.trading_client.get_asset(symbol)
                fractionable = getattr(asset, 'fractionable', False)
            except Exception:
                # If we can't get asset info, assume not fractionable
                pass
            
            quote = quotes.get(symbol)
            trade = trades.get(symbol)
            
            return {
                'symbol': symbol,
                'last': float(trade.price) if trade else None,
                'bid': float(quote.bid_price) if quote else None,
                'ask': float(quote.ask_price) if quote else None,
                'bid_size': int(quote.bid_size) if quote else None,
                'ask_size': int(quote.ask_size) if quote else None,
                'timestamp': str(trade.timestamp) if trade else None,
                'fractionable': fractionable
            }
        except Exception as e:
            print(f"Error getting market data for {symbol}: {e}")
            return {}
    
    async def get_current_prices(self, symbols: List[str]) -> Dict[str, float]:
        """Get current prices for multiple symbols"""
        prices = {}
        for symbol in symbols:
            try:
                market_data = await self.get_market_data(symbol)
                if market_data:
                    # Try 'last' price first (most recent trade)
                    current_price = market_data.get('last')
                    if current_price and current_price > 0:
                        prices[symbol] = float(current_price)
                    else:
                        # Fallback to bid/ask midpoint
                        bid = market_data.get('bid')
                        ask = market_data.get('ask')
                        if bid and ask and bid > 0 and ask > 0:
                            prices[symbol] = float((bid + ask) / 2)
            except Exception as e:
                print(f"Error getting price for {symbol}: {e}")
                continue
        return prices
    
    async def get_latest_price(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get latest price for a single symbol (for compatibility)"""
        try:
            market_data = await self.get_market_data(symbol)
            if market_data:
                price = market_data.get('last')
                if price and price > 0:
                    return {'price': float(price)}
        except Exception as e:
            print(f"Error getting latest price for {symbol}: {e}")
        return None

    async def get_account_summary(self) -> Dict[str, Any]:
        """Get account summary including buying power"""
        account_info = await self.get_account_info()
        if account_info:
            return {
                "BuyingPower": account_info.get("buying_power", 0),
                "TotalCashValue": account_info.get("cash", 0),
                "GrossPositionValue": account_info.get("portfolio_value", 0) - account_info.get("cash", 0),
                "NetLiquidation": account_info.get("portfolio_value", 0)
            }
        return {"BuyingPower": 0}

# Singleton instance (will be replaced with account-specific instances)
alpaca_client = None 