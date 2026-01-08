"""
Fyers TBT (Tick-by-Tick) WebSocket Client.

Provides real-time 50-level market depth data for NFO and NSE instruments.

Key Features:
- 50 levels of market depth
- Channel-based subscription management
- Incremental data updates (diff packets)
- Up to 5 symbols per connection, 3 connections per user

Uses the installed fyers-apiv3 library under the hood.
"""

import asyncio
import logging
from typing import Optional, Callable, Any, Dict, List, Set
from threading import Thread
import time
from dataclasses import dataclass, field
from enum import Enum

from fyers_apiv3.FyersWebsocket.tbt_ws import (
    FyersTbtSocket,
    SubscriptionModes,
    Depth,
)

from broker.fyers.websocket.models import (
    ConnectionState,
    WebSocketConfig,
)
from broker.fyers.core.logger import get_logger

logger = get_logger("fyers.websocket.tbt")


# ==================== TBT Models ====================

class TBTSubscriptionMode(str, Enum):
    """TBT subscription modes."""
    DEPTH = "depth"


@dataclass
class TBTDepthLevel:
    """Single level in the 50-level market depth."""
    price: float
    qty: int
    num_orders: int


@dataclass
class TBTDepth:
    """
    50-level market depth data.
    
    Attributes:
        symbol: Symbol ticker
        total_buy_qty: Total buy quantity
        total_sell_qty: Total sell quantity
        bid_prices: List of 50 bid prices
        ask_prices: List of 50 ask prices
        bid_quantities: List of 50 bid quantities
        ask_quantities: List of 50 ask quantities
        bid_orders: List of 50 bid order counts
        ask_orders: List of 50 ask order counts
        is_snapshot: True if this is a full snapshot, False for diff
        timestamp: Feed timestamp (epoch)
        send_time: Server send time (epoch)
    """
    symbol: str
    total_buy_qty: int = 0
    total_sell_qty: int = 0
    bid_prices: List[float] = field(default_factory=lambda: [0.0] * 50)
    ask_prices: List[float] = field(default_factory=lambda: [0.0] * 50)
    bid_quantities: List[int] = field(default_factory=lambda: [0] * 50)
    ask_quantities: List[int] = field(default_factory=lambda: [0] * 50)
    bid_orders: List[int] = field(default_factory=lambda: [0] * 50)
    ask_orders: List[int] = field(default_factory=lambda: [0] * 50)
    is_snapshot: bool = False
    timestamp: int = 0
    send_time: int = 0
    
    @classmethod
    def from_fyers_depth(cls, symbol: str, depth: Depth) -> "TBTDepth":
        """Create TBTDepth from Fyers Depth object."""
        return cls(
            symbol=symbol,
            total_buy_qty=depth.tbq,
            total_sell_qty=depth.tsq,
            bid_prices=depth.bidprice.copy(),
            ask_prices=depth.askprice.copy(),
            bid_quantities=depth.bidqty.copy(),
            ask_quantities=depth.askqty.copy(),
            bid_orders=depth.bidordn.copy(),
            ask_orders=depth.askordn.copy(),
            is_snapshot=depth.snapshot,
            timestamp=depth.timestamp,
            send_time=depth.sendtime,
        )
    
    @property
    def bids(self) -> List[TBTDepthLevel]:
        """Get all 50 bid levels as structured data."""
        return [
            TBTDepthLevel(
                price=self.bid_prices[i],
                qty=self.bid_quantities[i],
                num_orders=self.bid_orders[i]
            )
            for i in range(50) if self.bid_prices[i] > 0
        ]
    
    @property
    def asks(self) -> List[TBTDepthLevel]:
        """Get all 50 ask levels as structured data."""
        return [
            TBTDepthLevel(
                price=self.ask_prices[i],
                qty=self.ask_quantities[i],
                num_orders=self.ask_orders[i]
            )
            for i in range(50) if self.ask_prices[i] > 0
        ]
    
    @property
    def best_bid(self) -> Optional[TBTDepthLevel]:
        """Get best bid (highest bid price)."""
        if self.bid_prices[0] > 0:
            return TBTDepthLevel(
                price=self.bid_prices[0],
                qty=self.bid_quantities[0],
                num_orders=self.bid_orders[0]
            )
        return None
    
    @property
    def best_ask(self) -> Optional[TBTDepthLevel]:
        """Get best ask (lowest ask price)."""
        if self.ask_prices[0] > 0:
            return TBTDepthLevel(
                price=self.ask_prices[0],
                qty=self.ask_quantities[0],
                num_orders=self.ask_orders[0]
            )
        return None
    
    @property
    def spread(self) -> Optional[float]:
        """Calculate bid-ask spread."""
        if self.bid_prices[0] > 0 and self.ask_prices[0] > 0:
            return self.ask_prices[0] - self.bid_prices[0]
        return None


@dataclass
class TBTConfig:
    """Configuration for TBT WebSocket."""
    reconnect: bool = True
    max_reconnect_attempts: int = 50
    reconnect_delay: int = 5
    write_to_file: bool = False
    log_path: Optional[str] = None
    diff_only: bool = False  # If True, only returns diff packets (not accumulated)


# ==================== TBT WebSocket Client ====================

class FyersTBTWebSocket:
    """
    Async-friendly wrapper for Fyers TBT (Tick-by-Tick) WebSocket.
    
    Provides 50-level market depth data for NFO and NSE instruments.
    
    Rate Limits:
    - Max 3 active connections per app per user
    - Max 5 symbols per connection
    - Max 50 channels per connection
    
    Example:
        ```python
        async def on_depth(depth: TBTDepth):
            print(f"{depth.symbol}: Best Bid={depth.best_bid.price}, Best Ask={depth.best_ask.price}")
            print(f"Total Buy: {depth.total_buy_qty}, Total Sell: {depth.total_sell_qty}")
        
        ws = FyersTBTWebSocket(
            access_token="your_token",
            on_depth_update=on_depth,
        )
        
        await ws.connect()
        await ws.subscribe(
            symbols=["NSE:NIFTY25MARFUT", "NSE:BANKNIFTY25MARFUT"],
            channel="1",
        )
        await ws.switch_channel(resume=["1"])
        await ws.keep_running()
        ```
    """
    
    # Rate limits
    MAX_SYMBOLS_PER_CONNECTION = 5
    MAX_CHANNELS = 50
    MAX_CONNECTIONS_PER_USER = 3
    
    def __init__(
        self,
        access_token: str,
        on_depth_update: Optional[Callable[[TBTDepth], Any]] = None,
        on_error: Optional[Callable[[Dict[str, Any]], Any]] = None,
        on_error_message: Optional[Callable[[str], Any]] = None,
        on_connect: Optional[Callable[[], Any]] = None,
        on_close: Optional[Callable[[Dict[str, Any]], Any]] = None,
        config: Optional[TBTConfig] = None,
    ):
        """
        Initialize TBT WebSocket client.
        
        Args:
            access_token: Fyers access token (format: "appid:accesstoken")
            on_depth_update: Callback for 50-level depth updates
            on_error: Callback for WebSocket errors
            on_error_message: Callback for server error messages
            on_connect: Callback when connected
            on_close: Callback when connection closes
            config: TBT WebSocket configuration
        """
        self._access_token = access_token
        self._config = config or TBTConfig()
        
        # User callbacks
        self._on_depth_update = on_depth_update
        self._on_error = on_error
        self._on_error_message = on_error_message
        self._on_connect = on_connect
        self._on_close = on_close
        
        # Internal state
        self._state = ConnectionState.DISCONNECTED
        self._socket: Optional[FyersTbtSocket] = None
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._subscribed_channels: Dict[str, Set[str]] = {}  # channel -> symbols
        self._active_channels: Set[str] = set()
        
        logger.info("FyersTBTWebSocket initialized")
    
    # ==================== Callbacks for underlying socket ====================
    
    def _handle_depth_update(self, ticker: str, depth: Depth) -> None:
        """Handle depth update from socket."""
        try:
            tbt_depth = TBTDepth.from_fyers_depth(ticker, depth)
            
            logger.debug(
                f"TBT Depth: {ticker} - TBQ={tbt_depth.total_buy_qty}, "
                f"TSQ={tbt_depth.total_sell_qty}, Snapshot={tbt_depth.is_snapshot}"
            )
            
            if self._on_depth_update:
                if asyncio.iscoroutinefunction(self._on_depth_update):
                    if self._loop:
                        asyncio.run_coroutine_threadsafe(
                            self._on_depth_update(tbt_depth), self._loop
                        )
                else:
                    self._on_depth_update(tbt_depth)
                    
        except Exception as e:
            logger.error(f"Error handling depth update: {e}")
            self._handle_error({"error": str(e), "ticker": ticker})
    
    def _handle_error(self, message: Dict[str, Any]) -> None:
        """Handle error from socket."""
        logger.error(f"TBT WebSocket error: {message}")
        
        if self._on_error:
            if asyncio.iscoroutinefunction(self._on_error):
                if self._loop:
                    asyncio.run_coroutine_threadsafe(
                        self._on_error(message), self._loop
                    )
            else:
                self._on_error(message)
    
    def _handle_error_message(self, message: str) -> None:
        """Handle error message from server."""
        logger.error(f"TBT Server error: {message}")
        
        if self._on_error_message:
            if asyncio.iscoroutinefunction(self._on_error_message):
                if self._loop:
                    asyncio.run_coroutine_threadsafe(
                        self._on_error_message(message), self._loop
                    )
            else:
                self._on_error_message(message)
    
    def _handle_connect(self) -> None:
        """Handle connection established."""
        self._state = ConnectionState.CONNECTED
        logger.info("TBT WebSocket connected")
        
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
        logger.info(f"TBT WebSocket closed: {message}")
        
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
        Establish TBT WebSocket connection.
        
        Creates the underlying FyersTbtSocket and connects to the server.
        """
        if self._state == ConnectionState.CONNECTED:
            logger.warning("Already connected")
            return
        
        self._state = ConnectionState.CONNECTING
        self._loop = asyncio.get_event_loop()
        
        try:
            # Create the Fyers TBT socket instance
            self._socket = FyersTbtSocket(
                access_token=self._access_token,
                write_to_file=self._config.write_to_file,
                log_path=self._config.log_path,
                on_depth_update=self._handle_depth_update,
                on_error_message=self._handle_error_message,
                on_error=self._handle_error,
                on_open=self._handle_connect,
                on_close=self._handle_close,
                reconnect=self._config.reconnect,
                diff_only=self._config.diff_only,
                reconnect_retry=self._config.max_reconnect_attempts,
            )
            
            # Connect in a thread to not block
            await asyncio.get_event_loop().run_in_executor(
                None, self._socket.connect
            )
            
            logger.info("TBT WebSocket connection initiated")
            
        except Exception as e:
            self._state = ConnectionState.ERROR
            logger.error(f"Failed to connect TBT: {e}")
            raise
    
    async def subscribe(
        self,
        symbols: List[str],
        channel: str = "1",
        mode: TBTSubscriptionMode = TBTSubscriptionMode.DEPTH,
    ) -> None:
        """
        Subscribe to 50-level market depth for symbols.
        
        Args:
            symbols: List of symbols (max 5 per connection)
                     Must be NFO or NSE instruments
            channel: Channel number (1-50)
            mode: Subscription mode (currently only DEPTH)
            
        Example:
            ```python
            await ws.subscribe(
                symbols=["NSE:NIFTY25MARFUT", "NSE:BANKNIFTY25MARFUT"],
                channel="1",
            )
            ```
        
        Note: You must call switch_channel() to start receiving data.
        """
        if not self._socket:
            raise RuntimeError("Not connected. Call connect() first.")
        
        if len(symbols) > self.MAX_SYMBOLS_PER_CONNECTION:
            raise ValueError(
                f"Maximum {self.MAX_SYMBOLS_PER_CONNECTION} symbols allowed per connection"
            )
        
        channel_int = int(channel)
        if channel_int < 1 or channel_int > self.MAX_CHANNELS:
            raise ValueError(f"Channel must be between 1 and {self.MAX_CHANNELS}")
        
        # Track subscribed symbols
        if channel not in self._subscribed_channels:
            self._subscribed_channels[channel] = set()
        self._subscribed_channels[channel].update(symbols)
        
        # Map mode to Fyers mode
        fyers_mode = SubscriptionModes.DEPTH
        
        logger.info(f"Subscribing to {len(symbols)} symbols on channel {channel}")
        
        await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: self._socket.subscribe(
                symbol_tickers=set(symbols),
                channelNo=channel,
                mode=fyers_mode,
            )
        )
    
    async def unsubscribe(
        self,
        symbols: List[str],
        channel: str = "1",
        mode: TBTSubscriptionMode = TBTSubscriptionMode.DEPTH,
    ) -> None:
        """
        Unsubscribe from symbols on a channel.
        
        Args:
            symbols: List of symbols to unsubscribe
            channel: Channel number
            mode: Subscription mode
        """
        if not self._socket:
            raise RuntimeError("Not connected. Call connect() first.")
        
        # Update tracking
        if channel in self._subscribed_channels:
            self._subscribed_channels[channel].difference_update(symbols)
            if not self._subscribed_channels[channel]:
                del self._subscribed_channels[channel]
        
        fyers_mode = SubscriptionModes.DEPTH
        
        logger.info(f"Unsubscribing from {len(symbols)} symbols on channel {channel}")
        
        await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: self._socket.unsubscribe(
                symbol_tickers=set(symbols),
                channelNo=channel,
                mode=fyers_mode,
            )
        )
    
    async def switch_channel(
        self,
        resume: Optional[List[str]] = None,
        pause: Optional[List[str]] = None,
    ) -> None:
        """
        Switch between active and paused channels.
        
        Data is only received for resumed channels. Subscribed channels
        must be resumed to start receiving data.
        
        Args:
            resume: List of channel numbers to resume (start receiving data)
            pause: List of channel numbers to pause (stop receiving data)
            
        Example:
            ```python
            # Start receiving data from channel 1
            await ws.switch_channel(resume=["1"])
            
            # Pause channel 1, resume channel 2
            await ws.switch_channel(resume=["2"], pause=["1"])
            
            # Resume multiple channels
            await ws.switch_channel(resume=["1", "2", "3"])
            ```
        """
        if not self._socket:
            raise RuntimeError("Not connected. Call connect() first.")
        
        resume_set = set(resume or [])
        pause_set = set(pause or [])
        
        # Update tracking
        self._active_channels.update(resume_set)
        self._active_channels.difference_update(pause_set)
        
        logger.info(f"Switching channels - Resume: {resume_set}, Pause: {pause_set}")
        
        await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: self._socket.switchChannel(
                resume_channels=resume_set,
                pause_channels=pause_set,
            )
        )
    
    async def close(self) -> None:
        """Close the TBT WebSocket connection."""
        if self._socket:
            logger.info("Closing TBT WebSocket connection")
            await asyncio.get_event_loop().run_in_executor(
                None, self._socket.close_connection
            )
            self._socket = None
            self._state = ConnectionState.DISCONNECTED
            self._subscribed_channels = {}
            self._active_channels = set()
    
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
    def subscribed_channels(self) -> Dict[str, Set[str]]:
        """Get subscribed channels and their symbols."""
        return {k: v.copy() for k, v in self._subscribed_channels.items()}
    
    @property
    def active_channels(self) -> Set[str]:
        """Get currently active (receiving data) channels."""
        return self._active_channels.copy()
    
    # ==================== Context Manager ====================
    
    async def __aenter__(self) -> "FyersTBTWebSocket":
        """Async context manager entry."""
        await self.connect()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Async context manager exit."""
        await self.close()


# ==================== Synchronous Wrapper ====================

class FyersTBTWebSocketSync:
    """
    Synchronous wrapper for Fyers TBT WebSocket.
    
    For use cases where async is not needed.
    
    Example:
        ```python
        def on_depth(ticker, depth):
            print(f"{ticker}: TBQ={depth.tbq}, TSQ={depth.tsq}")
        
        ws = FyersTBTWebSocketSync(
            access_token="your_token",
            on_depth_update=on_depth,
        )
        
        ws.connect()
        ws.subscribe(["NSE:NIFTY25MARFUT"], channel="1")
        ws.switch_channel(resume=["1"])
        ws.keep_running()  # Blocks
        ```
    """
    
    MAX_SYMBOLS_PER_CONNECTION = 5
    MAX_CHANNELS = 50
    
    def __init__(
        self,
        access_token: str,
        on_depth_update: Optional[Callable[[str, Depth], Any]] = None,
        on_error: Optional[Callable[[Dict[str, Any]], Any]] = None,
        on_error_message: Optional[Callable[[str], Any]] = None,
        on_connect: Optional[Callable[[], Any]] = None,
        on_close: Optional[Callable[[Dict[str, Any]], Any]] = None,
        config: Optional[TBTConfig] = None,
    ):
        """Initialize synchronous TBT WebSocket client."""
        self._access_token = access_token
        self._config = config or TBTConfig()
        
        self._on_depth_update = on_depth_update
        self._on_error = on_error
        self._on_error_message = on_error_message
        self._on_connect = on_connect
        self._on_close = on_close
        
        self._socket: Optional[FyersTbtSocket] = None
        self._subscribed_channels: Dict[str, Set[str]] = {}
        self._active_channels: Set[str] = set()
    
    def connect(self) -> None:
        """Establish TBT WebSocket connection."""
        self._socket = FyersTbtSocket(
            access_token=self._access_token,
            write_to_file=self._config.write_to_file,
            log_path=self._config.log_path,
            on_depth_update=self._on_depth_update,
            on_error_message=self._on_error_message,
            on_error=self._on_error,
            on_open=self._on_connect,
            on_close=self._on_close,
            reconnect=self._config.reconnect,
            diff_only=self._config.diff_only,
            reconnect_retry=self._config.max_reconnect_attempts,
        )
        self._socket.connect()
    
    def subscribe(
        self,
        symbols: List[str],
        channel: str = "1",
        mode: str = "depth",
    ) -> None:
        """Subscribe to symbols on a channel."""
        if self._socket:
            if channel not in self._subscribed_channels:
                self._subscribed_channels[channel] = set()
            self._subscribed_channels[channel].update(symbols)
            
            self._socket.subscribe(
                symbol_tickers=set(symbols),
                channelNo=channel,
                mode=SubscriptionModes.DEPTH,
            )
    
    def unsubscribe(
        self,
        symbols: List[str],
        channel: str = "1",
        mode: str = "depth",
    ) -> None:
        """Unsubscribe from symbols."""
        if self._socket:
            if channel in self._subscribed_channels:
                self._subscribed_channels[channel].difference_update(symbols)
            
            self._socket.unsubscribe(
                symbol_tickers=set(symbols),
                channelNo=channel,
                mode=SubscriptionModes.DEPTH,
            )
    
    def switch_channel(
        self,
        resume: Optional[List[str]] = None,
        pause: Optional[List[str]] = None,
    ) -> None:
        """Switch between active and paused channels."""
        if self._socket:
            resume_set = set(resume or [])
            pause_set = set(pause or [])
            
            self._active_channels.update(resume_set)
            self._active_channels.difference_update(pause_set)
            
            self._socket.switchChannel(
                resume_channels=resume_set,
                pause_channels=pause_set,
            )
    
    def close(self) -> None:
        """Close connection."""
        if self._socket:
            self._socket.close_connection()
            self._socket = None
            self._subscribed_channels = {}
            self._active_channels = set()
    
    def keep_running(self) -> None:
        """Keep connection running (blocks)."""
        if self._socket:
            self._socket.keep_running()
    
    @property
    def is_connected(self) -> bool:
        """Check if connected."""
        return self._socket.is_connected() if self._socket else False