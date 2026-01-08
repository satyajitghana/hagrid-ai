"""
Fyers WebSocket Module

Provides real-time WebSocket connections for:
- Order updates (orders, trades, positions)
- Market data (symbol updates, depth updates, index updates)

Example usage:
    ```python
    from broker.fyers.websocket import FyersOrderWebSocket, FyersDataWebSocket
    
    # Order WebSocket
    order_ws = FyersOrderWebSocket(
        access_token="your_access_token",
        on_order=lambda msg: print(f"Order: {msg}"),
        on_trade=lambda msg: print(f"Trade: {msg}"),
        on_position=lambda msg: print(f"Position: {msg}"),
    )
    await order_ws.connect()
    await order_ws.subscribe_orders()
    
    # Data WebSocket
    data_ws = FyersDataWebSocket(
        access_token="your_access_token",
        on_message=lambda msg: print(f"Data: {msg}"),
    )
    await data_ws.connect()
    await data_ws.subscribe(["NSE:SBIN-EQ", "NSE:INFY-EQ"])
    ```
"""

from broker.fyers.websocket.order_socket import (
    FyersOrderWebSocket,
    FyersOrderWebSocketSync,
)
from broker.fyers.websocket.data_socket import (
    FyersDataWebSocket,
    FyersDataWebSocketSync,
)
from broker.fyers.websocket.tbt_socket import (
    FyersTBTWebSocket,
    FyersTBTWebSocketSync,
    TBTDepth,
    TBTDepthLevel,
    TBTConfig,
    TBTSubscriptionMode,
)
from broker.fyers.websocket.models import (
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
    
    # Enums
    OrderStatus,
    OrderSide,
    Segment,
    Exchange,
    OrderType,
    DataType,
    SubscriptionType,
    
    # Configuration
    ConnectionState,
    WebSocketConfig,
)

__all__ = [
    # WebSocket Clients (Async)
    "FyersOrderWebSocket",
    "FyersDataWebSocket",
    "FyersTBTWebSocket",
    
    # WebSocket Clients (Sync)
    "FyersOrderWebSocketSync",
    "FyersDataWebSocketSync",
    "FyersTBTWebSocketSync",
    
    # Order WebSocket Models
    "OrderUpdate",
    "TradeUpdate",
    "PositionUpdate",
    "GeneralUpdate",
    "WebSocketMessage",
    
    # Data WebSocket Models
    "SymbolUpdate",
    "DepthUpdate",
    "IndexUpdate",
    
    # Enums
    "OrderStatus",
    "OrderSide",
    "Segment",
    "Exchange",
    "OrderType",
    "DataType",
    "SubscriptionType",
    
    # Configuration
    "ConnectionState",
    "WebSocketConfig",
    
    # TBT (Tick-by-Tick) Models
    "TBTDepth",
    "TBTDepthLevel",
    "TBTConfig",
    "TBTSubscriptionMode",
]