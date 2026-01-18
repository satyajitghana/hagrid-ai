"""
WebSocket Models for Fyers API.

This module contains Pydantic models for WebSocket events including:
- Order updates
- Trade updates
- Position updates
- Market data updates (symbol, depth, index)
"""

from datetime import datetime
from enum import IntEnum, Enum
from typing import Optional, Any, Dict, List
from pydantic import BaseModel, Field


# ==================== Enums ====================
# NOTE: These enums are specific to WebSocket protocol and may have different
# values than REST API enums in models/enums.py. The WebSocket binary protocol
# uses its own encoding scheme. Do not consolidate with models/enums.py.

class OrderStatus(IntEnum):
    """Order status codes from Fyers WebSocket."""
    CANCELLED = 1
    TRADED = 2
    # 3 is not used currently
    TRANSIT = 4
    REJECTED = 5
    PENDING = 6
    EXPIRED = 7


class OrderSide(IntEnum):
    """Order side - buy or sell."""
    BUY = 1
    SELL = -1


class Segment(IntEnum):
    """Exchange segment codes for WebSocket protocol."""
    EQUITY = 10       # E (Equity)
    FNO = 11          # D (F&O)
    CURRENCY = 12     # C (Currency)
    COMMODITY = 20    # M (Commodity)


class Exchange(IntEnum):
    """Exchange codes for WebSocket protocol."""
    NSE = 10
    BSE = 20
    MCX = 30


class OrderType(IntEnum):
    """Order type codes."""
    LIMIT = 1
    MARKET = 2
    STOP = 3       # SL-M
    STOP_LIMIT = 4 # SL-L


class DataType(str, Enum):
    """Market data types for WebSocket subscription."""
    SYMBOL_UPDATE = "SymbolUpdate"
    DEPTH_UPDATE = "DepthUpdate"


class SubscriptionType(str, Enum):
    """Order WebSocket subscription types."""
    ORDERS = "OnOrders"
    TRADES = "OnTrades"
    POSITIONS = "OnPositions"
    GENERAL = "OnGeneral"


# ==================== Order WebSocket Models ====================

class OrderUpdate(BaseModel):
    """
    Model for order update events from WebSocket.
    
    Attributes match the Fyers order update response structure.
    """
    client_id: Optional[str] = Field(None, alias="clientId", description="Client ID")
    id: str = Field(..., description="Unique order ID")
    parent_id: Optional[str] = Field(None, alias="parentId", description="Parent order ID for BO/CO")
    exchange_order_id: Optional[str] = Field(None, alias="exchOrdId", description="Exchange order ID")
    symbol: str = Field(..., description="Symbol in Fyers format (e.g., NSE:SBIN-EQ)")
    qty: int = Field(..., description="Original order quantity")
    remaining_quantity: Optional[int] = Field(None, alias="remainingQuantity", description="Remaining quantity")
    filled_qty: Optional[int] = Field(None, alias="filledQty", description="Filled quantity")
    limit_price: Optional[float] = Field(None, alias="limitPrice", description="Limit price")
    stop_price: Optional[float] = Field(None, alias="stopPrice", description="Stop/trigger price")
    traded_price: Optional[float] = Field(None, alias="tradedPrice", description="Average traded price")
    status: int = Field(..., description="Order status code")
    message: Optional[str] = Field(None, description="Status/error message")
    segment: int = Field(..., description="Segment code (10=Equity, 11=F&O, etc.)")
    product_type: str = Field(..., alias="productType", description="Product type (INTRADAY, CNC, etc.)")
    order_type: int = Field(..., alias="type", description="Order type (1=Limit, 2=Market, etc.)")
    side: int = Field(..., description="Side (1=Buy, -1=Sell)")
    order_validity: str = Field(..., alias="orderValidity", description="Order validity (DAY, IOC)")
    order_datetime: str = Field(..., alias="orderDateTime", description="Order time in IST")
    source: Optional[str] = Field(None, description="Order source (W=Web, M=Mobile, etc.)")
    fy_token: Optional[str] = Field(None, alias="fyToken", description="Fyers unique token")
    offline_order: bool = Field(False, alias="offlineOrder", description="True for AMO orders")
    pan: Optional[str] = Field(None, description="Client PAN")
    exchange: int = Field(..., description="Exchange code")
    instrument: Optional[int] = Field(None, description="Instrument type")
    ex_sym: Optional[str] = Field(None, alias="ex_sym", description="Exchange symbol")
    description: Optional[str] = Field(None, description="Symbol description")
    order_num_status: Optional[str] = Field(None, alias="orderNumStatus", description="Order ID:Status")
    
    class Config:
        populate_by_name = True
        
    @property
    def status_name(self) -> str:
        """Get human-readable status name."""
        status_map = {
            1: "Cancelled",
            2: "Traded",
            4: "Transit",
            5: "Rejected",
            6: "Pending",
            7: "Expired",
        }
        return status_map.get(self.status, f"Unknown ({self.status})")
    
    @property
    def is_buy(self) -> bool:
        """Check if this is a buy order."""
        return self.side == OrderSide.BUY
    
    @property
    def is_complete(self) -> bool:
        """Check if order is complete (traded/cancelled/rejected/expired)."""
        return self.status in [1, 2, 5, 7]


class TradeUpdate(BaseModel):
    """
    Model for trade update events from WebSocket.
    """
    symbol: str = Field(..., description="Symbol in Fyers format")
    id: Optional[str] = Field(None, description="Unique trade ID")
    trade_number: str = Field(..., alias="tradeNumber", description="Trade number from exchange")
    order_number: str = Field(..., alias="orderNumber", description="Associated order ID")
    order_datetime: str = Field(..., alias="orderDateTime", description="Trade time")
    trade_price: float = Field(..., alias="tradePrice", description="Trade execution price")
    trade_value: float = Field(..., alias="tradeValue", description="Total trade value")
    traded_qty: int = Field(..., alias="tradedQty", description="Traded quantity")
    side: int = Field(..., description="Side (1=Buy, -1=Sell)")
    product_type: str = Field(..., alias="productType", description="Product type")
    exchange_order_no: Optional[str] = Field(None, alias="exchangeOrderNo", description="Exchange order number")
    segment: int = Field(..., description="Segment code")
    exchange: int = Field(..., description="Exchange code")
    fy_token: Optional[str] = Field(None, alias="fyToken", description="Fyers unique token")
    
    class Config:
        populate_by_name = True
    
    @property
    def is_buy(self) -> bool:
        """Check if this is a buy trade."""
        return self.side == OrderSide.BUY


class PositionUpdate(BaseModel):
    """
    Model for position update events from WebSocket.
    """
    symbol: str = Field(..., description="Symbol in Fyers format")
    id: str = Field(..., description="Position ID")
    buy_avg: float = Field(..., alias="buyAvg", description="Average buy price")
    buy_qty: int = Field(..., alias="buyQty", description="Total buy quantity")
    buy_val: Optional[float] = Field(None, alias="buyVal", description="Total buy value")
    sell_avg: float = Field(..., alias="sellAvg", description="Average sell price")
    sell_qty: int = Field(..., alias="sellQty", description="Total sell quantity")
    sell_val: Optional[float] = Field(None, alias="sellVal", description="Total sell value")
    net_avg: float = Field(..., alias="netAvg", description="Net average price")
    net_qty: int = Field(..., alias="netQty", description="Net quantity")
    side: int = Field(..., description="Position side (1=Long, -1=Short, 0=Closed)")
    qty: int = Field(..., description="Absolute quantity")
    product_type: str = Field(..., alias="productType", description="Product type")
    realized_profit: float = Field(..., alias="realized_profit", description="Realized P&L")
    unrealized_profit: Optional[float] = Field(None, alias="unrealized_profit", description="Unrealized P&L")
    pl: Optional[float] = Field(None, description="Total P&L")
    cross_currency: Optional[str] = Field(None, alias="crossCurrency", description="Cross currency flag")
    rbi_ref_rate: Optional[float] = Field(None, alias="rbiRefRate", description="RBI reference rate")
    qty_multi_com: Optional[float] = Field(None, alias="qtyMulti_com", description="Commodity multiplier")
    segment: int = Field(..., description="Segment code")
    exchange: int = Field(..., description="Exchange code")
    fy_token: Optional[str] = Field(None, alias="fyToken", description="Fyers unique token")
    cf_buy_qty: Optional[int] = Field(None, alias="cfBuyQty", description="Carry forward buy qty")
    cf_sell_qty: Optional[int] = Field(None, alias="cfSellQty", description="Carry forward sell qty")
    day_buy_qty: Optional[int] = Field(None, alias="dayBuyQty", description="Day buy qty")
    day_sell_qty: Optional[int] = Field(None, alias="daySellQty", description="Day sell qty")
    
    class Config:
        populate_by_name = True
    
    @property
    def is_long(self) -> bool:
        """Check if position is long."""
        return self.side == 1
    
    @property
    def is_short(self) -> bool:
        """Check if position is short."""
        return self.side == -1
    
    @property
    def is_closed(self) -> bool:
        """Check if position is closed."""
        return self.side == 0 or self.net_qty == 0


class GeneralUpdate(BaseModel):
    """
    Model for general update events (EDIS, price alerts, login).
    """
    data: Dict[str, Any] = Field(default_factory=dict, description="General update data")
    status: str = Field("ok", alias="s", description="Status")
    
    class Config:
        populate_by_name = True
        extra = "allow"


# ==================== Market Data WebSocket Models ====================

class SymbolUpdate(BaseModel):
    """
    Model for market data symbol updates.
    
    Contains real-time price data for subscribed symbols.
    """
    symbol: str = Field(..., description="Symbol in Fyers format")
    ltp: float = Field(..., description="Last traded price")
    prev_close_price: Optional[float] = Field(None, alias="prev_close_price", description="Previous close")
    high_price: Optional[float] = Field(None, alias="high_price", description="Day high")
    low_price: Optional[float] = Field(None, alias="low_price", description="Day low")
    open_price: Optional[float] = Field(None, alias="open_price", description="Day open")
    ch: Optional[float] = Field(None, description="Price change")
    chp: Optional[float] = Field(None, description="Price change percentage")
    vol_traded_today: Optional[int] = Field(None, alias="vol_traded_today", description="Volume traded")
    last_traded_time: Optional[int] = Field(None, alias="last_traded_time", description="Last trade time (epoch)")
    bid_size: Optional[int] = Field(None, alias="bid_size", description="Bid size")
    ask_size: Optional[int] = Field(None, alias="ask_size", description="Ask size")
    bid_price: Optional[float] = Field(None, alias="bid_price", description="Best bid price")
    ask_price: Optional[float] = Field(None, alias="ask_price", description="Best ask price")
    last_traded_qty: Optional[int] = Field(None, alias="last_traded_qty", description="Last traded quantity")
    tot_buy_qty: Optional[int] = Field(None, alias="tot_buy_qty", description="Total buy quantity")
    tot_sell_qty: Optional[int] = Field(None, alias="tot_sell_qty", description="Total sell quantity")
    avg_trade_price: Optional[float] = Field(None, alias="avg_trade_price", description="Average trade price")
    type: str = Field("sf", description="Message type (sf=symbol, if=index, dp=depth)")
    
    class Config:
        populate_by_name = True
    
    @property
    def spread(self) -> Optional[float]:
        """Calculate bid-ask spread."""
        if self.bid_price and self.ask_price:
            return self.ask_price - self.bid_price
        return None
    
    @property
    def change_positive(self) -> bool:
        """Check if price change is positive."""
        return (self.ch or 0) >= 0


class DepthUpdate(BaseModel):
    """
    Model for market depth (order book) updates.
    
    Contains 5 levels of bid/ask data.
    """
    symbol: str = Field(..., description="Symbol in Fyers format")
    
    # Bid prices (5 levels)
    bid_price1: Optional[float] = Field(None, alias="bid_price1")
    bid_price2: Optional[float] = Field(None, alias="bid_price2")
    bid_price3: Optional[float] = Field(None, alias="bid_price3")
    bid_price4: Optional[float] = Field(None, alias="bid_price4")
    bid_price5: Optional[float] = Field(None, alias="bid_price5")
    
    # Ask prices (5 levels)
    ask_price1: Optional[float] = Field(None, alias="ask_price1")
    ask_price2: Optional[float] = Field(None, alias="ask_price2")
    ask_price3: Optional[float] = Field(None, alias="ask_price3")
    ask_price4: Optional[float] = Field(None, alias="ask_price4")
    ask_price5: Optional[float] = Field(None, alias="ask_price5")
    
    # Bid sizes (5 levels)
    bid_size1: Optional[int] = Field(None, alias="bid_size1")
    bid_size2: Optional[int] = Field(None, alias="bid_size2")
    bid_size3: Optional[int] = Field(None, alias="bid_size3")
    bid_size4: Optional[int] = Field(None, alias="bid_size4")
    bid_size5: Optional[int] = Field(None, alias="bid_size5")
    
    # Ask sizes (5 levels)
    ask_size1: Optional[int] = Field(None, alias="ask_size1")
    ask_size2: Optional[int] = Field(None, alias="ask_size2")
    ask_size3: Optional[int] = Field(None, alias="ask_size3")
    ask_size4: Optional[int] = Field(None, alias="ask_size4")
    ask_size5: Optional[int] = Field(None, alias="ask_size5")
    
    # Order counts (5 levels)
    bid_order1: Optional[int] = Field(None, alias="bid_order1")
    bid_order2: Optional[int] = Field(None, alias="bid_order2")
    bid_order3: Optional[int] = Field(None, alias="bid_order3")
    bid_order4: Optional[int] = Field(None, alias="bid_order4")
    bid_order5: Optional[int] = Field(None, alias="bid_order5")
    
    ask_order1: Optional[int] = Field(None, alias="ask_order1")
    ask_order2: Optional[int] = Field(None, alias="ask_order2")
    ask_order3: Optional[int] = Field(None, alias="ask_order3")
    ask_order4: Optional[int] = Field(None, alias="ask_order4")
    ask_order5: Optional[int] = Field(None, alias="ask_order5")
    
    type: str = Field("dp", description="Message type")
    
    class Config:
        populate_by_name = True
    
    @property
    def bids(self) -> List[Dict[str, Any]]:
        """Get list of bid levels."""
        bids = []
        for i in range(1, 6):
            price = getattr(self, f"bid_price{i}", None)
            size = getattr(self, f"bid_size{i}", None)
            orders = getattr(self, f"bid_order{i}", None)
            if price is not None:
                bids.append({"price": price, "size": size, "orders": orders})
        return bids
    
    @property
    def asks(self) -> List[Dict[str, Any]]:
        """Get list of ask levels."""
        asks = []
        for i in range(1, 6):
            price = getattr(self, f"ask_price{i}", None)
            size = getattr(self, f"ask_size{i}", None)
            orders = getattr(self, f"ask_order{i}", None)
            if price is not None:
                asks.append({"price": price, "size": size, "orders": orders})
        return asks


class IndexUpdate(BaseModel):
    """
    Model for index data updates.
    """
    symbol: str = Field(..., description="Index symbol")
    ltp: float = Field(..., description="Last traded value")
    prev_close_price: Optional[float] = Field(None, alias="prev_close_price", description="Previous close")
    high_price: Optional[float] = Field(None, alias="high_price", description="Day high")
    low_price: Optional[float] = Field(None, alias="low_price", description="Day low")
    open_price: Optional[float] = Field(None, alias="open_price", description="Day open")
    ch: Optional[float] = Field(None, description="Change")
    chp: Optional[float] = Field(None, description="Change percentage")
    exch_feed_time: Optional[int] = Field(None, alias="exch_feed_time", description="Exchange feed time")
    type: str = Field("if", description="Message type (if=index)")
    
    class Config:
        populate_by_name = True


# ==================== Generic WebSocket Message ====================

class WebSocketMessage(BaseModel):
    """
    Generic WebSocket message container.
    
    Used for wrapping different types of WebSocket messages.
    """
    status: str = Field("ok", alias="s", description="Message status")
    orders: Optional[OrderUpdate] = None
    trades: Optional[TradeUpdate] = None
    positions: Optional[PositionUpdate] = None
    data: Optional[Dict[str, Any]] = None
    
    class Config:
        populate_by_name = True
    
    @property
    def message_type(self) -> str:
        """Determine the type of message."""
        if self.orders:
            return "order"
        elif self.trades:
            return "trade"
        elif self.positions:
            return "position"
        else:
            return "general"


# ==================== Connection State Models ====================

class ConnectionState(str, Enum):
    """WebSocket connection states."""
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    RECONNECTING = "reconnecting"
    ERROR = "error"


class WebSocketConfig(BaseModel):
    """Configuration for WebSocket connections."""
    reconnect: bool = Field(True, description="Enable auto-reconnect")
    max_reconnect_attempts: int = Field(50, description="Maximum reconnection attempts")
    reconnect_delay: int = Field(5, description="Delay between reconnection attempts (seconds)")
    write_to_file: bool = Field(False, description="Write messages to log file")
    log_path: Optional[str] = Field(None, description="Path for log files")
    lite_mode: bool = Field(False, description="Enable lite mode for data socket (LTP only)")