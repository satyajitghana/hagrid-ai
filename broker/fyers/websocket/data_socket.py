"""
Fyers Data WebSocket Client.

Provides real-time market data updates for symbols, indices, and market depth.

Uses the installed fyers-apiv3 library under the hood.
"""

import asyncio
import logging
from typing import Optional, Callable, Any, Dict, List, Union
from threading import Thread
import time

from fyers_apiv3.FyersWebsocket import data_ws

from broker.fyers.websocket.models import (
    SymbolUpdate,
    DepthUpdate,
    IndexUpdate,
    ConnectionState,
    WebSocketConfig,
    DataType,
)
from broker.fyers.core.logger import get_logger

logger = get_logger("fyers.websocket.data")


class FyersDataWebSocket:
    """
    Async-friendly wrapper for Fyers Data WebSocket.
    
    Provides real-time market data including:
    - Symbol updates: Price, volume, bid/ask for stocks and options
    - Index updates: Index values
    - Depth updates: 5-level order book
    
    Supports up to 5000 symbol subscriptions.
    
    Example:
        ```python
        async def on_tick(data: SymbolUpdate):
            print(f"{data.symbol}: {data.ltp} ({data.chp}%)")
        
        ws = FyersDataWebSocket(
            access_token="your_token",
            on_message=on_tick,
        )
        
        await ws.connect()
        await ws.subscribe(["NSE:SBIN-EQ", "NSE:INFY-EQ"])
        
        # Keep running
        await ws.keep_running()
        
        # Cleanup
        await ws.close()
        ```
    """
    
    # Maximum symbols allowed per subscription
    MAX_SYMBOLS = 5000
    
    def __init__(
        self,
        access_token: str,
        on_message: Optional[Callable[[Union[SymbolUpdate, DepthUpdate, IndexUpdate]], Any]] = None,
        on_error: Optional[Callable[[Dict[str, Any]], Any]] = None,
        on_connect: Optional[Callable[[], Any]] = None,
        on_close: Optional[Callable[[Dict[str, Any]], Any]] = None,
        config: Optional[WebSocketConfig] = None,
    ):
        """
        Initialize Data WebSocket client.
        
        Args:
            access_token: Fyers access token (format: "appid:accesstoken")
            on_message: Callback for market data updates
            on_error: Callback for errors
            on_connect: Callback when connected
            on_close: Callback when connection closes
            config: WebSocket configuration
        """
        self._access_token = access_token
        self._config = config or WebSocketConfig()
        
        # User callbacks
        self._on_message = on_message
        self._on_error = on_error
        self._on_connect = on_connect
        self._on_close = on_close
        
        # Internal state
        self._state = ConnectionState.DISCONNECTED
        self._socket: Optional[data_ws.FyersDataSocket] = None
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._subscribed_symbols: List[str] = []
        self._data_type: DataType = DataType.SYMBOL_UPDATE
        
        logger.info("FyersDataWebSocket initialized")
    
    # ==================== Callbacks for underlying socket ====================
    
    def _handle_message(self, message: Dict[str, Any]) -> None:
        """Handle market data message from socket."""
        try:
            # Skip connection/subscription status messages
            if "type" in message and message.get("type") in ["cn", "sub", "unsub"]:
                logger.debug(f"Status message: {message}")
                return
            
            msg_type = message.get("type", "sf")
            
            # Parse based on message type
            if msg_type == "sf":  # Symbol/Equity data
                data = SymbolUpdate(**message)
            elif msg_type == "if":  # Index data
                data = IndexUpdate(**message)
            elif msg_type == "dp":  # Depth data
                data = DepthUpdate(**message)
            else:
                logger.warning(f"Unknown message type: {msg_type}")
                data = SymbolUpdate(**message)
            
            logger.debug(f"Data update: {data.symbol} LTP={getattr(data, 'ltp', 'N/A')}")
            
            if self._on_message:
                if asyncio.iscoroutinefunction(self._on_message):
                    if self._loop:
                        asyncio.run_coroutine_threadsafe(
                            self._on_message(data), self._loop
                        )
                else:
                    self._on_message(data)
                    
        except Exception as e:
            logger.error(f"Error handling data message: {e}")
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
        logger.info("Data WebSocket connected")
        
        # Re-subscribe if we had previous subscriptions
        if self._subscribed_symbols and self._socket:
            self._socket.subscribe(
                symbols=self._subscribed_symbols,
                data_type=self._data_type.value,
            )
        
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
        logger.info(f"Data WebSocket closed: {message}")
        
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
        
        Creates the underlying FyersDataSocket and connects to the server.
        """
        if self._state == ConnectionState.CONNECTED:
            logger.warning("Already connected")
            return
        
        self._state = ConnectionState.CONNECTING
        self._loop = asyncio.get_event_loop()
        
        try:
            # Create the Fyers socket instance
            self._socket = data_ws.FyersDataSocket(
                access_token=self._access_token,
                write_to_file=self._config.write_to_file,
                log_path=self._config.log_path,
                litemode=self._config.lite_mode,
                reconnect=self._config.reconnect,
                on_message=self._handle_message,
                on_error=self._handle_error,
                on_connect=self._handle_connect,
                on_close=self._handle_close,
                reconnect_retry=self._config.max_reconnect_attempts,
            )
            
            # Connect in a thread to not block
            await asyncio.get_event_loop().run_in_executor(
                None, self._socket.connect
            )
            
            logger.info("Data WebSocket connection initiated")
            
        except Exception as e:
            self._state = ConnectionState.ERROR
            logger.error(f"Failed to connect: {e}")
            raise
    
    async def subscribe(
        self,
        symbols: List[str],
        data_type: DataType = DataType.SYMBOL_UPDATE,
        channel: int = 11,
    ) -> None:
        """
        Subscribe to market data for symbols.
        
        Args:
            symbols: List of symbols in Fyers format (e.g., ["NSE:SBIN-EQ", "NSE:INFY-EQ"])
            data_type: Type of data (SymbolUpdate or DepthUpdate)
            channel: Channel number (default 11)
            
        Example:
            ```python
            # Subscribe to price updates
            await ws.subscribe(["NSE:SBIN-EQ", "NSE:INFY-EQ"])
            
            # Subscribe to market depth
            await ws.subscribe(
                ["NSE:SBIN-EQ"],
                data_type=DataType.DEPTH_UPDATE
            )
            ```
        """
        if not self._socket:
            raise RuntimeError("Not connected. Call connect() first.")
        
        if len(symbols) > self.MAX_SYMBOLS:
            raise ValueError(f"Maximum {self.MAX_SYMBOLS} symbols allowed")
        
        # Track subscribed symbols
        self._subscribed_symbols.extend(symbols)
        self._subscribed_symbols = list(set(self._subscribed_symbols))[:self.MAX_SYMBOLS]
        self._data_type = data_type
        
        logger.info(f"Subscribing to {len(symbols)} symbols ({data_type.value})")
        
        await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: self._socket.subscribe(
                symbols=symbols,
                data_type=data_type.value,
                channel=channel,
            )
        )
    
    async def subscribe_symbol_updates(self, symbols: List[str]) -> None:
        """Subscribe to symbol price updates."""
        await self.subscribe(symbols, DataType.SYMBOL_UPDATE)
    
    async def subscribe_depth_updates(self, symbols: List[str]) -> None:
        """Subscribe to market depth updates."""
        await self.subscribe(symbols, DataType.DEPTH_UPDATE)
    
    async def unsubscribe(
        self,
        symbols: List[str],
        data_type: DataType = DataType.SYMBOL_UPDATE,
        channel: int = 11,
    ) -> None:
        """
        Unsubscribe from market data for symbols.
        
        Args:
            symbols: List of symbols to unsubscribe
            data_type: Type of data
            channel: Channel number
        """
        if not self._socket:
            raise RuntimeError("Not connected. Call connect() first.")
        
        # Remove from tracked symbols
        for symbol in symbols:
            if symbol in self._subscribed_symbols:
                self._subscribed_symbols.remove(symbol)
        
        logger.info(f"Unsubscribing from {len(symbols)} symbols")
        
        await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: self._socket.unsubscribe(
                symbols=symbols,
                data_type=data_type.value,
                channel=channel,
            )
        )
    
    async def close(self) -> None:
        """Close the WebSocket connection."""
        if self._socket:
            logger.info("Closing Data WebSocket connection")
            await asyncio.get_event_loop().run_in_executor(
                None, self._socket.close_connection
            )
            self._socket = None
            self._state = ConnectionState.DISCONNECTED
            self._subscribed_symbols = []
    
    async def keep_running(self) -> None:
        """
        Keep the connection running.
        
        This method blocks until the connection is closed.
        """
        if not self._socket:
            raise RuntimeError("Not connected. Call connect() first.")
        
        await asyncio.get_event_loop().run_in_executor(
            None, self._socket.keep_running
        )
    
    async def channel_resume(self, channel: int) -> None:
        """Resume a paused channel."""
        if self._socket:
            await asyncio.get_event_loop().run_in_executor(
                None, self._socket.channel_resume, channel
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
    def subscribed_symbols(self) -> List[str]:
        """Get list of currently subscribed symbols."""
        return self._subscribed_symbols.copy()
    
    @property
    def subscription_count(self) -> int:
        """Get count of subscribed symbols."""
        return len(self._subscribed_symbols)
    
    # ==================== Context Manager ====================
    
    async def __aenter__(self) -> "FyersDataWebSocket":
        """Async context manager entry."""
        await self.connect()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Async context manager exit."""
        await self.close()


# ==================== Synchronous Wrapper ====================

class FyersDataWebSocketSync:
    """
    Synchronous wrapper for Fyers Data WebSocket.
    
    For use cases where async is not needed.
    
    Example:
        ```python
        def on_tick(message):
            print(f"Tick: {message}")
        
        ws = FyersDataWebSocketSync(
            access_token="your_token",
            on_message=on_tick,
        )
        
        ws.connect()
        ws.subscribe(["NSE:SBIN-EQ", "NSE:INFY-EQ"])
        ws.keep_running()  # Blocks
        ```
    """
    
    MAX_SYMBOLS = 5000
    
    def __init__(
        self,
        access_token: str,
        on_message: Optional[Callable[[Dict[str, Any]], Any]] = None,
        on_error: Optional[Callable[[Dict[str, Any]], Any]] = None,
        on_connect: Optional[Callable[[], Any]] = None,
        on_close: Optional[Callable[[Dict[str, Any]], Any]] = None,
        config: Optional[WebSocketConfig] = None,
    ):
        """Initialize synchronous Data WebSocket client."""
        self._access_token = access_token
        self._config = config or WebSocketConfig()
        
        self._on_message = on_message
        self._on_error = on_error
        self._on_connect = on_connect
        self._on_close = on_close
        
        self._socket: Optional[data_ws.FyersDataSocket] = None
        self._subscribed_symbols: List[str] = []
    
    def connect(self) -> None:
        """Establish WebSocket connection."""
        self._socket = data_ws.FyersDataSocket(
            access_token=self._access_token,
            write_to_file=self._config.write_to_file,
            log_path=self._config.log_path,
            litemode=self._config.lite_mode,
            reconnect=self._config.reconnect,
            on_message=self._on_message,
            on_error=self._on_error,
            on_connect=self._on_connect,
            on_close=self._on_close,
            reconnect_retry=self._config.max_reconnect_attempts,
        )
        self._socket.connect()
    
    def subscribe(
        self,
        symbols: List[str],
        data_type: str = "SymbolUpdate",
        channel: int = 11,
    ) -> None:
        """Subscribe to market data for symbols."""
        if self._socket:
            self._subscribed_symbols.extend(symbols)
            self._subscribed_symbols = list(set(self._subscribed_symbols))[:self.MAX_SYMBOLS]
            self._socket.subscribe(symbols=symbols, data_type=data_type, channel=channel)
    
    def subscribe_symbol_updates(self, symbols: List[str]) -> None:
        """Subscribe to symbol updates."""
        self.subscribe(symbols, "SymbolUpdate")
    
    def subscribe_depth_updates(self, symbols: List[str]) -> None:
        """Subscribe to depth updates."""
        self.subscribe(symbols, "DepthUpdate")
    
    def unsubscribe(
        self,
        symbols: List[str],
        data_type: str = "SymbolUpdate",
        channel: int = 11,
    ) -> None:
        """Unsubscribe from market data."""
        if self._socket:
            for symbol in symbols:
                if symbol in self._subscribed_symbols:
                    self._subscribed_symbols.remove(symbol)
            self._socket.unsubscribe(symbols=symbols, data_type=data_type, channel=channel)
    
    def close(self) -> None:
        """Close connection."""
        if self._socket:
            self._socket.close_connection()
            self._socket = None
            self._subscribed_symbols = []
    
    def keep_running(self) -> None:
        """Keep connection running (blocks)."""
        if self._socket:
            self._socket.keep_running()
    
    @property
    def is_connected(self) -> bool:
        """Check if connected."""
        return self._socket.is_connected() if self._socket else False
    
    @property
    def subscribed_symbols(self) -> List[str]:
        """Get subscribed symbols."""
        return self._subscribed_symbols.copy()