"""
Main Fyers client class.

This is the main entry point for the Fyers SDK.
"""

from typing import Any, Callable, Dict, List, Optional, Union
import asyncio

from broker.fyers.core.exceptions import (
    FyersException,
    FyersAuthenticationError,
    FyersTokenNotFoundError,
)
from broker.fyers.models.enums import (
    Exchange,
    Segment,
    OrderSide,
    OrderType,
    OrderStatus,
    PositionSide,
)
from broker.fyers.models.responses import (
    ProfileResponse,
    ProfileData,
    FundsResponse,
    HoldingsResponse,
    OrdersResponse,
    PositionsResponse,
    TradesResponse,
    HistoryResponse,
    OrderPlacementResponse,
    MultiOrderResponse,
    OrderModifyResponse,
    OrderCancelResponse,
    LogoutResponse,
    GenericResponse,
    QuotesResponse,
    MarketDepthResponse,
    MarketStatusResponse,
    MarginResponse,
    GTTOrdersResponse,
    OptionChainResponse,
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
from broker.fyers.utils.greeks import (
    compute_option_chain_greeks,
    DEFAULT_RISK_FREE_RATE,
)

logger = get_logger("fyers.client")


class FyersClient:
    """
    Main client for interacting with the Fyers API.
    
    Provides:
    - Smart OAuth authentication flow with token persistence
    - Automatic token loading and refresh
    - Rate-limited API requests
    - Comprehensive logging
    - Both async and sync interfaces
    
    Quick Start (Recommended):
        ```python
        from broker.fyers import create_client
        
        # One-liner setup with auto-authentication
        client = create_client(
            client_id="TX4LY7JMLL-100",
            secret_key="YOUR_SECRET",
            token_file="fyers_token.json",
            auto_authenticate=True,
        )
        
        # Make API calls
        import asyncio
        quotes = asyncio.run(client.get_quotes(["NSE:SBIN-EQ"]))
        ```
    
    Standard Setup:
        ```python
        from broker.fyers import FyersClient, FyersConfig
        
        config = FyersConfig(
            client_id="TX4LY7JMLL-100",
            secret_key="YOUR_SECRET",
            redirect_uri="http://127.0.0.1:9000/",
            token_file_path="fyers_token.json",
        )
        
        client = FyersClient(config)
        
        # Smart authenticate - uses saved token if available,
        # opens browser for login if needed
        await client.authenticate()
        
        # Now make API calls
        quotes = await client.get_quotes(["NSE:SBIN-EQ"])
        ```
    
    Authentication Scenarios:
        ```python
        # Scenario 1: Token already saved - instantly authenticated!
        await client.authenticate()
        
        # Scenario 2: Token expired, refresh it
        await client.authenticate(refresh_pin="1234")
        
        # Scenario 3: No token, auto-opens browser for login
        await client.authenticate()
        
        # Scenario 4: No token, manual OAuth flow
        await client.authenticate(auto_browser=False)
        # Then manually: await client.authenticate(redirect_url="...")
        
        # Sync version for non-async code
        client.authenticate_sync()
        ```
    
    Async Context Manager:
        ```python
        async with FyersClient(config) as client:
            # Token loaded automatically if available
            if client.is_authenticated:
                quotes = await client.get_quotes(["NSE:SBIN-EQ"])
            else:
                await client.authenticate()
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
        self._user_profile: Optional[ProfileData] = None
        
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
        redirect_url: Optional[str] = None,
        verify_state: bool = True,
        refresh_pin: Optional[str] = None,
        auto_browser: bool = True,
    ) -> TokenData:
        """
        Smart authentication that tries multiple strategies.
        
        This is the main authentication method that handles all scenarios:
        1. If a valid token exists in storage, uses it immediately
        2. If token is expired but refresh_token exists, tries to refresh (requires PIN)
        3. If redirect_url is provided, uses it for OAuth flow
        4. If auto_browser=True, opens browser for OAuth flow automatically
        5. Falls back to manual OAuth if nothing else works
        
        Args:
            redirect_url: Optional redirect URL from OAuth callback.
                         If not provided, will try saved token first.
            verify_state: Whether to verify OAuth state parameter
            refresh_pin: PIN for refreshing expired tokens (required for refresh)
            auto_browser: If True and no token exists, automatically opens
                         browser for OAuth flow (default: True)
            
        Returns:
            TokenData with access token
            
        Raises:
            FyersAuthenticationError: If all authentication strategies fail
            
        Example:
            ```python
            # Scenario 1: Token already saved (best case - just works!)
            await client.authenticate()  # Uses saved token
            
            # Scenario 2: Token expired, refresh it
            await client.authenticate(refresh_pin="1234")
            
            # Scenario 3: No token, automatic browser login
            await client.authenticate()  # Opens browser automatically
            
            # Scenario 4: Manual OAuth flow
            await client.authenticate(redirect_url="http://...?auth_code=...")
            ```
        """
        # Strategy 1: Try to load existing valid token
        if await self._try_load_saved_token():
            logger.info("Using existing valid token from storage")
            return await self._token_manager.get_token()
        
        # Strategy 2: Try to refresh expired token (if PIN provided)
        if refresh_pin:
            try:
                token_data = await self._try_refresh_token(refresh_pin)
                if token_data:
                    logger.info("Successfully refreshed expired token")
                    return token_data
            except Exception as e:
                logger.warning(f"Token refresh failed: {e}")
        
        # Strategy 3: Use provided redirect URL for OAuth
        if redirect_url:
            token_data = await self._oauth.authenticate_with_redirect(
                redirect_url,
                verify_state,
            )
            self._http_client.set_access_token(token_data.access_token)
            self._is_authenticated = True
            logger.info("Successfully authenticated via redirect URL")
            return token_data
        
        # Strategy 4: Automatic browser-based OAuth
        if auto_browser:
            logger.info("No valid token found, starting browser-based OAuth flow")
            return await self.authenticate_with_callback_server()
        
        # Strategy 5: Manual authentication required
        raise FyersAuthenticationError(
            "No valid token found and auto_browser=False. "
            "Either provide a redirect_url, enable auto_browser, "
            "or ensure token file contains a valid token."
        )
    
    async def _try_load_saved_token(self, validate_with_api: bool = True) -> bool:
        """
        Try to load a saved token and set it as active.
        
        Optionally validates the token by making a Profile API call
        to ensure it actually works (not just non-expired).
        
        Args:
            validate_with_api: If True, validates token with Profile API call.
                              This ensures the token is actually usable,
                              not just that it hasn't expired locally.
        
        Returns:
            True if valid token was loaded and set
        """
        try:
            token_data = await self._token_manager.get_token()
            
            if not token_data:
                logger.debug("No token found in storage")
                return False
            
            # Check local expiry first (fast check)
            if token_data.is_expired():
                logger.debug("Token is expired (local check)")
                return False
            
            # Set token temporarily to make validation call
            self._http_client.set_access_token(token_data.access_token)
            
            # Validate with Profile API if requested
            if validate_with_api:
                try:
                    profile_response = await self._http_client.get("/profile")
                    
                    # Parse the response
                    parsed = ProfileResponse(**profile_response)
                    
                    if not parsed.is_success():
                        logger.warning(f"Token validation failed: {parsed.message}")
                        self._http_client.clear_access_token()
                        return False
                    
                    # Cache user profile for convenience methods
                    if parsed.data:
                        self._user_profile = parsed.data
                        logger.info(f"Token validated for user: {parsed.data.name} ({parsed.data.fy_id})")
                    
                except Exception as e:
                    logger.warning(f"Token validation API call failed: {e}")
                    self._http_client.clear_access_token()
                    return False
            
            self._is_authenticated = True
            return True
            
        except FyersTokenNotFoundError:
            return False
        except Exception as e:
            logger.debug(f"Error loading saved token: {e}")
            return False
    
    async def _try_refresh_token(self, pin: str) -> Optional[TokenData]:
        """
        Try to refresh an expired token.
        
        Args:
            pin: User's PIN for refresh
            
        Returns:
            New TokenData if refresh successful, None otherwise
        """
        try:
            # Load token even if expired to get refresh_token
            token = await self._token_storage.load_token()
            
            if not token or not token.refresh_token:
                logger.debug("No refresh token available")
                return None
            
            token_data = await self._oauth.refresh_access_token(
                token.refresh_token,
                pin,
            )
            
            self._http_client.set_access_token(token_data.access_token)
            self._is_authenticated = True
            
            return token_data
            
        except Exception as e:
            logger.warning(f"Token refresh failed: {e}")
            return None
    
    async def authenticate_with_redirect(
        self,
        redirect_url: str,
        verify_state: bool = True,
    ) -> TokenData:
        """
        Complete authentication using the redirect URL directly.
        
        This is a lower-level method. Most users should use authenticate() instead.
        
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
        
        This is automatically called when using the async context manager.
        Most users should use authenticate() which handles this automatically.
        
        Returns:
            True if valid token was loaded
        """
        return await self._try_load_saved_token()
    
    async def ensure_authenticated(
        self,
        refresh_pin: Optional[str] = None,
        auto_browser: bool = True,
    ) -> TokenData:
        """
        Ensure the client is authenticated, loading or refreshing token as needed.
        
        Convenience method that calls authenticate() with sensible defaults.
        This is the recommended way to ensure authentication in scripts.
        
        Args:
            refresh_pin: Optional PIN for token refresh
            auto_browser: Whether to auto-open browser if no token exists
            
        Returns:
            TokenData with access token
            
        Example:
            ```python
            # One-liner to ensure authentication
            token = await client.ensure_authenticated()
            
            # With refresh capability
            token = await client.ensure_authenticated(refresh_pin="1234")
            ```
        """
        return await self.authenticate(
            refresh_pin=refresh_pin,
            auto_browser=auto_browser,
        )
    
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
    
    # ==================== User Info Properties ====================
    
    @property
    def user_profile(self) -> Optional[ProfileData]:
        """
        Get the cached user profile data.
        
        This is populated automatically when:
        - Token is validated during authentication
        - get_profile_typed() is called
        
        Returns:
            ProfileData if available, None otherwise
            
        Example:
            ```python
            if client.user_profile:
                print(f"Hello, {client.user_profile.name}!")
            ```
        """
        return self._user_profile
    
    @property
    def user_name(self) -> Optional[str]:
        """
        Get the authenticated user's name.
        
        Returns:
            User's name if authenticated and profile loaded, None otherwise
        """
        return self._user_profile.name if self._user_profile else None
    
    @property
    def user_id(self) -> Optional[str]:
        """
        Get the authenticated user's Fyers ID (fy_id).
        
        Returns:
            Fyers ID if authenticated and profile loaded, None otherwise
        """
        return self._user_profile.fy_id if self._user_profile else None
    
    @property
    def user_email(self) -> Optional[str]:
        """
        Get the authenticated user's email.
        
        Returns:
            Email if authenticated and profile loaded, None otherwise
        """
        return self._user_profile.email_id if self._user_profile else None
    
    # ==================== Market Data APIs ====================
    
    async def get_quotes(self, symbols: List[str]) -> QuotesResponse:
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
            QuotesResponse object
        """
        self._ensure_authenticated()
        
        # Use data API endpoint for quotes
        params = {"symbols": ",".join(symbols)}
        response = await self._http_client.get(
            "/quotes",
            params=params,
            base_url="https://api-t1.fyers.in/data",
        )
        return QuotesResponse(**response)
    
    async def get_market_depth(
        self,
        symbol: str,
        ohlcv_flag: int = 1,
    ) -> MarketDepthResponse:
        """
        Get complete market depth for a symbol.
        
        Returns bid/ask prices with volume and order count,
        OHLCV data, circuit limits, and open interest.
        
        Args:
            symbol: Symbol to get depth for (e.g., "NSE:SBIN-EQ")
            ohlcv_flag: Include OHLCV data (1=yes, 0=no)
            
        Returns:
            MarketDepthResponse object with market depth data including:
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
        response = await self._http_client.get(
            "/depth",
            params=params,
            base_url="https://api-t1.fyers.in/data",
        )
        return MarketDepthResponse(**response)
    
    async def get_history(
        self,
        symbol: str,
        resolution: str,
        date_format: int,
        range_from: str,
        range_to: str,
        cont_flag: int = 0,
        oi_flag: int = 0,
    ) -> HistoryResponse:
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
            HistoryResponse object (use .dataframe property for DataFrame)
            
        Example:
            ```python
            # Get typed response
            history = await client.get_history(
                symbol="NSE:SBIN-EQ",
                resolution="5",
                date_format=1,
                range_from="2024-01-01",
                range_to="2024-01-31",
            )
            
            # Use raw data
            print(f"Got {len(history.candles)} candles")
            
            # Or convert to DataFrame
            df = history.dataframe
            print(df[['datetime', 'open', 'high', 'low', 'close']])
            ```
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
        
        response = await self._http_client.get(
            "/history",
            params=params,
            base_url="https://api-t1.fyers.in/data",
        )
        
        return HistoryResponse(**response)
    
    async def get_option_chain(
        self,
        symbol: str,
        strike_count: int = 10,
        timestamp: Optional[str] = None,
    ) -> OptionChainResponse:
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
            OptionChainResponse object (use .dataframe property for DataFrame)
            
        Example:
            ```python
            # Get typed response
            oc = await client.get_option_chain("NSE:NIFTY50-INDEX", strike_count=5)
            
            # Use response methods
            print(f"Call OI: {oc.get_call_oi()}, Put OI: {oc.get_put_oi()}")
            
            # Convert to DataFrame when needed
            df = oc.dataframe
            print(df[['symbol', 'strike_price', 'option_type', 'ltp', 'oi']])
            ```
        """
        self._ensure_authenticated()
        
        params = {
            "symbol": symbol,
            "strikecount": strike_count,
        }
        
        if timestamp:
            params["timestamp"] = timestamp
        
        response = await self._http_client.get(
            "/options-chain-v3",
            params=params,
            base_url="https://api-t1.fyers.in/data",
        )
        
        return OptionChainResponse(**response)

    async def get_option_greeks(
        self,
        symbol: str,
        strike_count: int = 10,
        risk_free_rate: float = DEFAULT_RISK_FREE_RATE,
    ) -> List[Dict[str, Any]]:
        """
        Get option chain with computed Greeks (IV, Delta, Gamma, Theta, Vega, Rho).

        Uses Black-Scholes model for European-style options.

        Args:
            symbol: Underlying symbol (e.g., "NSE:NIFTY50-INDEX", "NSE:SBIN-EQ")
            strike_count: Number of strikes to return (max 50)
            risk_free_rate: Annual risk-free rate (decimal, default ~6.5% for India)

        Returns:
            List of dictionaries with option data and computed Greeks:
            - symbol, strike, option_type, expiry_epoch
            - time_to_expiry_years, time_to_expiry_days
            - spot, ltp, iv (percentage)
            - delta, gamma, theta (per day), vega (per 1%), rho (per 1%)
            - oi, volume, bid, ask

        Example:
            ```python
            greeks = await client.get_option_greeks("NSE:NIFTY50-INDEX", strike_count=5)
            for opt in greeks:
                print(f"{opt['symbol']}: IV={opt['iv']}%, Delta={opt['delta']}")
            ```
        """
        self._ensure_authenticated()

        # Get option chain
        option_chain = await self.get_option_chain(symbol, strike_count=strike_count)

        # Get spot price
        quotes = await self.get_quotes([symbol])
        spot_price = None

        if quotes.d:
            for quote in quotes.d:
                # quote.v is a dict, not a pydantic model
                if quote.v and quote.v.get('lp'):
                    spot_price = quote.v.get('lp')
                    break

        if spot_price is None:
            raise FyersException(f"Could not get spot price for {symbol}")

        # Extract nearest expiry from expiryData (options don't have expiry field)
        nearest_expiry = None
        if option_chain.data:
            expiry_data = option_chain.data.get('expiryData', [])
            if expiry_data:
                # First entry is the nearest expiry
                nearest_expiry = expiry_data[0].get('expiry')

        # Prepare option chain data for Greeks computation
        options_data = []
        # Use helper method since option_chain.data is a dict
        for opt in option_chain.get_options_chain():
            # Skip underlying (no option_type)
            if not opt.get("option_type"):
                continue

            options_data.append({
                "symbol": opt.get("symbol"),
                "strike_price": opt.get("strike_price"),
                "option_type": opt.get("option_type"),
                "expiry": nearest_expiry,  # Use extracted expiry
                "ltp": opt.get("ltp"),
                "bid": opt.get("bid"),
                "ask": opt.get("ask"),
                "oi": opt.get("oi"),
                "volume": opt.get("volume"),
            })

        # Compute Greeks
        return compute_option_chain_greeks(
            options_data,
            spot_price,
            risk_free_rate=risk_free_rate,
        )

    # ==================== Order APIs ====================
    
    async def place_order(self, order_data: Dict[str, Any]) -> OrderPlacementResponse:
        """
        Place a single order.
        
        Args:
            order_data: Order parameters
            
        Returns:
            OrderPlacementResponse object
        """
        self._ensure_authenticated()
        response = await self._http_client.post("/orders/sync", json_data=order_data)
        return OrderPlacementResponse(**response)
    
    async def place_multi_order(
        self,
        orders: List[Dict[str, Any]],
    ) -> MultiOrderResponse:
        """
        Place multiple orders (Basket Order).
        
        Args:
            orders: List of order data dictionaries
            
        Returns:
            MultiOrderResponse object
        """
        self._ensure_authenticated()
        response = await self._http_client.post("/multi-order/sync", json_data=orders)
        return MultiOrderResponse(**response)
    
    # Alias for compatibility with official SDK naming
    place_basket_orders = place_multi_order
    
    async def modify_order(
        self,
        order_id: str,
        modifications: Dict[str, Any],
    ) -> OrderModifyResponse:
        """
        Modify an existing order.
        
        Args:
            order_id: Order ID to modify
            modifications: Modifications to apply
            
        Returns:
            OrderModifyResponse object
        """
        self._ensure_authenticated()
        
        data = {"id": order_id, **modifications}
        response = await self._http_client.patch("/orders/sync", json_data=data)
        return OrderModifyResponse(**response)
    
    async def cancel_order(self, order_id: str) -> OrderCancelResponse:
        """
        Cancel an order.
        
        Args:
            order_id: Order ID to cancel
            
        Returns:
            OrderCancelResponse object
        """
        self._ensure_authenticated()
        
        data = {"id": order_id}
        response = await self._http_client.delete("/orders/sync", json_data=data)
        return OrderCancelResponse(**response)
    
    async def get_orders(self) -> OrdersResponse:
        """
        Get all orders for the day.
        
        Returns:
            OrdersResponse object
        """
        self._ensure_authenticated()
        response = await self._http_client.get("/orders")
        return OrdersResponse(**response)
    
    async def get_order_by_id(self, order_id: str) -> OrdersResponse:
        """
        Get details for a specific order.
        
        Args:
            order_id: Order ID
            
        Returns:
            OrdersResponse object with order details
        """
        self._ensure_authenticated()
        # API uses query parameter, not path parameter
        response = await self._http_client.get("/orders", params={"id": order_id})
        return OrdersResponse(**response)
    
    # ==================== Position APIs ====================
    
    async def get_positions(self) -> PositionsResponse:
        """
        Get all positions.
        
        Returns:
            PositionsResponse object
        """
        self._ensure_authenticated()
        response = await self._http_client.get("/positions")
        return PositionsResponse(**response)
    
    async def exit_position(
        self,
        position_id: Optional[str] = None,
    ) -> GenericResponse:
        """
        Exit position(s).
        
        Args:
            position_id: Specific position to exit (None = exit all)
            
        Returns:
            GenericResponse object
        """
        self._ensure_authenticated()
        
        if position_id:
            data = {"id": position_id}
        else:
            data = {}
            
        response = await self._http_client.delete("/positions", json_data=data)
        return GenericResponse(**response)
    
    async def convert_position(
        self,
        conversion_data: Dict[str, Any],
    ) -> GenericResponse:
        """
        Convert position from one product to another.
        
        Args:
            conversion_data: Conversion parameters
            
        Returns:
            GenericResponse object
        """
        self._ensure_authenticated()
        response = await self._http_client.post("/positions", json_data=conversion_data)
        return GenericResponse(**response)
    
    # ==================== Portfolio APIs ====================
    
    async def get_holdings(self) -> HoldingsResponse:
        """
        Get portfolio holdings.
        
        Returns:
            HoldingsResponse object
        """
        self._ensure_authenticated()
        response = await self._http_client.get("/holdings")
        return HoldingsResponse(**response)
    
    async def get_funds(self) -> FundsResponse:
        """
        Get available funds.
        
        Returns:
            FundsResponse object
        """
        self._ensure_authenticated()
        response = await self._http_client.get("/funds")
        return FundsResponse(**response)
    
    # ==================== User Profile APIs ====================
    
    async def get_profile(self) -> ProfileResponse:
        """
        Get user profile.
        
        Returns:
            ProfileResponse with user profile data
            
        Example:
            ```python
            profile = await client.get_profile()
            if profile.is_success():
                print(f"Name: {profile.data.name}")
                print(f"Fyers ID: {profile.data.fy_id}")
                print(f"Email: {profile.data.email_id}")
            ```
        """
        self._ensure_authenticated()
        
        response = await self._http_client.get("/profile")
        parsed = ProfileResponse(**response)
        
        # Cache profile data
        if parsed.is_success() and parsed.data:
            self._user_profile = parsed.data
        
        return parsed
    
    async def get_tradebook(self) -> TradesResponse:
        """
        Get trade book for the day.
        
        Returns:
            TradesResponse object
        """
        self._ensure_authenticated()
        response = await self._http_client.get("/tradebook")
        return TradesResponse(**response)
    
    async def get_tradebook_by_tag(self, order_tag: str) -> TradesResponse:
        """
        Get trade book filtered by order tag.
        
        Args:
            order_tag: Order tag to filter by
            
        Returns:
            Filtered trade book data
        """
        self._ensure_authenticated()
        response = await self._http_client.get(
            "/tradebook",
            params={"order_tag": order_tag}
        )
        return TradesResponse(**response)
    
    async def get_orders_by_tag(self, order_tag: str) -> OrdersResponse:
        """
        Get orders filtered by order tag.
        
        Args:
            order_tag: Order tag to filter by
            
        Returns:
            Filtered orders list
        """
        self._ensure_authenticated()
        response = await self._http_client.get(
            "/orders",
            params={"order_tag": order_tag}
        )
        return OrdersResponse(**response)
    
    
    # ==================== Multi-Leg Orders ====================
    
    async def place_multileg_order(
        self,
        legs: Dict[str, Dict[str, Any]],
        product_type: str = "INTRADAY",
        order_type: str = "2L",
        validity: str = "IOC",
        offline_order: bool = False,
        order_tag: Optional[str] = None,
    ) -> OrderPlacementResponse:
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
            OrderPlacementResponse object
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
        
        response = await self._http_client.post("/multileg/orders/sync", json_data=data)
        return OrderPlacementResponse(**response)
    
    # ==================== Cancel Multiple Orders ====================
    
    async def cancel_multi_order(self, order_ids: List[str]) -> MultiOrderResponse:
        """
        Cancel multiple orders at once.
        
        Args:
            order_ids: List of order IDs to cancel
            
        Returns:
            MultiOrderResponse object
        """
        self._ensure_authenticated()
        
        orders = [{"id": order_id} for order_id in order_ids]
        # Using DELETE on /multi-order/sync as inferred from structure,
        # though official doc isn't explicit on the curl endpoint for basket cancel.
        response = await self._http_client.delete("/multi-order/sync", json_data=orders)
        return MultiOrderResponse(**response)
    
    # Alias for compatibility with official SDK naming
    cancel_basket_orders = cancel_multi_order
    
    # ==================== API Logout ====================
    
    async def api_logout(self) -> LogoutResponse:
        """
        Invalidate the access token via API.
        
        This invalidates the access token for this specific app only.
        
        Returns:
            LogoutResponse object
        """
        self._ensure_authenticated()
        
        response = await self._http_client.post("/logout")
        
        # Clear local auth state
        await self.logout()
        
        return LogoutResponse(**response)
    
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
    ) -> OrderPlacementResponse:
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
            OrderPlacementResponse object
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
        
        response = await self._http_client.post("/gtt/orders/sync", json_data=data)
        return OrderPlacementResponse(**response)
    
    async def modify_gtt_order(
        self,
        order_id: str,
        leg1_price: Optional[float] = None,
        leg1_trigger_price: Optional[float] = None,
        leg1_qty: Optional[int] = None,
        leg2_price: Optional[float] = None,
        leg2_trigger_price: Optional[float] = None,
        leg2_qty: Optional[int] = None,
    ) -> OrderModifyResponse:
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
            OrderModifyResponse object
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
        
        response = await self._http_client.request(
            "PATCH", "/gtt/orders/sync", json_data=data
        )
        return OrderModifyResponse(**response)
    
    async def cancel_gtt_order(self, order_id: str) -> OrderCancelResponse:
        """
        Cancel a pending GTT order.
        
        Args:
            order_id: GTT order ID to cancel
            
        Returns:
            OrderCancelResponse object
        """
        self._ensure_authenticated()
        
        data = {"id": order_id}
        response = await self._http_client.delete("/gtt/orders/sync", json_data=data)
        return OrderCancelResponse(**response)
    
    async def get_gtt_orders(self) -> GTTOrdersResponse:
        """
        Get all pending GTT orders.
        
        Returns:
            GTTOrdersResponse object
        """
        self._ensure_authenticated()
        response = await self._http_client.get("/gtt/orders")
        return GTTOrdersResponse(**response)
    
    # ==================== Modify Multi Orders ====================
    
    async def modify_multi_order(
        self,
        modifications: List[Dict[str, Any]],
    ) -> MultiOrderResponse:
        """
        Modify multiple orders at once (up to 10).
        
        Args:
            modifications: List of modification dictionaries.
                Each should have 'id' and fields to modify.
                
        Returns:
            MultiOrderResponse object
        """
        self._ensure_authenticated()
        # Official docs don't explicitly show the method for multi-order modify in curl samples,
        # but single order modify uses PATCH. Assuming PATCH for consistency.
        response = await self._http_client.request(
            "PATCH", "/multi-order/sync", json_data=modifications
        )
        return MultiOrderResponse(**response)
    
    # Alias for compatibility with official SDK naming
    modify_basket_orders = modify_multi_order
    
    # ==================== Exit Position Advanced ====================
    
    async def exit_positions_by_ids(self, position_ids: List[str]) -> GenericResponse:
        """
        Exit multiple positions by their IDs.
        
        Args:
            position_ids: List of position IDs to exit
            
        Returns:
            GenericResponse object
        """
        self._ensure_authenticated()
        
        data = {"id": position_ids}
        response = await self._http_client.delete("/positions", json_data=data)
        return GenericResponse(**response)
    
    async def exit_positions_by_segment(
        self,
        segments: List[Union[int, Segment]],
        sides: List[Union[int, OrderSide]],
        product_types: List[str],
    ) -> GenericResponse:
        """
        Exit positions by segment, side, and product type.
        
        Args:
            segments: List of segments (use Segment.CAPITAL_MARKET, Segment.EQUITY_DERIVATIVES, etc.)
            sides: List of sides (use OrderSide.BUY, OrderSide.SELL)
            product_types: List of product types (INTRADAY, CNC, etc.)
            
        Returns:
            GenericResponse object
            
        Example:
            ```python
            from broker.fyers.models.enums import Segment, OrderSide
            
            # Exit all buy positions in equity derivatives
            await client.exit_positions_by_segment(
                segments=[Segment.EQUITY_DERIVATIVES],
                sides=[OrderSide.BUY],
                product_types=["INTRADAY", "MARGIN"]
            )
            ```
        """
        self._ensure_authenticated()
        
        # Convert enums to integers
        segment_vals = [int(s) if isinstance(s, Segment) else s for s in segments]
        side_vals = [int(s) if isinstance(s, OrderSide) else s for s in sides]
        
        data = {
            "segment": segment_vals,
            "side": side_vals,
            "productType": product_types,
        }
        response = await self._http_client.delete("/positions", json_data=data)
        return GenericResponse(**response)
    
    async def exit_all_positions_with_pending_cancel(self) -> GenericResponse:
        """
        Exit all positions and cancel pending orders.
        
        Returns:
            GenericResponse object
        """
        self._ensure_authenticated()
        
        data = {"pending_orders_cancel": 1}
        response = await self._http_client.delete("/positions", json_data=data)
        return GenericResponse(**response)
    
    async def exit_position_with_pending_cancel(
        self,
        position_id: str,
    ) -> GenericResponse:
        """
        Exit a specific position and cancel its pending orders.
        
        Args:
            position_id: Position ID to exit
            
        Returns:
            GenericResponse object
        """
        self._ensure_authenticated()
        
        data = {
            "id": position_id,
            "pending_orders_cancel": 1,
        }
        response = await self._http_client.delete("/positions", json_data=data)
        return GenericResponse(**response)
    
    # ==================== Margin Calculator ====================
    
    async def calculate_span_margin(
        self,
        positions: List[Dict[str, Any]],
    ) -> MarginResponse:
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
            MarginResponse object with margin calculation
        """
        self._ensure_authenticated()
        
        data = {"data": positions}
        response = await self._http_client.post(
            "/span_margin",
            json_data=data,
            base_url="https://api.fyers.in/api/v2",
        )
        return MarginResponse(**response)
    
    async def calculate_order_margin(
        self,
        orders: List[Dict[str, Any]],
    ) -> MarginResponse:
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
            MarginResponse object with margin calculation
        """
        self._ensure_authenticated()
        
        data = {"data": orders}
        response = await self._http_client.post("/multiorder/margin", json_data=data)
        return MarginResponse(**response)
    
    # ==================== Market Status ====================
    
    async def get_market_status(self) -> MarketStatusResponse:
        """
        Get current market status for all exchanges and segments.
        
        Returns:
            MarketStatusResponse object with market status for each exchange/segment
        """
        self._ensure_authenticated()
        response = await self._http_client.get(
            "/marketStatus",
            base_url="https://api-t1.fyers.in/data"
        )
        return MarketStatusResponse(**response)
    
    # ==================== eDIS (Electronic Delivery Instruction Slip) ====================
    
    async def generate_edis_tpin(self) -> GenericResponse:
        """
        Generate TPIN for eDIS transactions.
        
        TPIN is an authorization code from CDSL/NSDL required to
        authorize sell transactions from demat account.
        
        Returns:
            GenericResponse object
        """
        self._ensure_authenticated()
        response = await self._http_client.get(
            "/tpin",
            base_url="https://api.fyers.in/api/v2",
        )
        return GenericResponse(**response)
    
    async def get_edis_details(self) -> GenericResponse:
        """
        Get eDIS authorization details.
        
        Returns information about holding authorizations that
        have been successfully completed.
        
        Returns:
            GenericResponse object with eDIS authorization details
        """
        self._ensure_authenticated()
        response = await self._http_client.get(
            "/details",
            base_url="https://api.fyers.in/api/v2",
        )
        return GenericResponse(**response)
    
    async def get_edis_index_page(
        self,
        holdings: List[Dict[str, Any]],
    ) -> GenericResponse:
        """
        Get the CDSL page for eDIS authorization.
        
        Args:
            holdings: List of holdings to authorize with:
                - isin_code: ISIN code of the holding
                - qty: Quantity to authorize
                - symbol: Symbol (e.g., "NSE:SAIL-EQ")
                
        Returns:
            GenericResponse object with HTML page content for CDSL authorization
        """
        self._ensure_authenticated()
        
        data = {"recordLst": holdings}
        response = await self._http_client.post(
            "/index",
            json_data=data,
            base_url="https://api.fyers.in/api/v2",
        )
        return GenericResponse(**response)
    
    async def check_edis_transaction_status(
        self,
        transaction_id: str,
    ) -> GenericResponse:
        """
        Check eDIS transaction status.
        
        Args:
            transaction_id: Base64 encoded transaction ID
                Example: For "915484108176", encode to "OTE1NDg0MTA4MTc2"
                
        Returns:
            GenericResponse object with transaction status
        """
        self._ensure_authenticated()
        
        data = {"transactionId": transaction_id}
        response = await self._http_client.post(
            "/inquiry",
            json_data=data,
            base_url="https://api.fyers.in/api/v2",
        )
        return GenericResponse(**response)
    
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
                "Client is not authenticated. "
                "Call 'await client.authenticate()' or 'client.authenticate_sync()' first.\n"
                "\nQuick fix options:\n"
                "  1. await client.authenticate()  # Opens browser if no saved token\n"
                "  2. client.authenticate_sync()   # Same, but synchronous\n"
                "  3. Use context manager: async with FyersClient(config) as client:\n"
                "\nIf you have a token file, ensure it contains a valid, non-expired token."
            )
    
    async def __aenter__(self):
        """
        Async context manager entry.
        
        Automatically tries to load saved token when entering context.
        If a valid token exists in storage, the client will be ready to use.
        """
        await self._try_load_saved_token(validate_with_api=True)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        # Persist rate limit state on exit
        self._rate_limiter.force_persist()
    
    # ==================== Synchronous Helpers ====================
    
    def authenticate_sync(
        self,
        redirect_url: Optional[str] = None,
        verify_state: bool = True,
        refresh_pin: Optional[str] = None,
        auto_browser: bool = True,
    ) -> TokenData:
        """
        Synchronous version of authenticate().
        
        Runs the async authenticate() in an event loop.
        Use this when you're not in an async context.
        
        Args:
            redirect_url: Optional redirect URL from OAuth callback
            verify_state: Whether to verify OAuth state parameter
            refresh_pin: PIN for refreshing expired tokens
            auto_browser: If True, auto-opens browser for OAuth flow
            
        Returns:
            TokenData with access token
            
        Example:
            ```python
            from broker.fyers import FyersClient, FyersConfig
            
            config = FyersConfig(
                client_id="YOUR_CLIENT_ID",
                secret_key="YOUR_SECRET",
                token_file_path="fyers_token.json"
            )
            
            client = FyersClient(config)
            
            # Simple sync authentication - just works!
            client.authenticate_sync()
            
            # Now make API calls (use sync wrappers or run async)
            import asyncio
            quotes = asyncio.run(client.get_quotes(["NSE:SBIN-EQ"]))
            ```
        """
        import asyncio
        
        try:
            loop = asyncio.get_running_loop()
            # We're in an async context, use nest_asyncio or create task
            raise RuntimeError(
                "authenticate_sync() cannot be called from an async context. "
                "Use 'await client.authenticate()' instead."
            )
        except RuntimeError:
            # No running loop, safe to use asyncio.run()
            return asyncio.run(
                self.authenticate(
                    redirect_url=redirect_url,
                    verify_state=verify_state,
                    refresh_pin=refresh_pin,
                    auto_browser=auto_browser,
                )
            )
    
    def ensure_authenticated_sync(
        self,
        refresh_pin: Optional[str] = None,
        auto_browser: bool = True,
    ) -> TokenData:
        """
        Synchronous version of ensure_authenticated().
        
        Args:
            refresh_pin: Optional PIN for token refresh
            auto_browser: Whether to auto-open browser if no token exists
            
        Returns:
            TokenData with access token
        """
        return self.authenticate_sync(
            refresh_pin=refresh_pin,
            auto_browser=auto_browser,
        )


# Factory function for easy client creation
def create_client(
    client_id: str,
    secret_key: str,
    redirect_uri: str = "http://127.0.0.1:9000/",
    token_file: Optional[str] = None,
    rate_limit_file: Optional[str] = None,
    auto_authenticate: bool = False,
    auto_init: bool = True,
) -> FyersClient:
    """
    Create a FyersClient with minimal configuration.
    
    This is the recommended way to create a client for quick scripts.
    
    Args:
        client_id: Fyers app ID (e.g., "TX4LY7JMLL-100")
        secret_key: Fyers app secret
        redirect_uri: OAuth redirect URI (default: localhost for easy local auth)
        token_file: Optional file path for token storage (strongly recommended!)
        rate_limit_file: Optional file path for rate limit persistence
        auto_authenticate: If True, calls authenticate_sync() immediately
            (opens browser if no valid token)
        auto_init: If True (default), tries to load saved token silently.
            If token exists and is valid, client is ready to use without
            calling authenticate(). No browser is opened.
        
    Returns:
        FyersClient instance (authenticated if auto_authenticate=True)
        
    Example (Scripts):
        ```python
        from broker.fyers import create_client
        
        # Simple! Just create and use (auto-authenticates)
        client = create_client(
            client_id="TX4LY7JMLL-100",
            secret_key="YOUR_SECRET",
            token_file="fyers_token.json",
        )
        
        # Client is ready! Make calls with asyncio.run()
        import asyncio
        quotes = asyncio.run(client.get_quotes(["NSE:SBIN-EQ"]))
        positions = asyncio.run(client.get_positions())
        ```
    
    Example (Jupyter Notebooks - use async API):
        ```python
        from broker.fyers import FyersClient, FyersConfig
        
        config = FyersConfig(
            client_id="TX4LY7JMLL-100",
            secret_key="YOUR_SECRET",
            token_file_path="fyers_token.json",
        )
        
        client = FyersClient(config)
        await client.authenticate()  # Use await!
        
        # Now make calls directly
        quotes = await client.get_quotes(["NSE:SBIN-EQ"])
        ```
    """
    config = FyersConfig(
        client_id=client_id,
        secret_key=secret_key,
        redirect_uri=redirect_uri,
        token_file_path=token_file,
        rate_limit_file_path=rate_limit_file,
    )
    
    client = FyersClient(config)
    
    # Auto-authenticate if requested
    if auto_authenticate:
        try:
            # Detect if we're in an async environment (e.g., Jupyter)
            try:
                asyncio.get_running_loop()
                # Running loop detected - print helpful message
                print("\n" + "="*60)
                print("📓 Jupyter Notebook Detected")
                print("="*60)
                print("Auto-authentication skipped to avoid blocking.")
                print("Please add one line after creating the client:\n")
                print("  await client.authenticate()\n")
                print("Full example:")
                print("  client = create_client(...)")
                print("  await client.authenticate()")
                print("  quotes = await client.get_quotes([...])")
                print("="*60 + "\n")
            except RuntimeError:
                # No running loop - safe to use sync auth
                client.authenticate_sync()
        except Exception as e:
            logger.warning(f"Auto-authentication failed: {e}")
    
    return client


async def create_client_async(
    client_id: str,
    secret_key: str,
    redirect_uri: str = "http://127.0.0.1:9000/",
    token_file: Optional[str] = None,
    rate_limit_file: Optional[str] = None,
) -> FyersClient:
    """
    Create and auto-authenticate a FyersClient (async version for Jupyter).
    
    This is the recommended way to use the SDK in Jupyter Notebooks.
    
    Args:
        client_id: Your Fyers app ID
        secret_key: Your Fyers app secret
        redirect_uri: OAuth redirect URI
        token_file: File path for token storage
        rate_limit_file: File path for rate limit persistence
        
    Returns:
        Authenticated FyersClient ready to use
        
    Example (Jupyter):
        ```python
        from broker.fyers import create_client_async
        
        client = await create_client_async(
            client_id="TX4LY7JMLL-100",
            secret_key="YOUR_SECRET",
            token_file="fyers_token.json",
        )
        
        # Ready to use!
        quotes = await client.get_quotes(["NSE:SBIN-EQ"])
        ```
    """
    config = FyersConfig(
        client_id=client_id,
        secret_key=secret_key,
        redirect_uri=redirect_uri,
        token_file_path=token_file,
        rate_limit_file_path=rate_limit_file,
    )
    
    client = FyersClient(config)
    await client.authenticate()  # Auto-authenticate
    
    return client


def create_client_from_env(
    token_file: Optional[str] = None,
    auto_authenticate: bool = False,
    auto_init: bool = True,
) -> FyersClient:
    """
    Create a FyersClient from environment variables.
    
    Required environment variables:
    - FYERS_CLIENT_ID: Your Fyers app ID
    - FYERS_SECRET_KEY: Your Fyers app secret
    
    Optional environment variables:
    - FYERS_REDIRECT_URI: OAuth redirect URI (default: http://127.0.0.1:9000/)
    - FYERS_TOKEN_FILE: Token file path (can be overridden by token_file arg)
    
    Args:
        token_file: Override for token file path (uses FYERS_TOKEN_FILE if None)
        auto_authenticate: If True, authenticates immediately
        auto_init: If True (default), tries to load saved token silently
        
    Returns:
        Configured FyersClient instance
        
    Raises:
        ValueError: If required environment variables are not set
        
    Example:
        ```bash
        # Set environment variables first
        export FYERS_CLIENT_ID="TX4LY7JMLL-100"
        export FYERS_SECRET_KEY="YOUR_SECRET"
        export FYERS_TOKEN_FILE="fyers_token.json"
        ```
        
        ```python
        from broker.fyers import create_client_from_env
        
        # Creates client from env vars - super clean!
        client = create_client_from_env()
        
        if client.is_authenticated:
            print(f"Hello, {client.user_name}!")
        else:
            client.authenticate_sync()
        ```
    """
    import os
    
    config = FyersConfig.from_env(token_file=token_file)
    
    client = FyersClient(config)
    
    # Try to load saved token silently
    effective_token_file = token_file or os.environ.get("FYERS_TOKEN_FILE")
    if auto_init and effective_token_file:
        try:
            asyncio.run(client._try_load_saved_token(validate_with_api=True))
        except Exception as e:
            logger.debug(f"Auto-init token load failed: {e}")
    
    # Full authentication if requested
    if auto_authenticate and not client.is_authenticated:
        client.authenticate_sync()
    
    return client