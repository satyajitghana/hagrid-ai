"""
Fyers Broker SDK

A Python SDK for interacting with the Fyers trading API.
Includes OAuth authentication, rate limiting, WebSocket support, and comprehensive logging.

Rate Limits:
- Per second: 10 requests
- Per minute: 200 requests
- Per day: 100,000 requests

WebSocket Features:
- Order updates (orders, trades, positions)
- Market data (symbol updates, depth updates, index updates)
- Up to 5000 symbol subscriptions
- Auto-reconnection support

Quick Start (Scripts):
    ```python
    from broker.fyers import create_client
    import asyncio
    
    # Simple! Just create and it auto-authenticates
    client = create_client(
        client_id="TX4LY7JMLL-100",
        secret_key="YOUR_SECRET",
        token_file="fyers_token.json",  # Saves/loads token
    )
    
    # Make API calls
    quotes = asyncio.run(client.get_quotes(["NSE:SBIN-EQ"]))
    positions = asyncio.run(client.get_positions())
    ```

Quick Start (Jupyter Notebooks):
    ```python
    from broker.fyers import create_client_async
    
    # One-liner for Jupyter! Auto-authenticates
    client = await create_client_async(
        client_id="TX4LY7JMLL-100",
        secret_key="YOUR_SECRET",
        token_file="fyers_token.json",
    )
    
    # Ready to use with await
    quotes = await client.get_quotes(["NSE:SBIN-EQ"])
    positions = await client.get_positions()
    ```

Environment Variables:
    ```python
    # Set: FYERS_CLIENT_ID, FYERS_SECRET_KEY
    from broker.fyers import create_client_from_env
    import asyncio
    
    client = create_client_from_env()
    quotes = asyncio.run(client.get_quotes(["NSE:SBIN-EQ"]))
    ```
"""

from broker.fyers.client import FyersClient, create_client, create_client_async, create_client_from_env
from broker.fyers.auth.oauth import FyersOAuth, interactive_login
from broker.fyers.auth.token_storage import (
    TokenStorage,
    FileTokenStorage,
    MemoryTokenStorage,
    TokenManager,
)
from broker.fyers.models.config import FyersConfig
from broker.fyers.models.auth import TokenData, AuthState
from broker.fyers.models.rate_limit import (
    RateLimitConfig,
    RateLimitState,
    RateLimitType,
)
from broker.fyers.models.orders import (
    SingleOrderRequest,
    ModifyOrderRequest,
    CancelOrderRequest,
    MultiLegOrderRequest,
    ConvertPositionRequest,
    create_market_order,
    create_limit_order,
    create_stop_order,
    create_stop_limit_order,
    create_bracket_order,
    create_cover_order,
    OrderType,
    OrderSide,
)
from broker.fyers.models.responses import (
    ProfileResponse,
    ProfileData,
    FundsResponse,
    HoldingsResponse,
    OrdersResponse,
    PositionsResponse,
    TradesResponse,
    OrderPlacementResponse,
    MultiOrderResponse,
)
from broker.fyers.data.symbol_master import (
    SymbolMaster,
    Symbol,
    ExchangeSegment,
)
from broker.fyers.webhooks.postback import (
    PostbackPayload,
    PostbackHandler,
    create_webhook_server,
)
from broker.fyers.core.exceptions import (
    FyersException,
    FyersAuthenticationError,
    FyersRateLimitError,
    FyersAPIError,
    FyersTokenExpiredError,
    FyersTokenNotFoundError,
    FyersNetworkError,
)
from broker.fyers.core.rate_limiter import RateLimiter
from broker.fyers.core.http_client import HTTPClient
from broker.fyers.core.logger import get_logger, configure_logging

# WebSocket imports
from broker.fyers.websocket import (
    # WebSocket Clients
    FyersOrderWebSocket,
    FyersOrderWebSocketSync,
    FyersDataWebSocket,
    FyersDataWebSocketSync,
    FyersTBTWebSocket,
    FyersTBTWebSocketSync,
    
    # Order WebSocket Models
    OrderUpdate,
    TradeUpdate,
    PositionUpdate,
    GeneralUpdate,
    WebSocketMessage,
    
    # Data WebSocket Models
    SymbolUpdate,
    DepthUpdate,
    IndexUpdate,
    
    # TBT WebSocket Models
    TBTDepth,
    TBTDepthLevel,
    TBTConfig,
    TBTSubscriptionMode,
    
    # WebSocket Enums
    OrderStatus as WSOrderStatus,
    Segment,
    Exchange,
    DataType,
    SubscriptionType,
    
    # Configuration
    ConnectionState,
    WebSocketConfig,
)

__all__ = [
    # Main client
    "FyersClient",
    "create_client",
    "create_client_async",
    "create_client_from_env",
    
    # Authentication
    "FyersOAuth",
    "interactive_login",
    "TokenStorage",
    "FileTokenStorage",
    "MemoryTokenStorage",
    "TokenManager",
    
    # Configuration
    "FyersConfig",
    
    # Auth Models
    "TokenData",
    "AuthState",
    
    # Rate Limit Models
    "RateLimitConfig",
    "RateLimitState",
    "RateLimitType",
    
    # Order Models & Helpers
    "SingleOrderRequest",
    "ModifyOrderRequest",
    "CancelOrderRequest",
    "MultiLegOrderRequest",
    "ConvertPositionRequest",
    "create_market_order",
    "create_limit_order",
    "create_stop_order",
    "create_stop_limit_order",
    "create_bracket_order",
    "create_cover_order",
    "OrderType",
    "OrderSide",
    
    # Response Models
    "ProfileResponse",
    "ProfileData",
    "FundsResponse",
    "HoldingsResponse",
    "OrdersResponse",
    "PositionsResponse",
    "TradesResponse",
    "OrderPlacementResponse",
    "MultiOrderResponse",
    
    # Symbol Master
    "SymbolMaster",
    "Symbol",
    "ExchangeSegment",
    
    # Webhooks
    "PostbackPayload",
    "PostbackHandler",
    "create_webhook_server",
    
    # Exceptions
    "FyersException",
    "FyersAuthenticationError",
    "FyersRateLimitError",
    "FyersAPIError",
    "FyersTokenExpiredError",
    "FyersTokenNotFoundError",
    "FyersNetworkError",
    
    # Core components
    "RateLimiter",
    "HTTPClient",
    "get_logger",
    "configure_logging",
    
    # WebSocket Clients
    "FyersOrderWebSocket",
    "FyersOrderWebSocketSync",
    "FyersDataWebSocket",
    "FyersDataWebSocketSync",
    "FyersTBTWebSocket",
    "FyersTBTWebSocketSync",
    
    # WebSocket Order Models
    "OrderUpdate",
    "TradeUpdate",
    "PositionUpdate",
    "GeneralUpdate",
    "WebSocketMessage",
    
    # WebSocket Data Models
    "SymbolUpdate",
    "DepthUpdate",
    "IndexUpdate",
    
    # WebSocket Enums
    "WSOrderStatus",
    "Segment",
    "Exchange",
    "DataType",
    "SubscriptionType",
    
    # WebSocket Configuration
    "ConnectionState",
    "WebSocketConfig",
    
    # TBT WebSocket Models
    "TBTDepth",
    "TBTDepthLevel",
    "TBTConfig",
    "TBTSubscriptionMode",
]

__version__ = "0.1.0"