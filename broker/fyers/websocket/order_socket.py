"""
Fyers Order WebSocket Client.

Provides real-time updates for orders, trades, positions, and general events.

Uses the installed fyers-apiv3 library under the hood.
"""

import asyncio
import logging
from typing import Optional, Callable, Any, Dict, List
from threading import Thread
import time

from fyers_apiv3.FyersWebsocket import order_ws

from broker.fyers.websocket.models import (
    OrderUpdate,
    TradeUpdate,
    PositionUpdate,
    GeneralUpdate,
    ConnectionState,
    WebSocketConfig,
    SubscriptionType,
)
from broker.fyers.core.logger import get_logger

logger = get_logger("fyers.websocket.order")


class FyersOrderWebSocket:
    """
    Async-friendly wrapper for Fyers Order WebSocket.
    
    Provides real-time updates for:
    - Orders: New orders, modifications, cancellations, fills
    - Trades: Executed trades
    - Positions: Position changes
    - General: eDIS, price alerts, login events
    
    Example:
        ```python
        async def on_order(order: OrderUpdate):
            print(f"Order {order.id}: {order.status_name}")
        
        ws = FyersOrderWebSocket(
            access_token="your_token",
            on_order=on_order,
        )
        
        await ws.connect()
        await ws.subscribe(SubscriptionType.ORDERS, SubscriptionType.TRADES)
        
        # Keep running
        await ws.keep_running()
        
        # Cleanup
        await ws.close()
        ```
    """
    
    def __init__(
        self,
        access_token: str,
        on_order: Optional[Callable[[OrderUpdate], Any]] = None,
        on_trade: Optional[Callable[[TradeUpdate], Any]] = None,
        on_position: Optional[Callable[[PositionUpdate], Any]] = None,
        on_general: Optional[Callable[[GeneralUpdate], Any]] = None,
        on_error: Optional[Callable[[Dict[str, Any]], Any]] = None,
        on_connect: Optional[Callable[[], Any]] = None,
        on_close: Optional[Callable[[Dict[str, Any]], Any]] = None,
        config: Optional[WebSocketConfig] = None,
    ):
        """
        Initialize Order WebSocket client.
        
        Args:
            access_token: Fyers access token (format: "appid:accesstoken")
            on_order: Callback for order updates
            on_trade: Callback for trade updates
            on_position: Callback for position updates
            on_general: Callback for general updates (eDIS, alerts, etc.)
            on_error: Callback for errors
            on_connect: Callback when connected
            on_close: Callback when connection closes
            config: WebSocket configuration
        """
        self._access_token = access_token
        self._config = config or WebSocketConfig()
        
        # User callbacks
        self._on_order = on_order
        self._on_trade = on_trade
        self._on_position = on_position
        self._on_general = on_general
        self._on_error = on_error
        self._on_connect = on_connect
        self._on_close = on_close
        
        # Internal state
        self._state = ConnectionState.DISCONNECTED
        self._socket: Optional[order_ws.FyersOrderSocket] = None
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._subscribed_types: List[SubscriptionType] = []
        
        logger.info("FyersOrderWebSocket initialized")
    
    # ==================== Callbacks for underlying socket ====================
    
    def _handle_order(self, message: Dict[str, Any]) -> None:
        """Handle order update from socket."""
        try:
            if "orders" in message:
                order_data = message.get("orders", {})
                order = OrderUpdate(**order_data)
                
                logger.debug(f"Order update: {order.id} - {order.status_name}")
                
                if self._on_order:
                    if asyncio.iscoroutinefunction(self._on_order):
                        if self._loop:
                            asyncio.run_coroutine_threadsafe(
                                self._on_order(order), self._loop
                            )
                    else:
                        self._on_order(order)
        except Exception as e:
            logger.error(f"Error handling order update: {e}")
            self._handle_error({"error": str(e), "raw_message": message})
    
    def _handle_trade(self, message: Dict[str, Any]) -> None:
        """Handle trade update from socket."""
        try:
            if "trades" in message:
                trade_data = message.get("trades", {})
                trade = TradeUpdate(**trade_data)
                
                logger.debug(f"Trade update: {trade.trade_number}")
                
                if self._on_trade:
                    if asyncio.iscoroutinefunction(self._on_trade):
                        if self._loop:
                            asyncio.run_coroutine_threadsafe(
                                self._on_trade(trade), self._loop
                            )
                    else:
                        self._on_trade(trade)
        except Exception as e:
            logger.error(f"Error handling trade update: {e}")
            self._handle_error({"error": str(e), "raw_message": message})
    
    def _handle_position(self, message: Dict[str, Any]) -> None:
        """Handle position update from socket."""
        try:
            if "positions" in message:
                position_data = message.get("positions", {})
                position = PositionUpdate(**position_data)
                
                logger.debug(f"Position update: {position.symbol}")
                
                if self._on_position:
                    if asyncio.iscoroutinefunction(self._on_position):
                        if self._loop:
                            asyncio.run_coroutine_threadsafe(
                                self._on_position(position), self._loop
                            )
                    else:
                        self._on_position(position)
        except Exception as e:
            logger.error(f"Error handling position update: {e}")
            self._handle_error({"error": str(e), "raw_message": message})
    
    def _handle_general(self, message: Dict[str, Any]) -> None:
        """Handle general update from socket."""
        try:
            general = GeneralUpdate(data=message)
            
            logger.debug(f"General update received")
            
            if self._on_general:
                if asyncio.iscoroutinefunction(self._on_general):
                    if self._loop:
                        asyncio.run_coroutine_threadsafe(
                            self._on_general(general), self._loop
                        )
                else:
                    self._on_general(general)
        except Exception as e:
            logger.error(f"Error handling general update: {e}")
            self._handle_error({"error": str(e), "raw_message": message})
    
    def _handle_error(self, message: Dict[str, Any]) -> None:
        """Handle error from socket."""
        logger.error(f"WebSocket error: {message}")
        
        if self._on_error:
            if asyncio.iscoroutinefunction(self._on_error):
                if self._loop:
                    asyncio.run_coroutine_threadsafe(
                        self._on_error(message), self._loop
                    )
            else:
                self._on_error(message)
    
    def _handle_connect(self) -> None:
        """Handle connection established."""
        self._state = ConnectionState.CONNECTED
        logger.info("Order WebSocket connected")
        
        # Re-subscribe if we had previous subscriptions
        if self._subscribed_types and self._socket:
            data_types = ",".join([t.value for t in self._subscribed_types])
            self._socket.subscribe(data_type=data_types)
        
        if self._on_connect:
            if asyncio.iscoroutinefunction(self._on_connect):
                if self._loop:
                    asyncio.run_coroutine_threadsafe(
                        self._on_connect(), self._loop
                    )
            else:
                self._on_connect()
    
    def _handle_close(self, message: Dict[str, Any]) -> None:
        """Handle connection closed."""
        self._state = ConnectionState.DISCONNECTED
        logger.info(f"Order WebSocket closed: {message}")
        
        if self._on_close:
            if asyncio.iscoroutinefunction(self._on_close):
                if self._loop:
                    asyncio.run_coroutine_threadsafe(
                        self._on_close(message), self._loop
                    )
            else:
                self._on_close(message)
    
    # ==================== Public API ====================
    
    async def connect(self) -> None:
        """
        Establish WebSocket connection.
        
        Creates the underlying FyersOrderSocket and connects to the server.
        """
        if self._state == ConnectionState.CONNECTED:
            logger.warning("Already connected")
            return
        
        self._state = ConnectionState.CONNECTING
        self._loop = asyncio.get_event_loop()
        
        try:
            # Create the Fyers socket instance
            self._socket = order_ws.FyersOrderSocket(
                access_token=self._access_token,
                write_to_file=self._config.write_to_file,
                log_path=self._config.log_path,
                on_orders=self._handle_order,
                on_trades=self._handle_trade,
                on_positions=self._handle_position,
                on_general=self._handle_general,
                on_error=self._handle_error,
                on_connect=self._handle_connect,
                on_close=self._handle_close,
                reconnect=self._config.reconnect,
                reconnect_retry=self._config.max_reconnect_attempts,
            )
            
            # Connect in a thread to not block
            await asyncio.get_event_loop().run_in_executor(
                None, self._socket.connect
            )
            
            logger.info("Order WebSocket connection initiated")
            
        except Exception as e:
            self._state = ConnectionState.ERROR
            logger.error(f"Failed to connect: {e}")
            raise
    
    async def subscribe(self, *data_types: SubscriptionType) -> None:
        """
        Subscribe to data types.
        
        Args:
            *data_types: One or more subscription types (ORDERS, TRADES, POSITIONS, GENERAL)
            
        Example:
            ```python
            await ws.subscribe(SubscriptionType.ORDERS, SubscriptionType.TRADES)
            ```
        """
        if not self._socket:
            raise RuntimeError("Not connected. Call connect() first.")
        
        if not data_types:
            data_types = (SubscriptionType.ORDERS,)
        
        self._subscribed_types = list(data_types)
        data_type_str = ",".join([t.value for t in data_types])
        
        logger.info(f"Subscribing to: {data_type_str}")
        
        await asyncio.get_event_loop().run_in_executor(
            None, self._socket.subscribe, data_type_str
        )
    
    async def subscribe_all(self) -> None:
        """Subscribe to all data types (orders, trades, positions, general)."""
        await self.subscribe(
            SubscriptionType.ORDERS,
            SubscriptionType.TRADES,
            SubscriptionType.POSITIONS,
            SubscriptionType.GENERAL,
        )
    
    async def subscribe_orders(self) -> None:
        """Subscribe to order updates only."""
        await self.subscribe(SubscriptionType.ORDERS)
    
    async def subscribe_trades(self) -> None:
        """Subscribe to trade updates only."""
        await self.subscribe(SubscriptionType.TRADES)
    
    async def subscribe_positions(self) -> None:
        """Subscribe to position updates only."""
        await self.subscribe(SubscriptionType.POSITIONS)
    
    async def unsubscribe(self, *data_types: SubscriptionType) -> None:
        """
        Unsubscribe from data types.
        
        Args:
            *data_types: One or more subscription types to unsubscribe from
        """
        if not self._socket:
            raise RuntimeError("Not connected. Call connect() first.")
        
        for dt in data_types:
            if dt in self._subscribed_types:
                self._subscribed_types.remove(dt)
        
        data_type_str = ",".join([t.value for t in data_types])
        
        logger.info(f"Unsubscribing from: {data_type_str}")
        
        await asyncio.get_event_loop().run_in_executor(
            None, self._socket.unsubscribe, data_type_str
        )
    
    async def close(self) -> None:
        """Close the WebSocket connection."""
        if self._socket:
            logger.info("Closing Order WebSocket connection")
            await asyncio.get_event_loop().run_in_executor(
                None, self._socket.close_connection
            )
            self._socket = None
            self._state = ConnectionState.DISCONNECTED
    
    async def keep_running(self) -> None:
        """
        Keep the connection running.
        
        This method blocks until the connection is closed.
        Use in an async context to keep receiving updates.
        """
        if not self._socket:
            raise RuntimeError("Not connected. Call connect() first.")
        
        # Start the keep_running in a thread
        await asyncio.get_event_loop().run_in_executor(
            None, self._socket.keep_running
        )
    
    @property
    def is_connected(self) -> bool:
        """Check if WebSocket is connected."""
        if self._socket:
            return self._socket.is_connected()
        return False
    
    @property
    def state(self) -> ConnectionState:
        """Get current connection state."""
        return self._state
    
    @property
    def subscribed_types(self) -> List[SubscriptionType]:
        """Get list of currently subscribed data types."""
        return self._subscribed_types.copy()
    
    # ==================== Context Manager ====================
    
    async def __aenter__(self) -> "FyersOrderWebSocket":
        """Async context manager entry."""
        await self.connect()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Async context manager exit."""
        await self.close()


# ==================== Synchronous Wrapper ====================

class FyersOrderWebSocketSync:
    """
    Synchronous wrapper for Fyers Order WebSocket.
    
    For use cases where async is not needed.
    
    Example:
        ```python
        def on_order(order):
            print(f"Order: {order}")
        
        ws = FyersOrderWebSocketSync(
            access_token="your_token",
            on_order=on_order,
        )
        
        ws.connect()
        ws.subscribe_orders()
        ws.keep_running()  # Blocks
        ```
    """
    
    def __init__(
        self,
        access_token: str,
        on_order: Optional[Callable[[Dict[str, Any]], Any]] = None,
        on_trade: Optional[Callable[[Dict[str, Any]], Any]] = None,
        on_position: Optional[Callable[[Dict[str, Any]], Any]] = None,
        on_general: Optional[Callable[[Dict[str, Any]], Any]] = None,
        on_error: Optional[Callable[[Dict[str, Any]], Any]] = None,
        on_connect: Optional[Callable[[], Any]] = None,
        on_close: Optional[Callable[[Dict[str, Any]], Any]] = None,
        config: Optional[WebSocketConfig] = None,
    ):
        """Initialize synchronous Order WebSocket client."""
        self._access_token = access_token
        self._config = config or WebSocketConfig()
        
        self._on_order = on_order
        self._on_trade = on_trade
        self._on_position = on_position
        self._on_general = on_general
        self._on_error = on_error
        self._on_connect = on_connect
        self._on_close = on_close
        
        self._socket: Optional[order_ws.FyersOrderSocket] = None
        self._subscribed_types: List[str] = []
    
    def connect(self) -> None:
        """Establish WebSocket connection."""
        self._socket = order_ws.FyersOrderSocket(
            access_token=self._access_token,
            write_to_file=self._config.write_to_file,
            log_path=self._config.log_path,
            on_orders=self._on_order,
            on_trades=self._on_trade,
            on_positions=self._on_position,
            on_general=self._on_general,
            on_error=self._on_error,
            on_connect=self._on_connect,
            on_close=self._on_close,
            reconnect=self._config.reconnect,
            reconnect_retry=self._config.max_reconnect_attempts,
        )
        self._socket.connect()
    
    def subscribe(self, data_type: str) -> None:
        """Subscribe to data types."""
        if self._socket:
            self._socket.subscribe(data_type=data_type)
    
    def subscribe_orders(self) -> None:
        """Subscribe to order updates."""
        self.subscribe("OnOrders")
    
    def subscribe_trades(self) -> None:
        """Subscribe to trade updates."""
        self.subscribe("OnTrades")
    
    def subscribe_positions(self) -> None:
        """Subscribe to position updates."""
        self.subscribe("OnPositions")
    
    def subscribe_all(self) -> None:
        """Subscribe to all updates."""
        self.subscribe("OnOrders,OnTrades,OnPositions,OnGeneral")
    
    def unsubscribe(self, data_type: str) -> None:
        """Unsubscribe from data types."""
        if self._socket:
            self._socket.unsubscribe(data_type=data_type)
    
    def close(self) -> None:
        """Close connection."""
        if self._socket:
            self._socket.close_connection()
            self._socket = None
    
    def keep_running(self) -> None:
        """Keep connection running (blocks)."""
        if self._socket:
            self._socket.keep_running()
    
    @property
    def is_connected(self) -> bool:
        """Check if connected."""
        return self._socket.is_connected() if self._socket else False