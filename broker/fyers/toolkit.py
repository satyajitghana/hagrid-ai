"""
Fyers Toolkit for Agno Agents.

Provides direct access to Fyers API functionality as agent tools.
Optimized for LLM consumption with CSV-formatted outputs.

Features:
- Real-time market data (quotes, depth, option chains)
- Historical OHLCV data for technical analysis
- Position, order, and portfolio management
- Technical indicators computation
- Built-in request caching with configurable TTL
"""

from typing import List, Dict, Any, Optional, Callable
from agno.tools import Toolkit
from broker.fyers.client import FyersClient
from broker.fyers.models.config import FyersConfig
from datetime import datetime, timedelta
from pathlib import Path
import hashlib
import json
import time
import pandas as pd


class FyersCache:
    """
    Request cache for Fyers API with TTL-based expiration.

    Supports both memory and file-based caching for persistence across sessions.

    TTL Defaults (in seconds):
    - quotes: 30s (real-time data, short TTL)
    - depth: 30s (order book, short TTL)
    - historical: 3600s (1 hour, stable data)
    - options: 120s (2 minutes, moderate refresh)
    - positions: 10s (user data, very short TTL)
    - orders: 10s (user data, very short TTL)
    - holdings: 300s (5 minutes, semi-stable)
    - funds: 60s (1 minute)
    - profile: 86400s (24 hours, rarely changes)
    - indicators: 3600s (1 hour, derived from historical)
    - correlation: 3600s (1 hour, derived from historical)
    """

    # Default TTL values in seconds
    DEFAULT_TTL = {
        "quotes": 30,
        "depth": 30,
        "historical": 3600,
        "options": 120,
        "positions": 10,
        "orders": 10,
        "holdings": 300,
        "funds": 60,
        "profile": 86400,
        "indicators": 3600,
        "correlation": 3600,
    }

    CACHE_DIR = Path(".cache/fyers")

    def __init__(
        self,
        enabled: bool = True,
        persist_to_file: bool = True,
        custom_ttl: Optional[Dict[str, int]] = None
    ):
        """
        Initialize FyersCache.

        Args:
            enabled: Whether caching is enabled
            persist_to_file: Whether to persist cache to disk
            custom_ttl: Custom TTL values to override defaults
        """
        self.enabled = enabled
        self.persist_to_file = persist_to_file
        self.ttl = {**self.DEFAULT_TTL, **(custom_ttl or {})}

        # In-memory cache: {cache_key: {"data": ..., "expires_at": timestamp}}
        self._memory_cache: Dict[str, Dict[str, Any]] = {}

        if persist_to_file:
            self.CACHE_DIR.mkdir(parents=True, exist_ok=True)

    def _make_key(self, cache_type: str, *args, **kwargs) -> str:
        """Generate a unique cache key from type and arguments."""
        key_data = f"{cache_type}:{args}:{sorted(kwargs.items())}"
        return hashlib.md5(key_data.encode()).hexdigest()

    def _get_cache_path(self, cache_type: str) -> Path:
        """Get file path for a cache type."""
        return self.CACHE_DIR / f"{cache_type}_cache.json"

    def _load_file_cache(self, cache_type: str) -> Dict[str, Any]:
        """Load cache from file."""
        if not self.persist_to_file:
            return {}

        cache_path = self._get_cache_path(cache_type)
        if not cache_path.exists():
            return {}

        try:
            with open(cache_path, "r") as f:
                return json.load(f)
        except Exception:
            return {}

    def _save_file_cache(self, cache_type: str, data: Dict[str, Any]) -> None:
        """Save cache to file."""
        if not self.persist_to_file:
            return

        cache_path = self._get_cache_path(cache_type)
        try:
            with open(cache_path, "w") as f:
                json.dump(data, f)
        except Exception:
            pass

    def get(self, cache_type: str, *args, **kwargs) -> Optional[str]:
        """
        Get cached data if available and not expired.

        Args:
            cache_type: Type of data (quotes, historical, etc.)
            *args, **kwargs: Arguments used to generate cache key

        Returns:
            Cached data string or None if not found/expired
        """
        if not self.enabled:
            return None

        key = self._make_key(cache_type, *args, **kwargs)
        now = time.time()

        # Check memory cache first
        if key in self._memory_cache:
            entry = self._memory_cache[key]
            if entry["expires_at"] > now:
                return entry["data"]
            else:
                del self._memory_cache[key]

        # Check file cache
        if self.persist_to_file:
            file_cache = self._load_file_cache(cache_type)
            if key in file_cache:
                entry = file_cache[key]
                if entry["expires_at"] > now:
                    # Restore to memory cache
                    self._memory_cache[key] = entry
                    return entry["data"]

        return None

    def set(self, cache_type: str, data: str, *args, **kwargs) -> None:
        """
        Store data in cache.

        Args:
            cache_type: Type of data (quotes, historical, etc.)
            data: Data string to cache
            *args, **kwargs: Arguments used to generate cache key
        """
        if not self.enabled:
            return

        key = self._make_key(cache_type, *args, **kwargs)
        ttl = self.ttl.get(cache_type, 60)
        expires_at = time.time() + ttl

        entry = {"data": data, "expires_at": expires_at}

        # Store in memory
        self._memory_cache[key] = entry

        # Persist to file
        if self.persist_to_file:
            file_cache = self._load_file_cache(cache_type)
            file_cache[key] = entry
            # Clean expired entries while saving
            now = time.time()
            file_cache = {k: v for k, v in file_cache.items() if v["expires_at"] > now}
            self._save_file_cache(cache_type, file_cache)

    def invalidate(self, cache_type: Optional[str] = None) -> None:
        """
        Invalidate cache entries.

        Args:
            cache_type: Type to invalidate, or None for all
        """
        if cache_type:
            # Invalidate specific type from memory
            keys_to_remove = [k for k in self._memory_cache.keys() if k.startswith(cache_type)]
            for k in keys_to_remove:
                del self._memory_cache[k]
            # Remove file cache
            if self.persist_to_file:
                cache_path = self._get_cache_path(cache_type)
                if cache_path.exists():
                    cache_path.unlink()
        else:
            # Clear all
            self._memory_cache.clear()
            if self.persist_to_file:
                for cache_file in self.CACHE_DIR.glob("*_cache.json"):
                    cache_file.unlink()

    def stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        now = time.time()
        memory_entries = len(self._memory_cache)
        valid_entries = sum(1 for e in self._memory_cache.values() if e["expires_at"] > now)

        file_entries = 0
        if self.persist_to_file:
            for cache_file in self.CACHE_DIR.glob("*_cache.json"):
                try:
                    with open(cache_file, "r") as f:
                        data = json.load(f)
                        file_entries += len(data)
                except Exception:
                    pass

        return {
            "enabled": self.enabled,
            "persist_to_file": self.persist_to_file,
            "memory_entries": memory_entries,
            "valid_memory_entries": valid_entries,
            "file_entries": file_entries,
            "ttl_config": self.ttl,
        }


class FyersToolkit(Toolkit):
    """
    Toolkit that provides agents access to Fyers broker data and operations.

    This toolkit wraps the FyersClient directly without an adapter layer,
    providing optimized access to broker functionality.

    Usage:
        ```python
        from broker.fyers.toolkit import FyersToolkit
        from broker.fyers import FyersConfig, FyersClient

        config = FyersConfig(
            client_id="YOUR_CLIENT_ID",
            secret_key="YOUR_SECRET",
            token_file_path="token.json"
        )
        client = FyersClient(config)

        # Full toolkit
        toolkit = FyersToolkit(client)

        # Options agent - only options-related tools
        options_toolkit = FyersToolkit(client, include_tools=[
            "get_option_chain", "get_quotes"
        ])

        # Position agent - only position-related tools
        position_toolkit = FyersToolkit(client, include_tools=[
            "get_positions", "get_quotes", "get_market_depth", "get_historical_data"
        ])
        ```
    """

    # Tool categories for easy selection
    MARKET_DATA_TOOLS = [
        "get_quotes",
        "get_market_depth",
        "get_historical_data",
        "get_option_chain",
        "get_option_greeks",
        "get_market_status",
    ]

    POSITION_TOOLS = [
        "get_positions",
        "exit_position",
        "convert_position",
    ]

    ORDER_TOOLS = [
        "place_order",
        "modify_order",
        "cancel_order",
        "get_orders",
    ]

    PORTFOLIO_TOOLS = [
        "get_holdings",
        "get_funds",
        "get_profile",
    ]

    MARGIN_TOOLS = [
        "calculate_margin",
    ]

    ANALYSIS_TOOLS = [
        "get_technical_indicators",
        "get_correlation_matrix",
    ]

    def __init__(
        self,
        client: FyersClient,
        include_tools: Optional[List[str]] = None,
        exclude_tools: Optional[List[str]] = None,
        cache_enabled: bool = True,
        cache_persist: bool = True,
        cache_ttl: Optional[Dict[str, int]] = None,
        **kwargs
    ):
        """
        Initialize FyersToolkit.

        Args:
            client: Authenticated FyersClient instance
            include_tools: List of tool names to include (if None, includes all)
            exclude_tools: List of tool names to exclude
            cache_enabled: Enable request caching (default: True)
            cache_persist: Persist cache to disk (default: True)
            cache_ttl: Custom TTL values in seconds, e.g., {"quotes": 60, "historical": 7200}
            **kwargs: Additional arguments for Toolkit base class

        Example:
            ```python
            # Default caching
            toolkit = FyersToolkit(client)

            # Disable caching
            toolkit = FyersToolkit(client, cache_enabled=False)

            # Custom TTL (longer historical cache)
            toolkit = FyersToolkit(client, cache_ttl={"historical": 7200})
            ```
        """
        self.client = client
        self.cache = FyersCache(
            enabled=cache_enabled,
            persist_to_file=cache_persist,
            custom_ttl=cache_ttl
        )

        # Define all available tools
        all_tools = {
            # Market Data
            "get_quotes": self.get_quotes,
            "get_market_depth": self.get_market_depth,
            "get_historical_data": self.get_historical_data,
            "get_option_chain": self.get_option_chain,
            "get_option_greeks": self.get_option_greeks,
            "get_market_status": self.get_market_status,
            # Positions
            "get_positions": self.get_positions,
            "exit_position": self.exit_position,
            # Orders
            "place_order": self.place_order,
            "get_orders": self.get_orders,
            # Portfolio
            "get_holdings": self.get_holdings,
            "get_funds": self.get_funds,
            "get_profile": self.get_profile,
            # Margin
            "calculate_margin": self.calculate_margin,
            # Analysis
            "get_technical_indicators": self.get_technical_indicators,
            "get_correlation_matrix": self.get_correlation_matrix,
        }

        # Filter tools based on include/exclude
        if include_tools:
            tools = [all_tools[name] for name in include_tools if name in all_tools]
        else:
            tools = list(all_tools.values())

        if exclude_tools:
            exclude_set = set(exclude_tools)
            tools = [t for t in tools if t.__name__ not in exclude_set]

        instructions = """Use these tools for Fyers broker operations:
- Real-time quotes and market depth
- Historical OHLCV data for technical analysis
- Option chains with Greeks (IV, Delta, Gamma, Theta, Vega)
- Positions, orders, holdings, and funds
- Technical indicators (SMA, EMA, RSI, MACD, Bollinger Bands)
- Correlation matrix for portfolio analysis

Symbol format: "NSE:SYMBOL-EQ" for equities, "NSE:NIFTY50-INDEX" for indices.
Examples: "NSE:SBIN-EQ", "NSE:TCS-EQ", "NSE:NIFTY50-INDEX".

For order operations: side=1 for BUY, side=-1 for SELL."""

        super().__init__(name="fyers_toolkit", tools=tools, instructions=instructions, **kwargs)

    # ==================== Market Data Tools ====================

    async def get_quotes(self, symbols: List[str]) -> str:
        """
        Get real-time market quotes for multiple symbols.

        Args:
            symbols: List of symbols in Fyers format (e.g., ["NSE:SBIN-EQ", "NSE:TCS-EQ"])
                Maximum 50 symbols per request.

        Returns:
            str: Quote data in CSV format with columns:
                SYMBOL, LTP, CHANGE, CHANGE_PCT, VOLUME, OPEN, HIGH, LOW, PREV_CLOSE, BID, ASK

        Note: Results are cached for 30 seconds.
        """
        # Sort symbols for consistent cache key
        sorted_symbols = tuple(sorted(symbols))

        # Check cache
        cached = self.cache.get("quotes", sorted_symbols)
        if cached:
            return cached

        response = await self.client.get_quotes(symbols)

        lines = ["SYMBOL,LTP,CHANGE,CHANGE_PCT,VOLUME,OPEN,HIGH,LOW,PREV_CLOSE,BID,ASK"]
        for quote in response.d or []:
            v = quote.v
            if v:
                lines.append(
                    f"{quote.n},{v.get('lp')},{v.get('ch')},{v.get('chp')},{v.get('volume')},"
                    f"{v.get('open_price')},{v.get('high_price')},{v.get('low_price')},{v.get('prev_close_price')},"
                    f"{v.get('bid')},{v.get('ask')}"
                )

        result = "\n".join(lines)
        self.cache.set("quotes", result, sorted_symbols)
        return result

    async def get_market_depth(self, symbol: str) -> str:
        """
        Get order book depth for a symbol showing bid/ask levels.

        Args:
            symbol: Symbol in Fyers format (e.g., "NSE:SBIN-EQ")

        Returns:
            str: Market depth data showing:
                - LTP, volume, and spread info
                - Top 5 bid levels (price, volume, order count)
                - Top 5 ask levels (price, volume, order count)

        Note: Results are cached for 30 seconds.
        """
        # Check cache
        cached = self.cache.get("depth", symbol)
        if cached:
            return cached

        response = await self.client.get_market_depth(symbol, ohlcv_flag=1)
        data = response.d.get(symbol) if response.d else None

        lines = [f"MARKET DEPTH FOR {symbol}"]
        if data:
            lines.append(f"LTP: {data.ltp}, VOLUME: {data.v}")
            lines.append(f"TOTAL_BUY_QTY: {data.totalbuyqty}, TOTAL_SELL_QTY: {data.totalsellqty}")

            lines.append("\nBIDS (Price,Volume,Orders):")
            for bid in data.bids or []:
                lines.append(f"  {bid.price}, {bid.volume}, {bid.ord}")

            lines.append("\nASKS (Price,Volume,Orders):")
            for ask in data.ask or []:
                lines.append(f"  {ask.price}, {ask.volume}, {ask.ord}")
        else:
            lines.append("No depth data available")

        result = "\n".join(lines)
        self.cache.set("depth", result, symbol)
        return result

    async def get_historical_data(
        self,
        symbol: str,
        resolution: str = "D",
        days: int = 100
    ) -> str:
        """
        Get historical OHLCV candle data for technical analysis.

        Args:
            symbol: Symbol in Fyers format (e.g., "NSE:SBIN-EQ")
            resolution: Candle timeframe:
                - Minutes: "1", "5", "15", "30", "60"
                - Day: "D" or "1D"
            days: Number of days of history (max 100 for intraday, 366 for daily)

        Returns:
            str: Historical candles in CSV format:
                TIMESTAMP,OPEN,HIGH,LOW,CLOSE,VOLUME

        Note: Results are cached for 1 hour.
        """
        # Check cache
        cached = self.cache.get("historical", symbol, resolution=resolution, days=days)
        if cached:
            return cached

        range_to = datetime.now().strftime("%Y-%m-%d")
        range_from = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")

        response = await self.client.get_history(
            symbol=symbol,
            resolution=resolution,
            date_format=1,
            range_from=range_from,
            range_to=range_to
        )

        lines = ["TIMESTAMP,OPEN,HIGH,LOW,CLOSE,VOLUME"]
        for candle in response.candles or []:
            lines.append(f"{candle[0]},{candle[1]},{candle[2]},{candle[3]},{candle[4]},{candle[5]}")

        result = "\n".join(lines)
        self.cache.set("historical", result, symbol, resolution=resolution, days=days)
        return result

    async def get_option_chain(self, symbol: str, strike_count: int = 5) -> str:
        """
        Get option chain data for derivatives analysis.

        Args:
            symbol: Underlying symbol (e.g., "NSE:NIFTY50-INDEX", "NSE:SBIN-EQ")
            strike_count: Number of strikes above/below ATM (max 50)

        Returns:
            str: Option chain in CSV format:
                SYMBOL,STRIKE,TYPE,LTP,OI,VOLUME,IV,CHANGE,CHANGE_PCT

        Note: Results are cached for 2 minutes.
        """
        # Check cache
        cached = self.cache.get("options", symbol, strike_count=strike_count)
        if cached:
            return cached

        response = await self.client.get_option_chain(symbol, strike_count=strike_count)

        lines = ["SYMBOL,STRIKE,TYPE,LTP,OI,VOLUME,IV,CHANGE,CHANGE_PCT"]
        # Use helper method to get options chain (data is a dict)
        options_chain = response.get_options_chain()

        for option in options_chain:
            # options are dicts, not pydantic models
            lines.append(
                f"{option.get('symbol', '')},{option.get('strike_price', '')},"
                f"{option.get('option_type', '')},{option.get('ltp', '')},"
                f"{option.get('oi', '')},{option.get('volume', '')},"
                f"{option.get('iv', '')},{option.get('ch', '')},{option.get('chp', '')}"
            )

        result = "\n".join(lines)
        self.cache.set("options", result, symbol, strike_count=strike_count)
        return result

    async def get_option_greeks(self, symbol: str, strike_count: int = 5) -> str:
        """
        Get option chain with computed Greeks (IV, Delta, Gamma, Theta, Vega, Rho).

        Uses Black-Scholes model for European-style options.

        Args:
            symbol: Underlying symbol (e.g., "NSE:NIFTY50-INDEX", "NSE:SBIN-EQ")
            strike_count: Number of strikes above/below ATM (max 50)

        Returns:
            str: Option chain with Greeks in CSV format:
                SYMBOL,STRIKE,TYPE,EXPIRY_DAYS,LTP,IV,DELTA,GAMMA,THETA,VEGA,RHO,OI,VOLUME

        Notes:
            - IV is in percentage (e.g., 20.5 means 20.5%)
            - Theta is per day (time decay)
            - Vega is per 1% change in volatility
            - Rho is per 1% change in interest rate

        Note: Results are cached for 2 minutes.
        """
        # Check cache
        cached = self.cache.get("options", symbol, strike_count=strike_count, greeks=True)
        if cached:
            return cached

        try:
            greeks_data = await self.client.get_option_greeks(symbol, strike_count=strike_count)

            lines = ["SYMBOL,STRIKE,TYPE,EXPIRY_DAYS,LTP,IV,DELTA,GAMMA,THETA,VEGA,RHO,OI,VOLUME"]
            for opt in greeks_data:
                iv = opt.get("iv") or ""
                delta = opt.get("delta") or ""
                gamma = opt.get("gamma") or ""
                theta = opt.get("theta") or ""
                vega = opt.get("vega") or ""
                rho = opt.get("rho") or ""

                lines.append(
                    f"{opt.get('symbol', '')},{opt.get('strike', '')},"
                    f"{opt.get('option_type', '')},{opt.get('time_to_expiry_days', '')},"
                    f"{opt.get('ltp', '')},{iv},{delta},{gamma},{theta},{vega},{rho},"
                    f"{opt.get('oi', '')},{opt.get('volume', '')}"
                )

            result = "\n".join(lines)
            self.cache.set("options", result, symbol, strike_count=strike_count, greeks=True)
            return result
        except Exception as e:
            return f"ERROR: {str(e)}"

    async def get_market_status(self) -> str:
        """
        Get current market status for all exchanges and segments.

        Returns:
            str: Market status showing exchange, segment, and status (Open/Closed)
        """
        response = await self.client.get_market_status()

        lines = ["EXCHANGE,SEGMENT,MARKET_TYPE,STATUS"]
        # Use marketStatus (camelCase) as per the response model
        for status in response.marketStatus or []:
            lines.append(
                f"{status.exchange},{status.segment},"
                f"{status.market_type},{status.status}"
            )

        return "\n".join(lines)

    # ==================== Position Tools ====================

    async def get_positions(self) -> str:
        """
        Get all open positions for the day.

        Returns:
            str: Positions in CSV format:
                SYMBOL,QTY,AVG_PRICE,SIDE,REALIZED_PNL,UNREALIZED_PNL,LTP

        Note: Results are cached for 10 seconds.
        """
        # Check cache
        cached = self.cache.get("positions")
        if cached:
            return cached

        response = await self.client.get_positions()

        positions = response.netPositions or []
        if not positions:
            return "NO OPEN POSITIONS"

        lines = ["SYMBOL,QTY,AVG_PRICE,SIDE,REALIZED_PNL,UNREALIZED_PNL,LTP"]
        for pos in positions:
            side = "LONG" if pos.side == 1 else "SHORT" if pos.side == -1 else "CLOSED"
            lines.append(
                f"{pos.symbol},{pos.netQty},{pos.netAvg},{side},"
                f"{pos.realized_profit},{pos.unrealized_profit},{pos.ltp}"
            )

        result = "\n".join(lines)
        self.cache.set("positions", result)
        return result

    async def exit_position(self, position_id: Optional[str] = None) -> str:
        """
        Exit one or all positions.

        Args:
            position_id: Specific position ID to exit, or None to exit all

        Returns:
            str: Exit confirmation message
        """
        response = await self.client.exit_position(position_id)

        if response.s == "ok":
            if position_id:
                return f"POSITION EXITED: {position_id}"
            return "ALL POSITIONS EXITED"
        return f"EXIT FAILED: {response.message}"

    # ==================== Order Tools ====================

    async def place_order(
        self,
        symbol: str,
        qty: int,
        side: int,
        order_type: int = 2,
        limit_price: float = 0.0,
        stop_price: float = 0.0,
        product_type: str = "INTRADAY"
    ) -> str:
        """
        Place a trading order.

        Args:
            symbol: Symbol to trade (e.g., "NSE:SBIN-EQ")
            qty: Quantity to trade
            side: 1 for BUY, -1 for SELL
            order_type: 1=Limit, 2=Market, 3=Stop, 4=StopLimit
            limit_price: Limit price (required for type 1, 4)
            stop_price: Stop/trigger price (required for type 3, 4)
            product_type: INTRADAY, CNC, MARGIN

        Returns:
            str: Order confirmation with order ID
        """
        order_data = {
            "symbol": symbol,
            "qty": qty,
            "side": side,
            "type": order_type,
            "limitPrice": limit_price,
            "stopPrice": stop_price,
            "productType": product_type,
        }

        response = await self.client.place_order(order_data)

        if response.s == "ok":
            side_str = "BUY" if side == 1 else "SELL"
            return f"ORDER PLACED: ID={response.id}, SYMBOL={symbol}, QTY={qty}, SIDE={side_str}"
        return f"ORDER FAILED: {response.message}"

    async def get_orders(self) -> str:
        """
        Get all orders for the day.

        Returns:
            str: Orders in CSV format:
                ORDER_ID,SYMBOL,QTY,FILLED_QTY,SIDE,TYPE,STATUS,PRICE,MESSAGE
        """
        response = await self.client.get_orders()

        orders = response.orderBook or []
        if not orders:
            return "NO ORDERS TODAY"

        lines = ["ORDER_ID,SYMBOL,QTY,FILLED_QTY,SIDE,TYPE,STATUS,PRICE,MESSAGE"]
        for order in orders:
            side = "BUY" if order.side == 1 else "SELL"
            status_map = {1: "CANCELLED", 2: "TRADED", 4: "TRANSIT", 5: "REJECTED", 6: "PENDING", 7: "EXPIRED"}
            status = status_map.get(order.status, f"UNKNOWN({order.status})")
            lines.append(
                f"{order.id},{order.symbol},{order.qty},{order.filledQty},"
                f"{side},{order.type},{status},{order.limitPrice},{order.message or ''}"
            )

        return "\n".join(lines)

    # ==================== Portfolio Tools ====================

    async def get_holdings(self) -> str:
        """
        Get portfolio holdings (delivery shares).

        Returns:
            str: Holdings in CSV format:
                SYMBOL,QTY,AVG_PRICE,CURRENT_PRICE,PNL,PNL_PCT

        Note: Results are cached for 5 minutes.
        """
        # Check cache
        cached = self.cache.get("holdings")
        if cached:
            return cached

        response = await self.client.get_holdings()

        holdings = response.holdings or []
        if not holdings:
            return "NO HOLDINGS"

        lines = ["SYMBOL,QTY,AVG_PRICE,CURRENT_PRICE,PNL,PNL_PCT"]
        for holding in holdings:
            pnl = (holding.ltp - holding.costPrice) * holding.quantity if holding.ltp and holding.costPrice else 0
            pnl_pct = (pnl / (holding.costPrice * holding.quantity) * 100) if holding.costPrice and holding.quantity else 0
            lines.append(
                f"{holding.symbol},{holding.quantity},{holding.costPrice},"
                f"{holding.ltp},{pnl:.2f},{pnl_pct:.2f}"
            )

        result = "\n".join(lines)
        self.cache.set("holdings", result)
        return result

    async def get_funds(self) -> str:
        """
        Get available funds and margin information.

        Returns:
            str: Funds summary with available balance, used margin, etc.

        Note: Results are cached for 1 minute.
        """
        # Check cache
        cached = self.cache.get("funds")
        if cached:
            return cached

        response = await self.client.get_funds()

        funds = response.fund_limit or []
        lines = ["FUNDS SUMMARY"]

        for fund in funds:
            lines.append(f"{fund.title}: {fund.equityAmount}")

        result = "\n".join(lines)
        self.cache.set("funds", result)
        return result

    async def get_profile(self) -> str:
        """
        Get user profile information.

        Returns:
            str: Profile information

        Note: Results are cached for 24 hours.
        """
        # Check cache
        cached = self.cache.get("profile")
        if cached:
            return cached

        response = await self.client.get_profile()

        if response.data:
            profile = response.data
            result = (
                f"USER PROFILE\n"
                f"Name: {profile.name}\n"
                f"Fyers ID: {profile.fy_id}\n"
                f"Email: {profile.email_id}\n"
                f"PAN: {profile.pan}"
            )
            self.cache.set("profile", result)
            return result
        return "PROFILE NOT AVAILABLE"

    # ==================== Margin Tools ====================

    async def calculate_margin(self, orders_data: str) -> str:
        """
        Calculate margin requirement for orders.

        Args:
            orders_data: Orders in format "symbol,qty,side;symbol,qty,side"
                Example: "NSE:SBIN-EQ,100,1;NSE:TCS-EQ,50,-1"

        Returns:
            str: Margin requirements
        """
        orders = []
        for order_str in orders_data.split(";"):
            parts = order_str.strip().split(",")
            if len(parts) >= 3:
                orders.append({
                    "symbol": parts[0],
                    "qty": int(parts[1]),
                    "side": int(parts[2]),
                    "type": 2,
                    "limitPrice": 0.0,
                    "productType": "INTRADAY"
                })

        if not orders:
            return "ERROR: Invalid order format. Use: symbol,qty,side;symbol,qty,side"

        response = await self.client.calculate_order_margin(orders)

        if not response.is_success() or response.data is None:
            return f"ERROR: Failed to calculate margin. {response.message}"

        data = response.data

        # Access Pydantic model attributes directly (not dict)
        return (
            f"MARGIN CALCULATION\n"
            f"Total Required: ₹{data.margin_total:,.2f}\n"
            f"Available: ₹{data.margin_avail:,.2f}\n"
            f"After Order: ₹{data.margin_new_order:,.2f}"
        )

    # ==================== Analysis Tools ====================

    async def get_technical_indicators(
        self,
        symbol: str,
        resolution: str = "D",
        days: int = 100
    ) -> str:
        """
        Get computed technical indicators for a symbol.

        Args:
            symbol: Symbol in Fyers format (e.g., "NSE:SBIN-EQ")
            resolution: Candle resolution (D, 60, 15, etc.)
            days: Days of history to analyze

        Returns:
            str: JSON string of computed indicators including:
                - SMA (20, 50, 200), EMA (12, 26)
                - MACD (signal, histogram)
                - RSI (14)
                - Bollinger Bands
                - ATR
                - Support/Resistance levels

        Note: Results are cached for 1 hour.
        """
        # Check cache
        cached = self.cache.get("indicators", symbol, resolution=resolution, days=days)
        if cached:
            return cached

        try:
            csv_data = await self.get_historical_data(symbol, resolution, days)
            lines = csv_data.split("\n")

            if len(lines) <= 1:
                return json.dumps({"error": "No data found"})

            # Parse CSV to dataframe
            ohlcv_list = []
            for line in lines[1:]:
                parts = line.split(",")
                if len(parts) >= 6:
                    ohlcv_list.append({
                        "timestamp": int(parts[0]),
                        "open": float(parts[1]),
                        "high": float(parts[2]),
                        "low": float(parts[3]),
                        "close": float(parts[4]),
                        "volume": int(parts[5])
                    })

            if not ohlcv_list:
                return json.dumps({"error": "No valid candles"})

            df = pd.DataFrame(ohlcv_list)

            # Compute indicators
            indicators = self._compute_indicators(df)
            indicators['symbol'] = symbol

            result = json.dumps(indicators, indent=2)
            self.cache.set("indicators", result, symbol, resolution=resolution, days=days)
            return result

        except Exception as e:
            return json.dumps({"error": str(e)})

    def _compute_indicators(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Compute technical indicators from OHLCV data."""
        close = df['close']
        high = df['high']
        low = df['low']

        result = {}

        # Current price info
        result['current_price'] = float(close.iloc[-1])
        result['prev_close'] = float(close.iloc[-2]) if len(close) > 1 else None

        # Moving Averages
        if len(close) >= 20:
            result['sma_20'] = float(close.rolling(20).mean().iloc[-1])
        if len(close) >= 50:
            result['sma_50'] = float(close.rolling(50).mean().iloc[-1])
        if len(close) >= 200:
            result['sma_200'] = float(close.rolling(200).mean().iloc[-1])

        # EMA
        if len(close) >= 12:
            result['ema_12'] = float(close.ewm(span=12).mean().iloc[-1])
        if len(close) >= 26:
            result['ema_26'] = float(close.ewm(span=26).mean().iloc[-1])

        # MACD
        if len(close) >= 26:
            ema12 = close.ewm(span=12).mean()
            ema26 = close.ewm(span=26).mean()
            macd = ema12 - ema26
            signal = macd.ewm(span=9).mean()
            result['macd'] = float(macd.iloc[-1])
            result['macd_signal'] = float(signal.iloc[-1])
            result['macd_histogram'] = float((macd - signal).iloc[-1])

        # RSI
        if len(close) >= 15:
            delta = close.diff()
            gain = delta.where(delta > 0, 0).rolling(14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
            rs = gain / loss
            result['rsi_14'] = float(100 - (100 / (1 + rs.iloc[-1])))

        # Bollinger Bands
        if len(close) >= 20:
            sma20 = close.rolling(20).mean()
            std20 = close.rolling(20).std()
            result['bb_upper'] = float((sma20 + 2 * std20).iloc[-1])
            result['bb_middle'] = float(sma20.iloc[-1])
            result['bb_lower'] = float((sma20 - 2 * std20).iloc[-1])

        # ATR
        if len(close) >= 15:
            tr = pd.concat([
                high - low,
                (high - close.shift()).abs(),
                (low - close.shift()).abs()
            ], axis=1).max(axis=1)
            result['atr_14'] = float(tr.rolling(14).mean().iloc[-1])

        # Support/Resistance (recent highs/lows)
        if len(close) >= 20:
            result['recent_high'] = float(high.tail(20).max())
            result['recent_low'] = float(low.tail(20).min())

        return result

    async def get_correlation_matrix(self, symbols: List[str], days: int = 100) -> str:
        """
        Compute correlation matrix for multiple symbols.

        Args:
            symbols: List of symbols to analyze
            days: Number of days of history

        Returns:
            str: JSON correlation matrix

        Note: Results are cached for 1 hour. For NIFTY100 correlations, use CorrelationToolkit.
        """
        # Sort symbols for consistent cache key
        sorted_symbols = tuple(sorted(symbols))

        # Check cache
        cached = self.cache.get("correlation", sorted_symbols, days=days)
        if cached:
            return cached

        try:
            data = {}
            for symbol in symbols:
                csv_data = await self.get_historical_data(symbol, days=days)
                lines = csv_data.split("\n")

                if len(lines) > 1:
                    prices = []
                    timestamps = []
                    for line in lines[1:]:
                        parts = line.split(",")
                        if len(parts) >= 5:
                            timestamps.append(int(parts[0]))
                            prices.append(float(parts[4]))  # Close price

                    if prices:
                        s = pd.Series(prices, index=pd.to_datetime(timestamps, unit='s'), name=symbol)
                        data[symbol] = s

            if not data:
                return json.dumps({"error": "No data retrieved for symbols"})

            df = pd.DataFrame(data).dropna()

            if df.empty:
                return json.dumps({"error": "No overlapping data found"})

            # Compute correlation on returns
            returns = df.pct_change().dropna()
            corr_matrix = returns.corr()

            result = json.dumps({
                "correlation_matrix": corr_matrix.to_dict(),
                "symbols": list(corr_matrix.columns),
                "data_points": len(returns)
            }, indent=2)

            self.cache.set("correlation", result, sorted_symbols, days=days)
            return result

        except Exception as e:
            return json.dumps({"error": str(e)})
