"""
Main Fyers client class.

This is the main entry point for the Fyers SDK.
"""

from typing import Any, Callable, Dict, List, Optional, Union

from broker.fyers.core.exceptions import (
    FyersException,
    FyersAuthenticationError,
    FyersTokenNotFoundError,
)
from broker.fyers.websocket import (
    FyersOrderWebSocket,
    FyersDataWebSocket,
    FyersOrderWebSocketSync,
    FyersDataWebSocketSync,
    FyersTBTWebSocket,
    FyersTBTWebSocketSync,
    WebSocketConfig,
    OrderUpdate,
    TradeUpdate,
    PositionUpdate,
    GeneralUpdate,
    SymbolUpdate,
    DepthUpdate,
    IndexUpdate,
    TBTDepth,
    TBTConfig,
    SubscriptionType,
    DataType,
)
from broker.fyers.core.logger import get_logger, configure_logging
from broker.fyers.core.http_client import HTTPClient
from broker.fyers.core.rate_limiter import RateLimiter
from broker.fyers.models.config import FyersConfig
from broker.fyers.models.rate_limit import RateLimitConfig
from broker.fyers.models.auth import TokenData
from broker.fyers.auth.oauth import FyersOAuth
from broker.fyers.auth.token_storage import (
    TokenStorage,
    FileTokenStorage,
    MemoryTokenStorage,
    TokenManager,
)

logger = get_logger("fyers.client")


class FyersClient:
    """
    Main client for interacting with the Fyers API.
    
    Provides:
    - OAuth authentication flow
    - Rate-limited API requests
    - Token management
    - Comprehensive logging
    
    Example usage:
        ```python
        from broker.fyers import FyersClient, FyersConfig
        
        config = FyersConfig(
            client_id="TX4LY7JMLL-100",
            secret_key="your_secret_key",
            redirect_uri="https://your-redirect-uri.com",
        )
        
        client = FyersClient(config)
        
        # Generate auth URL for OAuth flow
        auth_url = client.generate_auth_url()
        print(f"Please visit: {auth_url}")
        
        # After user authenticates, get the redirect URL
        redirect_url = "https://your-redirect-uri.com?auth_code=..."
        await client.authenticate(redirect_url)
        
        # Now you can make API calls
        quotes = await client.get_quotes(["NSE:INFY-EQ"])
        ```
    """
    
    def __init__(
        self,
        config: FyersConfig,
        token_storage: Optional[TokenStorage] = None,
        rate_limiter: Optional[RateLimiter] = None,
    ):
        """
        Initialize the Fyers client.
        
        Args:
            config: Fyers configuration
            token_storage: Optional token storage backend. If not provided,
                          uses FileTokenStorage if token_file_path is set,
                          otherwise MemoryTokenStorage.
            rate_limiter: Optional rate limiter. If not provided, creates
                         a new one with default settings.
        """
        self.config = config
        
        # Configure logging
        if config.log_file or config.log_level != "INFO":
            import logging
            level = getattr(logging, config.log_level.upper(), logging.INFO)
            configure_logging(level=level, log_file=config.log_file)
        
        # Set up token storage
        if token_storage:
            self._token_storage = token_storage
        elif config.token_file_path:
            self._token_storage = FileTokenStorage(config.token_file_path)
        else:
            self._token_storage = MemoryTokenStorage()
        
        # Set up rate limiter
        self._rate_limiter = rate_limiter or RateLimiter(
            config=RateLimitConfig(),
            persistence_path=config.rate_limit_file_path,
        )
        
        # Initialize components
        self._http_client = HTTPClient(
            config=config,
            rate_limiter=self._rate_limiter,
        )
        
        self._oauth = FyersOAuth(
            config=config,
            token_storage=self._token_storage,
        )
        
        self._token_manager = TokenManager(self._token_storage)
        
        # State
        self._is_authenticated = False
        
        logger.info(f"FyersClient initialized for client_id: {config.client_id}")
    
    # ==================== Authentication ====================
    
    def generate_auth_url(self, state: Optional[str] = None) -> str:
        """
        Generate the authorization URL for OAuth flow.
        
        Args:
            state: Optional state parameter for CSRF protection
            
        Returns:
            Authorization URL
        """
        return self._oauth.generate_auth_url(state)
    
    def open_auth_url(self, state: Optional[str] = None) -> str:
        """
        Generate and open authorization URL in browser.
        
        Args:
            state: Optional state parameter
            
        Returns:
            The authorization URL that was opened
        """
        return self._oauth.open_auth_url(state)
    
    async def authenticate(
        self,
        redirect_url: str,
        verify_state: bool = True,
    ) -> TokenData:
        """
        Complete authentication using the redirect URL.
        
        Args:
            redirect_url: Full redirect URL from OAuth callback
            verify_state: Whether to verify state parameter
            
        Returns:
            TokenData with access token
        """
        token_data = await self._oauth.authenticate_with_redirect(
            redirect_url,
            verify_state,
        )
        
        # Set token in HTTP client
        self._http_client.set_access_token(token_data.access_token)
        self._is_authenticated = True
        
        logger.info("Successfully authenticated")
        return token_data
    
    async def authenticate_with_callback_server(
        self,
        port: Optional[int] = None,
        host: Optional[str] = None,
        timeout: int = 300,
    ) -> TokenData:
        """
        Authenticate automatically using a local HTTP callback server.
        
        This is the easiest authentication method - no manual copy-paste needed!
        Opens browser, waits for OAuth redirect, and automatically captures credentials.
        
        IMPORTANT: Your redirect_uri must be registered in Fyers dashboard beforehand.
        The server will use the exact host/port from your configured redirect_uri.
        
        Args:
            port: Port for callback server (uses redirect_uri port if None)
            host: Host address for callback server (uses redirect_uri host if None)
            timeout: Max seconds to wait for callback (default: 300)
            
        Returns:
            TokenData with access token
            
        Raises:
            FyersAuthenticationError: If authentication fails or times out
            RuntimeError: If the configured port is already in use
            
        Example:
            ```python
            # Step 1: Register redirect_uri in Fyers dashboard
            # e.g., http://127.0.0.1:9000/
            
            # Step 2: Configure client with same redirect_uri
            config = FyersConfig(
                client_id="YOUR_CLIENT_ID",
                secret_key="YOUR_SECRET",
                redirect_uri="http://127.0.0.1:9000/"  # Must match Fyers dashboard
            )
            client = FyersClient(config)
            
            # Step 3: Authenticate automatically - browser opens, you login, done!
            await client.authenticate_with_callback_server()
            
            # Now you can make API calls
            quotes = await client.get_quotes(["NSE:SBIN-EQ"])
            ```
        """
        token_data = await self._oauth.authenticate_with_callback_server(
            port=port,
            host=host,
            timeout=timeout,
        )
        
        # Set token in HTTP client
        self._http_client.set_access_token(token_data.access_token)
        self._is_authenticated = True
        
        logger.info("Successfully authenticated with callback server")
        return token_data
    
    async def authenticate_with_auth_code(self, auth_code: str) -> TokenData:
        """
        Authenticate using an authorization code directly.
        
        Args:
            auth_code: Authorization code from OAuth redirect
            
        Returns:
            TokenData with access token
        """
        token_data = await self._oauth.validate_auth_code(auth_code)
        
        self._http_client.set_access_token(token_data.access_token)
        self._is_authenticated = True
        
        logger.info("Successfully authenticated with auth code")
        return token_data
    
    async def set_access_token(self, access_token: str) -> None:
        """
        Set an existing access token directly.
        
        Use this when you already have a valid access token.
        
        Args:
            access_token: Valid access token
        """
        token_data = TokenData(access_token=access_token)
        await self._token_manager.set_token(token_data)
        self._http_client.set_access_token(access_token)
        self._is_authenticated = True
        
        logger.info("Access token set directly")
    
    async def refresh_token(self, pin: str) -> TokenData:
        """
        Refresh the access token using the refresh token.
        
        Args:
            pin: User's PIN
            
        Returns:
            New TokenData with fresh access token
        """
        current_token = await self._token_manager.get_token()
        
        if not current_token or not current_token.refresh_token:
            raise FyersAuthenticationError("No refresh token available")
        
        token_data = await self._oauth.refresh_access_token(
            current_token.refresh_token,
            pin,
        )
        
        self._http_client.set_access_token(token_data.access_token)
        
        logger.info("Successfully refreshed access token")
        return token_data
    
    async def load_saved_token(self) -> bool:
        """
        Load and validate a previously saved token.
        
        Returns:
            True if valid token was loaded
        """
        try:
            token_data = await self._token_manager.get_token()
            
            if token_data and not token_data.is_expired():
                self._http_client.set_access_token(token_data.access_token)
                self._is_authenticated = True
                logger.info("Loaded saved token")
                return True
            
            return False
            
        except FyersTokenNotFoundError:
            return False
    
    async def logout(self) -> None:
        """Clear authentication and stored tokens."""
        await self._oauth.logout()
        self._http_client.clear_access_token()
        self._is_authenticated = False
        logger.info("Logged out")
    
    @property
    def is_authenticated(self) -> bool:
        """Check if client is authenticated."""
        return self._is_authenticated
    
    async def get_token(self) -> Optional[TokenData]:
        """Get the current token data."""
        return await self._oauth.get_token()
    
    # ==================== Market Data APIs ====================
    
    async def get_quotes(self, symbols: List[str]) -> Dict[str, Any]:
        """
        Get full market quotes for symbols.
        
        Maximum 50 symbols per request.
        
        Response includes: ch (change), chp (change%), lp (LTP), spread,
        ask, bid, open_price, high_price, low_price, prev_close_price,
        volume, etc.
        
        Args:
            symbols: List of symbols (e.g., ["NSE:INFY-EQ", "NSE:TCS-EQ"])
                Maximum 50 symbols per request.
            
        Returns:
            Quote data from API
        """
        self._ensure_authenticated()
        
        # Use data API endpoint for quotes
        params = {"symbols": ",".join(symbols)}
        return await self._http_client.get(
            "/quotes",
            params=params,
            base_url="https://api-t1.fyers.in/data",
        )
    
    async def get_market_depth(
        self,
        symbol: str,
        ohlcv_flag: int = 1,
    ) -> Dict[str, Any]:
        """
        Get complete market depth for a symbol.
        
        Returns bid/ask prices with volume and order count,
        OHLCV data, circuit limits, and open interest.
        
        Args:
            symbol: Symbol to get depth for (e.g., "NSE:SBIN-EQ")
            ohlcv_flag: Include OHLCV data (1=yes, 0=no)
            
        Returns:
            Market depth data including:
            - totalbuyqty, totalsellqty
            - bids: [{price, volume, ord}]
            - ask: [{price, volume, ord}]
            - o, h, l, c (OHLC)
            - ltp, ltq, ltt
            - v (volume), atp (average traded price)
            - lower_ckt, upper_ckt (circuit limits)
            - oi, pdoi, oipercent (open interest)
        """
        self._ensure_authenticated()
        
        params = {"symbol": symbol, "ohlcv_flag": ohlcv_flag}
        return await self._http_client.get(
            "/depth",
            params=params,
            base_url="https://api-t1.fyers.in/data",
        )
    
    async def get_history(
        self,
        symbol: str,
        resolution: str,
        date_format: int,
        range_from: str,
        range_to: str,
        cont_flag: int = 0,
        oi_flag: int = 0,
    ) -> Dict[str, Any]:
        """
        Get historical candle data.
        
        Limits:
        - Up to 100 days per request for minute resolutions (1-240)
        - Up to 366 days per request for daily resolution
        - Data available from July 3, 2017
        - Seconds charts available for 30 trading days
        
        Note: To receive completed candle data, send a timestamp that
        comes before the current minute. Use range_to = current_time - resolution.
        
        Args:
            symbol: Symbol (e.g., "NSE:SBIN-EQ")
            resolution: Candle resolution:
                - Seconds: "5S", "10S", "15S", "30S", "45S"
                - Minutes: "1", "2", "3", "5", "10", "15", "20", "30", "60", "120", "240"
                - Day: "D" or "1D"
            date_format: 0 for epoch, 1 for YYYY-MM-DD
            range_from: Start date/timestamp
            range_to: End date/timestamp
            cont_flag: Set to 1 for continuous data (futures/options)
            oi_flag: Set to 1 to include open interest in candle data
            
        Returns:
            Historical candle data:
            {
                "s": "ok",
                "candles": [[epoch, open, high, low, close, volume], ...]
            }
        """
        self._ensure_authenticated()
        
        params = {
            "symbol": symbol,
            "resolution": resolution,
            "date_format": date_format,
            "range_from": range_from,
            "range_to": range_to,
            "cont_flag": cont_flag,
        }
        
        if oi_flag:
            params["oi_flag"] = oi_flag
        
        return await self._http_client.get(
            "/history",
            params=params,
            base_url="https://api-t1.fyers.in/data",
        )
    
    async def get_option_chain(
        self,
        symbol: str,
        strike_count: int = 10,
        timestamp: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Get option chain data for a symbol.
        
        Returns strike prices including ATM, OTM, and ITM options
        for both Call (CE) and Put (PE) options.
        
        Args:
            symbol: Underlying symbol (e.g., "NSE:SBIN-EQ", "NSE:NIFTY-INDEX")
            strike_count: Number of strikes to return (max 50)
                Returns strike_count ITM + ATM + strike_count OTM for each option type
            timestamp: Optional timestamp for historical option chain
            
        Returns:
            Option chain data including:
            - callOi, putOi: Total OI for calls/puts
            - expiryData: Available expiry dates
            - indiavixData: India VIX data
            - optionsChain: List of option contracts with:
                - symbol, fyToken, strike_price, option_type
                - ltp, ltpch, ltpchp
                - oi, oich, oichp, prev_oi
                - volume, bid, ask
        """
        self._ensure_authenticated()
        
        params = {
            "symbol": symbol,
            "strikecount": strike_count,
        }
        
        if timestamp:
            params["timestamp"] = timestamp
        
        return await self._http_client.get(
            "/options-chain-v3",
            params=params,
            base_url="https://api-t1.fyers.in/data",
        )
    
    # ==================== Order APIs ====================
    
    async def place_order(self, order_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Place a single order.
        
        Args:
            order_data: Order parameters
            
        Returns:
            Order response
        """
        self._ensure_authenticated()
        return await self._http_client.post("/orders/sync", json_data=order_data)
    
    async def place_multi_order(
        self,
        orders: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Place multiple orders.
        
        Args:
            orders: List of order data dictionaries
            
        Returns:
            Multi-order response
        """
        self._ensure_authenticated()
        return await self._http_client.post("/orders/multi", json_data=orders)
    
    async def modify_order(
        self,
        order_id: str,
        modifications: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Modify an existing order.
        
        Args:
            order_id: Order ID to modify
            modifications: Modifications to apply
            
        Returns:
            Modification response
        """
        self._ensure_authenticated()
        
        data = {"id": order_id, **modifications}
        return await self._http_client.put("/orders/sync", json_data=data)
    
    async def cancel_order(self, order_id: str) -> Dict[str, Any]:
        """
        Cancel an order.
        
        Args:
            order_id: Order ID to cancel
            
        Returns:
            Cancellation response
        """
        self._ensure_authenticated()
        
        data = {"id": order_id}
        return await self._http_client.delete("/orders/sync", json_data=data)
    
    async def get_orders(self) -> Dict[str, Any]:
        """
        Get all orders for the day.
        
        Returns:
            Orders list
        """
        self._ensure_authenticated()
        return await self._http_client.get("/orders")
    
    async def get_order_by_id(self, order_id: str) -> Dict[str, Any]:
        """
        Get details for a specific order.
        
        Args:
            order_id: Order ID
            
        Returns:
            Order details
        """
        self._ensure_authenticated()
        return await self._http_client.get(f"/orders/{order_id}")
    
    # ==================== Position APIs ====================
    
    async def get_positions(self) -> Dict[str, Any]:
        """
        Get all positions.
        
        Returns:
            Positions data
        """
        self._ensure_authenticated()
        return await self._http_client.get("/positions")
    
    async def exit_position(
        self,
        position_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Exit position(s).
        
        Args:
            position_id: Specific position to exit (None = exit all)
            
        Returns:
            Exit response
        """
        self._ensure_authenticated()
        
        if position_id:
            data = {"id": position_id}
        else:
            data = {}
            
        return await self._http_client.delete("/positions", json_data=data)
    
    async def convert_position(
        self,
        conversion_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Convert position from one product to another.
        
        Args:
            conversion_data: Conversion parameters
            
        Returns:
            Conversion response
        """
        self._ensure_authenticated()
        return await self._http_client.put("/positions", json_data=conversion_data)
    
    # ==================== Portfolio APIs ====================
    
    async def get_holdings(self) -> Dict[str, Any]:
        """
        Get portfolio holdings.
        
        Returns:
            Holdings data
        """
        self._ensure_authenticated()
        return await self._http_client.get("/holdings")
    
    async def get_funds(self) -> Dict[str, Any]:
        """
        Get available funds.
        
        Returns:
            Funds data
        """
        self._ensure_authenticated()
        return await self._http_client.get("/funds")
    
    # ==================== User Profile APIs ====================
    
    async def get_profile(self) -> Dict[str, Any]:
        """
        Get user profile.
        
        Returns:
            Profile data
        """
        self._ensure_authenticated()
        return await self._http_client.get("/profile")
    
    async def get_tradebook(self) -> Dict[str, Any]:
        """
        Get trade book for the day.
        
        Returns:
            Trade book data
        """
        self._ensure_authenticated()
        return await self._http_client.get("/tradebook")
    
    async def get_tradebook_by_tag(self, order_tag: str) -> Dict[str, Any]:
        """
        Get trade book filtered by order tag.
        
        Args:
            order_tag: Order tag to filter by
            
        Returns:
            Filtered trade book data
        """
        self._ensure_authenticated()
        return await self._http_client.get(
            "/tradebook",
            params={"order_tag": order_tag}
        )
    
    async def get_orders_by_tag(self, order_tag: str) -> Dict[str, Any]:
        """
        Get orders filtered by order tag.
        
        Args:
            order_tag: Order tag to filter by
            
        Returns:
            Filtered orders list
        """
        self._ensure_authenticated()
        return await self._http_client.get(
            "/orders",
            params={"order_tag": order_tag}
        )
    
    async def get_order_by_id_filtered(self, order_id: str) -> Dict[str, Any]:
        """
        Get order details by order ID using query param.
        
        Args:
            order_id: Order ID to fetch
            
        Returns:
            Order details
        """
        self._ensure_authenticated()
        return await self._http_client.get(
            "/orders",
            params={"id": order_id}
        )
    
    # ==================== Multi-Leg Orders ====================
    
    async def place_multileg_order(
        self,
        legs: Dict[str, Dict[str, Any]],
        product_type: str = "INTRADAY",
        order_type: str = "2L",
        validity: str = "IOC",
        offline_order: bool = False,
        order_tag: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Place a multi-leg order (2L or 3L).
        
        Args:
            legs: Dictionary of legs (leg1, leg2, leg3)
                Each leg should have: symbol, qty, side, type, limitPrice
            product_type: INTRADAY or MARGIN
            order_type: 2L or 3L
            validity: Order validity (IOC for multi-leg)
            offline_order: True for AMO
            order_tag: Optional order tag
            
        Returns:
            Order placement response
        """
        self._ensure_authenticated()
        
        data = {
            "productType": product_type,
            "orderType": order_type,
            "validity": validity,
            "offlineOrder": offline_order,
            "legs": legs,
        }
        
        if order_tag:
            data["orderTag"] = order_tag
        
        return await self._http_client.post("/orders/multileg", json_data=data)
    
    # ==================== Cancel Multiple Orders ====================
    
    async def cancel_multi_order(self, order_ids: List[str]) -> Dict[str, Any]:
        """
        Cancel multiple orders at once.
        
        Args:
            order_ids: List of order IDs to cancel
            
        Returns:
            Multi-cancel response
        """
        self._ensure_authenticated()
        
        orders = [{"id": order_id} for order_id in order_ids]
        return await self._http_client.delete("/orders/multi", json_data=orders)
    
    # ==================== API Logout ====================
    
    async def api_logout(self) -> Dict[str, Any]:
        """
        Invalidate the access token via API.
        
        This invalidates the access token for this specific app only.
        
        Returns:
            Logout response
        """
        self._ensure_authenticated()
        
        response = await self._http_client.post("/logout")
        
        # Clear local auth state
        await self.logout()
        
        return response
    
    # ==================== GTT Orders ====================
    
    async def place_gtt_order(
        self,
        symbol: str,
        side: int,
        product_type: str,
        leg1_price: float,
        leg1_trigger_price: float,
        leg1_qty: int,
        leg2_price: Optional[float] = None,
        leg2_trigger_price: Optional[float] = None,
        leg2_qty: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Place a GTT (Good Till Trigger) order.
        
        For OCO orders, provide both leg1 and leg2 parameters.
        - leg1 trigger price should be above LTP
        - leg2 trigger price should be below LTP
        
        Args:
            symbol: Symbol (e.g., "NSE:SBIN-EQ")
            side: 1 for buy, -1 for sell
            product_type: CNC, MARGIN, or MTF
            leg1_price: Price for leg1
            leg1_trigger_price: Trigger price for leg1
            leg1_qty: Quantity for leg1
            leg2_price: Price for leg2 (OCO only)
            leg2_trigger_price: Trigger price for leg2 (OCO only)
            leg2_qty: Quantity for leg2 (OCO only)
            
        Returns:
            GTT order placement response
        """
        self._ensure_authenticated()
        
        order_info = {
            "leg1": {
                "price": leg1_price,
                "triggerPrice": leg1_trigger_price,
                "qty": leg1_qty,
            }
        }
        
        # Add leg2 for OCO orders
        if leg2_price is not None and leg2_trigger_price is not None and leg2_qty is not None:
            order_info["leg2"] = {
                "price": leg2_price,
                "triggerPrice": leg2_trigger_price,
                "qty": leg2_qty,
            }
        
        data = {
            "side": side,
            "symbol": symbol,
            "productType": product_type,
            "orderInfo": order_info,
        }
        
        return await self._http_client.post("/gtt/orders/sync", json_data=data)
    
    async def modify_gtt_order(
        self,
        order_id: str,
        leg1_price: Optional[float] = None,
        leg1_trigger_price: Optional[float] = None,
        leg1_qty: Optional[int] = None,
        leg2_price: Optional[float] = None,
        leg2_trigger_price: Optional[float] = None,
        leg2_qty: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Modify a pending GTT order.
        
        Args:
            order_id: GTT order ID to modify
            leg1_price: New price for leg1
            leg1_trigger_price: New trigger price for leg1
            leg1_qty: New quantity for leg1
            leg2_price: New price for leg2 (OCO only)
            leg2_trigger_price: New trigger price for leg2 (OCO only)
            leg2_qty: New quantity for leg2 (OCO only)
            
        Returns:
            GTT order modification response
        """
        self._ensure_authenticated()
        
        order_info: Dict[str, Any] = {}
        
        # Build leg1 if any leg1 params provided
        leg1: Dict[str, Any] = {}
        if leg1_price is not None:
            leg1["price"] = leg1_price
        if leg1_trigger_price is not None:
            leg1["triggerPrice"] = leg1_trigger_price
        if leg1_qty is not None:
            leg1["qty"] = leg1_qty
        if leg1:
            order_info["leg1"] = leg1
        
        # Build leg2 if any leg2 params provided
        leg2: Dict[str, Any] = {}
        if leg2_price is not None:
            leg2["price"] = leg2_price
        if leg2_trigger_price is not None:
            leg2["triggerPrice"] = leg2_trigger_price
        if leg2_qty is not None:
            leg2["qty"] = leg2_qty
        if leg2:
            order_info["leg2"] = leg2
        
        data = {
            "id": order_id,
            "orderInfo": order_info,
        }
        
        return await self._http_client.request(
            "PATCH", "/gtt/orders/sync", json_data=data
        )
    
    async def cancel_gtt_order(self, order_id: str) -> Dict[str, Any]:
        """
        Cancel a pending GTT order.
        
        Args:
            order_id: GTT order ID to cancel
            
        Returns:
            GTT order cancellation response
        """
        self._ensure_authenticated()
        
        data = {"id": order_id}
        return await self._http_client.delete("/gtt/orders/sync", json_data=data)
    
    async def get_gtt_orders(self) -> Dict[str, Any]:
        """
        Get all pending GTT orders.
        
        Returns:
            GTT order book
        """
        self._ensure_authenticated()
        return await self._http_client.get("/gtt/orders")
    
    # ==================== Modify Multi Orders ====================
    
    async def modify_multi_order(
        self,
        modifications: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Modify multiple orders at once (up to 10).
        
        Args:
            modifications: List of modification dictionaries.
                Each should have 'id' and fields to modify.
                
        Returns:
            Multi-modify response
        """
        self._ensure_authenticated()
        return await self._http_client.request(
            "PATCH", "/orders/multi", json_data=modifications
        )
    
    # ==================== Exit Position Advanced ====================
    
    async def exit_positions_by_ids(self, position_ids: List[str]) -> Dict[str, Any]:
        """
        Exit multiple positions by their IDs.
        
        Args:
            position_ids: List of position IDs to exit
            
        Returns:
            Exit response
        """
        self._ensure_authenticated()
        
        data = {"id": position_ids}
        return await self._http_client.delete("/positions", json_data=data)
    
    async def exit_positions_by_segment(
        self,
        segments: List[int],
        sides: List[int],
        product_types: List[str],
    ) -> Dict[str, Any]:
        """
        Exit positions by segment, side, and product type.
        
        Args:
            segments: List of segment codes (10=CM, 11=Derivatives, 12=Currency, 20=Commodity)
            sides: List of sides (1=Buy, -1=Sell)
            product_types: List of product types (INTRADAY, CNC, etc.)
            
        Returns:
            Exit response
        """
        self._ensure_authenticated()
        
        data = {
            "segment": segments,
            "side": sides,
            "productType": product_types,
        }
        return await self._http_client.delete("/positions", json_data=data)
    
    async def exit_all_positions_with_pending_cancel(self) -> Dict[str, Any]:
        """
        Exit all positions and cancel pending orders.
        
        Returns:
            Exit response
        """
        self._ensure_authenticated()
        
        data = {"pending_orders_cancel": 1}
        return await self._http_client.delete("/positions", json_data=data)
    
    async def exit_position_with_pending_cancel(
        self,
        position_id: str,
    ) -> Dict[str, Any]:
        """
        Exit a specific position and cancel its pending orders.
        
        Args:
            position_id: Position ID to exit
            
        Returns:
            Exit response
        """
        self._ensure_authenticated()
        
        data = {
            "id": position_id,
            "pending_orders_cancel": 1,
        }
        return await self._http_client.delete("/positions", json_data=data)
    
    # ==================== Margin Calculator ====================
    
    async def calculate_span_margin(
        self,
        positions: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Calculate span margin for given positions.
        
        Args:
            positions: List of position dictionaries with:
                - symbol: Symbol (e.g., "NSE:BANKNIFTY23NOV44400CE")
                - qty: Quantity
                - side: 1=Buy, -1=Sell
                - type: Order type (1-4)
                - productType: Product type
                - limitPrice: Limit price (default 0.0)
                - stopLoss: Stop loss (default 0.0)
                
        Returns:
            Span margin calculation result
        """
        self._ensure_authenticated()
        
        data = {"data": positions}
        return await self._http_client.post(
            "/span_margin",
            json_data=data,
            base_url="https://api.fyers.in/api/v2",
        )
    
    async def calculate_order_margin(
        self,
        orders: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Calculate margin for multiple orders.
        
        Args:
            orders: List of order dictionaries with:
                - symbol: Symbol
                - qty: Quantity
                - side: 1=Buy, -1=Sell
                - type: Order type
                - productType: Product type
                - limitPrice: Limit price (default 0.0)
                - stopLoss: Stop loss (default 0.0)
                - stopPrice: Stop price (default 0.0)
                - takeProfit: Take profit (default 0.0)
                
        Returns:
            Margin calculation with available margin, total margin, and new order margin
        """
        self._ensure_authenticated()
        
        data = {"data": orders}
        return await self._http_client.post("/multiorder/margin", json_data=data)
    
    # ==================== Market Status ====================
    
    async def get_market_status(self) -> Dict[str, Any]:
        """
        Get current market status for all exchanges and segments.
        
        Returns:
            Market status for each exchange/segment
        """
        self._ensure_authenticated()
        return await self._http_client.get("/market-status")
    
    # ==================== eDIS (Electronic Delivery Instruction Slip) ====================
    
    async def generate_edis_tpin(self) -> Dict[str, Any]:
        """
        Generate TPIN for eDIS transactions.
        
        TPIN is an authorization code from CDSL/NSDL required to
        authorize sell transactions from demat account.
        
        Returns:
            TPIN generation response
        """
        self._ensure_authenticated()
        return await self._http_client.get(
            "/tpin",
            base_url="https://api.fyers.in/api/v2",
        )
    
    async def get_edis_details(self) -> Dict[str, Any]:
        """
        Get eDIS authorization details.
        
        Returns information about holding authorizations that
        have been successfully completed.
        
        Returns:
            eDIS authorization details
        """
        self._ensure_authenticated()
        return await self._http_client.get(
            "/details",
            base_url="https://api.fyers.in/api/v2",
        )
    
    async def get_edis_index_page(
        self,
        holdings: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Get the CDSL page for eDIS authorization.
        
        Args:
            holdings: List of holdings to authorize with:
                - isin_code: ISIN code of the holding
                - qty: Quantity to authorize
                - symbol: Symbol (e.g., "NSE:SAIL-EQ")
                
        Returns:
            HTML page content for CDSL authorization
        """
        self._ensure_authenticated()
        
        data = {"recordLst": holdings}
        return await self._http_client.post(
            "/index",
            json_data=data,
            base_url="https://api.fyers.in/api/v2",
        )
    
    async def check_edis_transaction_status(
        self,
        transaction_id: str,
    ) -> Dict[str, Any]:
        """
        Check eDIS transaction status.
        
        Args:
            transaction_id: Base64 encoded transaction ID
                Example: For "915484108176", encode to "OTE1NDg0MTA4MTc2"
                
        Returns:
            Transaction status with success/failed counts
        """
        self._ensure_authenticated()
        
        data = {"transactionId": transaction_id}
        return await self._http_client.post(
            "/inquiry",
            json_data=data,
            base_url="https://api.fyers.in/api/v2",
        )
    
    # ==================== Rate Limit Info ====================
    
    def get_rate_limit_status(self) -> Dict[str, Any]:
        """
        Get current rate limit status.
        
        Returns:
            Rate limit summary
        """
        return self._rate_limiter.get_summary()
    
    def get_remaining_daily_calls(self) -> int:
        """
        Get remaining daily API calls.
        
        Returns:
            Number of remaining calls
        """
        return self._rate_limiter.get_remaining_daily_calls()
    
    def is_daily_limit_reached(self) -> bool:
        """
        Check if daily rate limit reached.
        
        Returns:
            True if limit reached
        """
        return self._rate_limiter.is_daily_limit_reached()
    
    # ==================== WebSocket Support ====================
    
    def create_order_websocket(
        self,
        on_order: Optional[Callable[[OrderUpdate], Any]] = None,
        on_trade: Optional[Callable[[TradeUpdate], Any]] = None,
        on_position: Optional[Callable[[PositionUpdate], Any]] = None,
        on_general: Optional[Callable[[GeneralUpdate], Any]] = None,
        on_error: Optional[Callable[[Dict[str, Any]], Any]] = None,
        on_connect: Optional[Callable[[], Any]] = None,
        on_close: Optional[Callable[[Dict[str, Any]], Any]] = None,
        config: Optional[WebSocketConfig] = None,
    ) -> FyersOrderWebSocket:
        """
        Create an Order WebSocket instance for real-time order/trade/position updates.
        
        Requires authentication before calling this method.
        
        Args:
            on_order: Callback for order updates
            on_trade: Callback for trade updates
            on_position: Callback for position updates
            on_general: Callback for general updates (eDIS, alerts, etc.)
            on_error: Callback for errors
            on_connect: Callback when connected
            on_close: Callback when connection closes
            config: WebSocket configuration
            
        Returns:
            FyersOrderWebSocket instance
            
        Example:
            ```python
            async def handle_order(order: OrderUpdate):
                print(f"Order {order.id}: {order.status_name}")
            
            ws = client.create_order_websocket(on_order=handle_order)
            await ws.connect()
            await ws.subscribe_orders()
            await ws.keep_running()
            ```
        """
        self._ensure_authenticated()
        
        access_token = self._get_full_access_token()
        
        return FyersOrderWebSocket(
            access_token=access_token,
            on_order=on_order,
            on_trade=on_trade,
            on_position=on_position,
            on_general=on_general,
            on_error=on_error,
            on_connect=on_connect,
            on_close=on_close,
            config=config,
        )
    
    def create_data_websocket(
        self,
        on_message: Optional[Callable[[Union[SymbolUpdate, DepthUpdate, IndexUpdate]], Any]] = None,
        on_error: Optional[Callable[[Dict[str, Any]], Any]] = None,
        on_connect: Optional[Callable[[], Any]] = None,
        on_close: Optional[Callable[[Dict[str, Any]], Any]] = None,
        config: Optional[WebSocketConfig] = None,
    ) -> FyersDataWebSocket:
        """
        Create a Data WebSocket instance for real-time market data.
        
        Requires authentication before calling this method.
        Supports up to 5000 symbol subscriptions.
        
        Args:
            on_message: Callback for market data updates
            on_error: Callback for errors
            on_connect: Callback when connected
            on_close: Callback when connection closes
            config: WebSocket configuration (set lite_mode=True for LTP only)
            
        Returns:
            FyersDataWebSocket instance
            
        Example:
            ```python
            async def handle_tick(data: SymbolUpdate):
                print(f"{data.symbol}: {data.ltp} ({data.chp}%)")
            
            ws = client.create_data_websocket(on_message=handle_tick)
            await ws.connect()
            await ws.subscribe(["NSE:SBIN-EQ", "NSE:INFY-EQ"])
            await ws.keep_running()
            ```
        """
        self._ensure_authenticated()
        
        access_token = self._get_full_access_token()
        
        return FyersDataWebSocket(
            access_token=access_token,
            on_message=on_message,
            on_error=on_error,
            on_connect=on_connect,
            on_close=on_close,
            config=config,
        )
    
    def create_order_websocket_sync(
        self,
        on_order: Optional[Callable[[Dict[str, Any]], Any]] = None,
        on_trade: Optional[Callable[[Dict[str, Any]], Any]] = None,
        on_position: Optional[Callable[[Dict[str, Any]], Any]] = None,
        on_general: Optional[Callable[[Dict[str, Any]], Any]] = None,
        on_error: Optional[Callable[[Dict[str, Any]], Any]] = None,
        on_connect: Optional[Callable[[], Any]] = None,
        on_close: Optional[Callable[[Dict[str, Any]], Any]] = None,
        config: Optional[WebSocketConfig] = None,
    ) -> FyersOrderWebSocketSync:
        """
        Create a synchronous Order WebSocket instance.
        
        For use cases where async is not needed.
        
        Args:
            on_order: Callback for order updates (raw dict)
            on_trade: Callback for trade updates (raw dict)
            on_position: Callback for position updates (raw dict)
            on_general: Callback for general updates (raw dict)
            on_error: Callback for errors
            on_connect: Callback when connected
            on_close: Callback when connection closes
            config: WebSocket configuration
            
        Returns:
            FyersOrderWebSocketSync instance
        """
        self._ensure_authenticated()
        
        access_token = self._get_full_access_token()
        
        return FyersOrderWebSocketSync(
            access_token=access_token,
            on_order=on_order,
            on_trade=on_trade,
            on_position=on_position,
            on_general=on_general,
            on_error=on_error,
            on_connect=on_connect,
            on_close=on_close,
            config=config,
        )
    
    def create_data_websocket_sync(
        self,
        on_message: Optional[Callable[[Dict[str, Any]], Any]] = None,
        on_error: Optional[Callable[[Dict[str, Any]], Any]] = None,
        on_connect: Optional[Callable[[], Any]] = None,
        on_close: Optional[Callable[[Dict[str, Any]], Any]] = None,
        config: Optional[WebSocketConfig] = None,
    ) -> FyersDataWebSocketSync:
        """
        Create a synchronous Data WebSocket instance.
        
        For use cases where async is not needed.
        
        Args:
            on_message: Callback for market data (raw dict)
            on_error: Callback for errors
            on_connect: Callback when connected
            on_close: Callback when connection closes
            config: WebSocket configuration
            
        Returns:
            FyersDataWebSocketSync instance
        """
        self._ensure_authenticated()
        
        access_token = self._get_full_access_token()
        
        return FyersDataWebSocketSync(
            access_token=access_token,
            on_message=on_message,
            on_error=on_error,
            on_connect=on_connect,
            on_close=on_close,
            config=config,
        )
    
    def create_tbt_websocket(
        self,
        on_depth_update: Optional[Callable[[TBTDepth], Any]] = None,
        on_error: Optional[Callable[[Dict[str, Any]], Any]] = None,
        on_error_message: Optional[Callable[[str], Any]] = None,
        on_connect: Optional[Callable[[], Any]] = None,
        on_close: Optional[Callable[[Dict[str, Any]], Any]] = None,
        config: Optional[TBTConfig] = None,
    ) -> FyersTBTWebSocket:
        """
        Create a TBT (Tick-by-Tick) WebSocket instance for 50-level market depth.
        
        Provides real-time 50-level market depth data for NFO and NSE instruments.
        
        Rate Limits:
        - Max 3 active connections per app per user
        - Max 5 symbols per connection
        - Max 50 channels per connection
        
        Args:
            on_depth_update: Callback for 50-level depth updates
            on_error: Callback for WebSocket errors
            on_error_message: Callback for server error messages
            on_connect: Callback when connected
            on_close: Callback when connection closes
            config: TBT WebSocket configuration
            
        Returns:
            FyersTBTWebSocket instance
            
        Example:
            ```python
            async def handle_depth(depth: TBTDepth):
                print(f"{depth.symbol}: TBQ={depth.total_buy_qty}, TSQ={depth.total_sell_qty}")
                print(f"Best Bid: {depth.best_bid.price}, Best Ask: {depth.best_ask.price}")
            
            ws = client.create_tbt_websocket(on_depth_update=handle_depth)
            await ws.connect()
            await ws.subscribe(
                symbols=["NSE:NIFTY25MARFUT", "NSE:BANKNIFTY25MARFUT"],
                channel="1",
            )
            await ws.switch_channel(resume=["1"])
            await ws.keep_running()
            ```
        """
        self._ensure_authenticated()
        
        access_token = self._get_full_access_token()
        
        return FyersTBTWebSocket(
            access_token=access_token,
            on_depth_update=on_depth_update,
            on_error=on_error,
            on_error_message=on_error_message,
            on_connect=on_connect,
            on_close=on_close,
            config=config,
        )
    
    def create_tbt_websocket_sync(
        self,
        on_depth_update: Optional[Callable[[str, Any], Any]] = None,
        on_error: Optional[Callable[[Dict[str, Any]], Any]] = None,
        on_error_message: Optional[Callable[[str], Any]] = None,
        on_connect: Optional[Callable[[], Any]] = None,
        on_close: Optional[Callable[[Dict[str, Any]], Any]] = None,
        config: Optional[TBTConfig] = None,
    ) -> FyersTBTWebSocketSync:
        """
        Create a synchronous TBT WebSocket instance.
        
        For use cases where async is not needed.
        
        Args:
            on_depth_update: Callback for depth updates (ticker, Depth)
            on_error: Callback for errors
            on_error_message: Callback for server error messages
            on_connect: Callback when connected
            on_close: Callback when connection closes
            config: TBT WebSocket configuration
            
        Returns:
            FyersTBTWebSocketSync instance
        """
        self._ensure_authenticated()
        
        access_token = self._get_full_access_token()
        
        return FyersTBTWebSocketSync(
            access_token=access_token,
            on_depth_update=on_depth_update,
            on_error=on_error,
            on_error_message=on_error_message,
            on_connect=on_connect,
            on_close=on_close,
            config=config,
        )
    
    def _get_full_access_token(self) -> str:
        """
        Get the full access token in the format required for WebSocket.
        
        Returns:
            Access token in format "client_id:access_token"
        """
        # Get the raw access token from HTTP client
        raw_token = self._http_client._access_token
        
        if not raw_token:
            raise FyersAuthenticationError("No access token available")
        
        # If already in full format, return as is
        if ":" in raw_token and raw_token.startswith(self.config.client_id):
            return raw_token
        
        # Otherwise, prepend client_id
        return f"{self.config.client_id}:{raw_token}"
    
    @property
    def access_token(self) -> Optional[str]:
        """
        Get the current access token.
        
        Returns:
            Access token or None if not authenticated
        """
        if self._is_authenticated and self._http_client._access_token:
            return self._get_full_access_token()
        return None
    
    # ==================== Utility Methods ====================
    
    def _ensure_authenticated(self) -> None:
        """Ensure the client is authenticated."""
        if not self._is_authenticated:
            raise FyersAuthenticationError(
                "Client is not authenticated. Call authenticate() first."
            )
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self.load_saved_token()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        # Persist rate limit state on exit
        self._rate_limiter.force_persist()


# Factory function for easy client creation
def create_client(
    client_id: str,
    secret_key: str,
    redirect_uri: str = "https://trade.fyers.in/api-login/redirect-uri/index.html",
    token_file: Optional[str] = None,
    rate_limit_file: Optional[str] = None,
) -> FyersClient:
    """
    Create a FyersClient with minimal configuration.
    
    Args:
        client_id: Fyers app ID
        secret_key: Fyers app secret
        redirect_uri: OAuth redirect URI
        token_file: Optional file path for token storage
        rate_limit_file: Optional file path for rate limit persistence
        
    Returns:
        Configured FyersClient instance
    """
    config = FyersConfig(
        client_id=client_id,
        secret_key=secret_key,
        redirect_uri=redirect_uri,
        token_file_path=token_file,
        rate_limit_file_path=rate_limit_file,
    )
    
    return FyersClient(config)