from agno.tools import Toolkit
from broker.interface import BrokerService
from core.indicators import compute_technical_analysis
from typing import List, Dict, Any
import json
import pandas as pd

class BrokerToolkit(Toolkit):
    """Toolkit that provides agents access to broker data and operations"""
    
    def __init__(self, broker: BrokerService, **kwargs):
        self.broker = broker
        
        tools = [
            self.get_quotes,
            self.get_market_depth,
            self.get_historical_data,
            self.get_option_chain,
            self.place_order,
            self.get_positions,
            self.calculate_margin,
            self.get_technical_analysis  # New: returns computed indicators
        ]
        
        super().__init__(name="broker_toolkit", tools=tools, **kwargs)
    
    async def get_quotes(self, symbols: List[str]) -> str:
        """
        Get market quotes for multiple symbols.
        
        Args:
            symbols (List[str]): List of symbols in format "NSE:SBIN-EQ"
            
        Returns:
            str: Quote data in CSV-like format for easy LLM reading
        """
        result = await self.broker.get_quotes(symbols)
        
        # Convert to simple CSV-like format
        lines = ["SYMBOL,LTP,CHANGE,CHANGE_PCT,VOLUME,OPEN,HIGH,LOW,PREV_CLOSE"]
        for quote in result.get("d", []):
            v = quote.get("v", {})
            lines.append(f"{quote['n']},{v.get('lp')},{v.get('ch')},{v.get('chp')},{v.get('volume')},{v.get('open_price')},{v.get('high_price')},{v.get('low_price')},{v.get('prev_close_price')}")
        
        return "\n".join(lines)
    
    async def get_market_depth(self, symbol: str) -> str:
        """
        Get order book depth for a symbol.
        
        Args:
            symbol (str): Symbol in format "NSE:SBIN-EQ"
            
        Returns:
            str: Bid/Ask data in readable format
        """
        result = await self.broker.get_market_depth(symbol, ohlcv_flag=1)
        data = result.get("d", {}).get(symbol, {})
        
        # Format bids and asks
        lines = [f"MARKET DEPTH FOR {symbol}"]
        lines.append(f"LTP: {data.get('ltp')}, VOLUME: {data.get('v')}")
        lines.append("\nBIDS (Price,Volume,Orders):")
        for bid in data.get("bids", []):
            lines.append(f"  {bid['price']}, {bid['volume']}, {bid['ord']}")
        lines.append("\nASKS (Price,Volume,Orders):")
        for ask in data.get("ask", []):
            lines.append(f"  {ask['price']}, {ask['volume']}, {ask['ord']}")
        
        return "\n".join(lines)
    
    async def get_historical_data(
        self, 
        symbol: str, 
        resolution: str = "D",
        days: int = 100
    ) -> str:
        """
        Get historical candle data.
        
        Args:
            symbol (str): Symbol in format "NSE:SBIN-EQ"
            resolution (str): Candle resolution (D, 60, 15, etc.)
            days (int): Number of days of history
            
        Returns:
            str: Historical OHLCV candles in CSV format
        """
        from datetime import datetime, timedelta
        range_to = datetime.now().strftime("%Y-%m-%d")
        range_from = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
        
        result = await self.broker.get_history(
            symbol=symbol,
            resolution=resolution,
            date_format=1,
            range_from=range_from,
            range_to=range_to
        )
        
        # Convert to CSV format
        lines = ["TIMESTAMP,OPEN,HIGH,LOW,CLOSE,VOLUME"]
        for candle in result.get("candles", []):
            lines.append(f"{candle[0]},{candle[1]},{candle[2]},{candle[3]},{candle[4]},{candle[5]}")
        
        return "\n".join(lines)
    
    async def get_option_chain(self, symbol: str, strike_count: int = 5) -> str:
        """
        Get option chain for a symbol.
        
        Args:
            symbol (str): Underlying symbol
            strike_count (int): Number of strikes above/below ATM
            
        Returns:
            str: Option chain in CSV format
        """
        result = await self.broker.get_option_chain(symbol, strike_count)
        
        lines = ["SYMBOL,STRIKE,TYPE,LTP,OI,VOLUME"]
        for option in result.get("data", {}).get("optionsChain", []):
            lines.append(f"{option['symbol']},{option['strike_price']},{option['option_type']},{option['ltp']},{option['oi']},{option['volume']}")
        
        return "\n".join(lines)
    
    async def place_order(self, symbol: str, qty: int, side: int, order_type: int = 2, limit_price: float = 0.0) -> str:
        """
        Place an order.
        
        Args:
            symbol (str): Symbol to trade
            qty (int): Quantity
            side (int): 1 for BUY, -1 for SELL
            order_type (int): 1=Limit, 2=Market, 3=Stop, 4=StopLimit
            limit_price (float): Limit price (required for type 1,4)
            
        Returns:
            str: Order confirmation
        """
        order_data = {
            "symbol": symbol,
            "qty": qty,
            "side": side,
            "type": order_type,
            "limitPrice": limit_price,
            "productType": "INTRADAY"
        }
        result = await self.broker.place_order(order_data)
        
        if result.get("s") == "ok":
            return f"ORDER PLACED: ID={result['id']}, SYMBOL={symbol}, QTY={qty}, SIDE={'BUY' if side==1 else 'SELL'}"
        return f"ORDER FAILED: {result.get('message')}"
    
    async def get_positions(self) -> str:
        """
        Get all open positions.
        
        Returns:
            str: List of positions in CSV format
        """
        result = await self.broker.get_positions()
        
        positions = result.get("netPositions", [])
        if not positions:
            return "NO OPEN POSITIONS"
        
        lines = ["SYMBOL,QTY,AVG_PRICE,SIDE,PNL"]
        for pos in positions:
            lines.append(f"{pos.get('symbol')},{pos.get('netQty')},{pos.get('netAvg')},{pos.get('side')},{pos.get('realized_profit', 0)}")
        
        return "\n".join(lines)
    
    async def calculate_margin(self, orders_data: str) -> str:
        """
        Calculate margin requirement for orders.
        
        Args:
            orders_data (str): Orders in format "symbol,qty,side;symbol,qty,side"
            
        Returns:
            str: Margin requirements
        """
        # Parse simple format
        orders = []
        for order_str in orders_data.split(";"):
            parts = order_str.split(",")
            if len(parts) >= 3:
                orders.append({
                    "symbol": parts[0],
                    "qty": int(parts[1]),
                    "side": int(parts[2]),
                    "type": 2,
                    "limitPrice": 0.0,
                    "productType": "INTRADAY"
                })
        
        result = await self.broker.calculate_multi_order_margin(orders)
        data = result.get("data", {})
        
        return f"MARGIN_REQUIRED: {data.get('margin_total')}, MARGIN_AVAILABLE: {data.get('margin_avail')}, MARGIN_AFTER: {data.get('margin_new_order')}"