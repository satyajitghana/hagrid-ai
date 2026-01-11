"""
Pydantic models for Fyers API responses.
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any, Union

# Import enums from the enums module
from broker.fyers.models.enums import (
    OrderType,
    OrderSide,
    OrderStatus,
    PositionSide,
    Segment,
    Exchange,
    ProductType,
    OrderValidity,
    HoldingType,
    OrderSource,
)


# ==================== Profile ====================

class ProfileData(BaseModel):
    """
    User profile data from Fyers API.
    
    Contains user information including name, ID, email, and various
    account settings and statuses.
    
    Note: As per Fyers privacy policy, PII (Personally Identifiable Information)
    may be masked to safeguard customer information.
    """
    name: str = Field(..., description="Name of the client")
    display_name: Optional[str] = Field(None, description="Display name, if any, provided by the client")
    fy_id: str = Field(..., description="The client ID of the fyers user")
    image: Optional[str] = Field(None, description="URL link to the user's profile picture, if any")
    email_id: str = Field(..., description="Email address of the client")
    pan: Optional[str] = Field(None, description="PAN of the client (may be masked)")
    pin_change_date: Optional[str] = Field(None, description="Date when last PIN was updated")
    pwd_change_date: Optional[str] = Field(None, description="Date when last password was updated")
    mobile_number: Optional[str] = Field(None, description="Registered mobile number (may be masked)")
    totp: Optional[bool] = Field(None, description="Status of TOTP")
    pwd_to_expire: Optional[int] = Field(None, description="Number of days until the current password expires")
    ddpi_enabled: Optional[bool] = Field(None, description="Status of DDPI")
    mtf_enabled: Optional[bool] = Field(None, description="Status of MTF")
    
    class Config:
        """Pydantic model configuration."""
        populate_by_name = True
        extra = "ignore"  # Ignore extra fields from API


class ProfileResponse(BaseModel):
    """
    Profile API response.
    
    This endpoint can be used to verify if a token is valid by checking
    if it returns the user's profile successfully.
    """
    s: str = Field(..., description="Status: ok/error")
    code: int = Field(..., description="Response code")
    message: Optional[str] = Field("", description="Response message")
    data: Optional[ProfileData] = Field(None, description="Profile data")

    def is_success(self) -> bool:
        """Check if the response indicates success."""
        return self.s == "ok" and self.code == 200
    
    @property
    def user_name(self) -> Optional[str]:
        """Get the user's name."""
        return self.data.name if self.data else None
    
    @property
    def user_id(self) -> Optional[str]:
        """Get the Fyers user ID."""
        return self.data.fy_id if self.data else None
    
    @property
    def email(self) -> Optional[str]:
        """Get the user's email."""
        return self.data.email_id if self.data else None


# ==================== Funds ====================

class FundItem(BaseModel):
    """Individual fund item."""
    id: int = Field(..., description="Unique identity for fund")
    title: str = Field(..., description="Ledger heading")
    equityAmount: float = Field(..., description="Capital ledger amount")
    commodityAmount: float = Field(..., description="Commodity ledger amount")


class FundsResponse(BaseModel):
    """Funds API response."""
    s: str = Field(..., description="Status: ok/error")
    code: int = Field(..., description="Response code")
    message: Optional[str] = Field("", description="Response message")
    fund_limit: Optional[List[FundItem]] = Field(None, description="Fund limits")

    def is_success(self) -> bool:
        return self.s == "ok" and self.code == 200

    def get_available_balance(self) -> float:
        """Get available balance for equity."""
        if self.fund_limit:
            for item in self.fund_limit:
                if item.id == 10:  # Available Balance
                    return item.equityAmount
        return 0.0

    def get_total_balance(self) -> float:
        """Get total balance for equity."""
        if self.fund_limit:
            for item in self.fund_limit:
                if item.id == 1:  # Total Balance
                    return item.equityAmount
        return 0.0


# ==================== Holdings ====================

class HoldingItem(BaseModel):
    """Individual holding item."""
    symbol: str = Field(..., description="Symbol (e.g., NSE:RCOM-EQ)")
    holdingType: str = Field(..., description="Type of holding (T1 or HLD)")
    quantity: int = Field(..., description="Quantity at beginning of day")
    remainingQuantity: int = Field(..., description="Remaining quantity")
    pl: float = Field(..., description="Profit and loss")
    costPrice: float = Field(..., description="Original buy price")
    marketVal: float = Field(..., description="Market value")
    ltp: float = Field(..., description="Last traded price")
    id: int = Field(..., description="Unique ID")
    fytoken: Optional[str] = Field(None, alias="fyToken", description="Fytoken")
    exchange: int = Field(..., description="Exchange (10=NSE, 11=MCX, 12=BSE)")
    segment: int = Field(..., description="Segment (10=CM, 11=FO, 12=CD, 20=COM)")
    isin: Optional[str] = Field(None, description="ISIN")
    qty_t1: Optional[int] = Field(0, description="T+1 quantity")
    remainingPledgeQuantity: Optional[int] = Field(0, description="Remaining pledged quantity")
    collateralQuantity: Optional[int] = Field(0, description="Pledged quantity")


class HoldingsOverall(BaseModel):
    """Overall holdings summary."""
    count_total: int = Field(..., description="Total holdings count")
    total_investment: float = Field(..., description="Total investment")
    total_current_value: float = Field(..., description="Current value")
    total_pl: float = Field(..., description="Total P&L")
    pnl_perc: float = Field(..., description="P&L percentage")


class HoldingsResponse(BaseModel):
    """Holdings API response."""
    s: str = Field(..., description="Status: ok/error")
    code: int = Field(..., description="Response code")
    message: Optional[str] = Field("", description="Response message")
    holdings: Optional[List[HoldingItem]] = Field(None, description="Holdings list")
    overall: Optional[HoldingsOverall] = Field(None, description="Overall summary")

    def is_success(self) -> bool:
        return self.s == "ok" and self.code == 200
    
    @property
    def dataframe(self) -> "pd.DataFrame":
        """Get holdings as DataFrame."""
        try:
            import pandas as pd
        except ImportError:
            raise ImportError("pandas required. Install: pip install pandas")
        
        if not self.holdings:
            return pd.DataFrame()
        
        return pd.DataFrame([h.model_dump() for h in self.holdings])


# ==================== Orders ====================

class OrderItem(BaseModel):
    """Individual order item."""
    id: str = Field(..., description="Unique order ID")
    exchOrdId: Optional[str] = Field(None, description="Exchange order ID")
    id_fyers: Optional[str] = Field(None, description="Fyers system order ID")
    symbol: str = Field(..., description="Symbol")
    qty: int = Field(..., description="Original quantity")
    remainingQuantity: int = Field(..., description="Remaining quantity")
    filledQty: int = Field(..., description="Filled quantity")
    status: int = Field(..., description="Order status (1=Cancelled, 2=Traded, 4=Transit, 5=Rejected, 6=Pending)")
    slNo: Optional[int] = Field(None, description="Sorting number")
    message: Optional[str] = Field("", description="Error messages")
    segment: int = Field(..., description="Segment (10=CM, 11=FO, 12=CD, 20=COM)")
    limitPrice: float = Field(..., description="Limit price")
    stopPrice: float = Field(..., description="Stop price")
    productType: str = Field(..., description="Product type (CNC, INTRADAY, MARGIN, CO, BO, MTF)")
    type: int = Field(..., description="Order type (1=Limit, 2=Market, 3=Stop, 4=StopLimit)")
    side: int = Field(..., description="Order side (1=Buy, -1=Sell)")
    disclosedQty: int = Field(0, description="Disclosed quantity")
    orderValidity: str = Field(..., description="Order validity (DAY, IOC)")
    orderDateTime: str = Field(..., description="Order date/time")
    parentId: Optional[str] = Field(None, description="Parent order ID")
    tradedPrice: float = Field(0, description="Average traded price")
    source: Optional[str] = Field(None, description="Order source (M=Mobile, W=Web, R=Fyers One, A=Admin, ITS=API)")
    fytoken: Optional[str] = Field(None, alias="fyToken", description="Fytoken")
    offlineOrder: bool = Field(False, description="Is AMO order")
    pan: Optional[str] = Field(None, description="PAN")
    clientId: Optional[str] = Field(None, description="Client ID")
    exchange: int = Field(..., description="Exchange (10=NSE, 11=MCX, 12=BSE)")
    instrument: Optional[int] = Field(None, description="Instrument type")
    orderTag: Optional[str] = Field(None, description="Order tag")
    takeProfit: float = Field(0, description="Take profit for BO")
    stopLoss: float = Field(0, description="Stop loss for BO/CO")

    def is_filled(self) -> bool:
        return self.status == OrderStatus.TRADED

    def is_pending(self) -> bool:
        return self.status == OrderStatus.PENDING

    def is_cancelled(self) -> bool:
        return self.status == OrderStatus.CANCELLED


class OrdersResponse(BaseModel):
    """Orders API response."""
    s: str = Field(..., description="Status: ok/error")
    code: int = Field(..., description="Response code")
    message: Optional[str] = Field("", description="Response message")
    orderBook: Optional[List[OrderItem]] = Field(None, description="Order book")

    def is_success(self) -> bool:
        return self.s == "ok" and self.code == 200
    
    @property
    def dataframe(self) -> "pd.DataFrame":
        """Get orders as DataFrame."""
        try:
            import pandas as pd
        except ImportError:
            raise ImportError("pandas required. Install: pip install pandas")
        
        if not self.orderBook:
            return pd.DataFrame()
        
        return pd.DataFrame([o.model_dump() for o in self.orderBook])


# ==================== Positions ====================

class PositionItem(BaseModel):
    """Individual position item."""
    symbol: str = Field(..., description="Symbol")
    id: str = Field(..., description="Unique position ID")
    buyAvg: float = Field(..., description="Average buy price")
    buyQty: int = Field(..., description="Total buy quantity")
    sellAvg: float = Field(..., description="Average sell price")
    sellQty: int = Field(..., description="Total sell quantity")
    netAvg: float = Field(..., description="Net average")
    netQty: int = Field(..., description="Net quantity")
    side: int = Field(..., description="Position side (1=Long, -1=Short, 0=Closed)")
    qty: int = Field(..., description="Absolute net quantity")
    productType: str = Field(..., description="Product type")
    realized_profit: float = Field(..., description="Realized P&L")
    unrealized_profit: Optional[float] = Field(0, description="Unrealized P&L")
    pl: float = Field(..., description="Total P&L")
    crossCurrency: str = Field("N", description="Cross currency position")
    rbiRefRate: float = Field(1.0, description="RBI reference rate")
    qtyMulti_com: float = Field(1.0, description="Commodity multiplier")
    segment: int = Field(..., description="Segment (10=CM, 11=FO, 12=CD, 20=COM)")
    exchange: int = Field(..., description="Exchange (10=NSE, 11=MCX, 12=BSE)")
    slNo: int = Field(0, description="Sorting number")
    ltp: float = Field(..., description="Last traded price")
    fytoken: Optional[str] = Field(None, alias="fyToken", description="Fytoken")
    cfBuyQty: int = Field(0, description="Carry forward buy quantity")
    cfSellQty: int = Field(0, description="Carry forward sell quantity")
    dayBuyQty: int = Field(0, description="Day buy quantity")
    daySellQty: int = Field(0, description="Day sell quantity")

    def is_long(self) -> bool:
        return self.side == PositionSide.LONG

    def is_short(self) -> bool:
        return self.side == PositionSide.SHORT


class PositionsOverall(BaseModel):
    """Overall positions summary."""
    count_total: int = Field(..., description="Total positions")
    count_open: int = Field(..., description="Open positions")
    pl_total: float = Field(..., description="Total P&L")
    pl_realized: float = Field(..., description="Realized P&L")
    pl_unrealized: float = Field(..., description="Unrealized P&L")


class PositionsResponse(BaseModel):
    """Positions API response."""
    s: str = Field(..., description="Status: ok/error")
    code: int = Field(..., description="Response code")
    message: Optional[str] = Field("", description="Response message")
    netPositions: Optional[List[PositionItem]] = Field(None, description="Positions list")
    overall: Optional[PositionsOverall] = Field(None, description="Overall summary")

    def is_success(self) -> bool:
        return self.s == "ok" and self.code == 200
    
    @property
    def dataframe(self) -> "pd.DataFrame":
        """Get positions as DataFrame."""
        try:
            import pandas as pd
        except ImportError:
            raise ImportError("pandas required. Install: pip install pandas")
        
        if not self.netPositions:
            return pd.DataFrame()
        
        return pd.DataFrame([p.model_dump() for p in self.netPositions])


# ==================== Trades ====================

class TradeItem(BaseModel):
    """Individual trade item."""
    symbol: str = Field(..., description="Symbol")
    row: int = Field(..., description="Trade row for sorting")
    orderDateTime: str = Field(..., description="Trade time")
    orderNumber: str = Field(..., description="Order ID")
    tradeNumber: str = Field(..., description="Exchange trade number")
    tradePrice: float = Field(..., description="Trade price")
    tradeValue: float = Field(..., description="Trade value")
    tradedQty: int = Field(..., description="Traded quantity")
    side: int = Field(..., description="Trade side (1=Buy, -1=Sell)")
    productType: str = Field(..., description="Product type")
    exchangeOrderNo: str = Field(..., description="Exchange order number")
    segment: int = Field(..., description="Segment (10=CM, 11=FO, 12=CD, 20=COM)")
    exchange: int = Field(..., description="Exchange (10=NSE, 11=MCX, 12=BSE)")
    fyToken: Optional[str] = Field(None, description="Fytoken")
    orderTag: Optional[str] = Field(None, description="Order tag")
    clientId: Optional[str] = Field(None, description="Client ID")
    orderType: Optional[int] = Field(None, description="Order type")


class TradesResponse(BaseModel):
    """Trades API response."""
    s: str = Field(..., description="Status: ok/error")
    code: int = Field(..., description="Response code")
    message: Optional[str] = Field("", description="Response message")
    tradeBook: Optional[List[TradeItem]] = Field(None, description="Trade book")

    def is_success(self) -> bool:
        return self.s == "ok" and self.code == 200
    
    @property
    def dataframe(self) -> "pd.DataFrame":
        """Get trades as DataFrame."""
        try:
            import pandas as pd
        except ImportError:
            raise ImportError("pandas required. Install: pip install pandas")
        
        if not self.tradeBook:
            return pd.DataFrame()
        
        return pd.DataFrame([t.model_dump() for t in self.tradeBook])


# ==================== Order Placement ====================

class OrderPlacementResponse(BaseModel):
    """Single order placement response."""
    s: str = Field(..., description="Status: ok/error")
    code: int = Field(..., description="Response code")
    message: str = Field(..., description="Response message")
    id: Optional[str] = Field(None, description="Order ID")

    def is_success(self) -> bool:
        return self.s == "ok" and self.code == 1101


class MultiOrderItemResponse(BaseModel):
    """Individual multi-order response item."""
    statusCode: int = Field(..., description="HTTP status code")
    body: OrderPlacementResponse = Field(..., description="Order response body")
    statusDescription: str = Field(..., description="Status description")


class MultiOrderResponse(BaseModel):
    """Multi-order placement response."""
    s: str = Field(..., description="Status: ok/error")
    code: int = Field(..., description="Response code")
    message: str = Field("", description="Response message")
    data: Optional[List[MultiOrderItemResponse]] = Field(None, description="Order responses")

    def is_success(self) -> bool:
        return self.s == "ok" and self.code == 200

    def get_order_ids(self) -> List[str]:
        """Get all successful order IDs."""
        if not self.data:
            return []
        return [
            item.body.id for item in self.data
            if item.body.id and item.body.is_success()
        ]


class OrderModifyResponse(BaseModel):
    """Order modification response."""
    s: str = Field(..., description="Status: ok/error")
    code: int = Field(..., description="Response code")
    message: str = Field(..., description="Response message")
    id: Optional[str] = Field(None, description="Order ID")

    def is_success(self) -> bool:
        return self.s == "ok" and self.code == 1102


class OrderCancelResponse(BaseModel):
    """Order cancellation response."""
    s: str = Field(..., description="Status: ok/error")
    code: int = Field(..., description="Response code")
    message: str = Field(..., description="Response message")
    id: Optional[str] = Field(None, description="Order ID")

    def is_success(self) -> bool:
        return self.s == "ok" and self.code == 1103


# ==================== Logout ====================

class LogoutResponse(BaseModel):
    """Logout API response."""
    s: str = Field(..., description="Status: ok/error")
    code: int = Field(..., description="Response code")
    message: str = Field(..., description="Response message")

    def is_success(self) -> bool:
        return self.s == "ok" and self.code == 200


# ==================== History ====================

class HistoryResponse(BaseModel):
    """History API response."""
    s: str = Field(..., description="Status: ok/error")
    candles: Optional[List[List[Union[float, int]]]] = Field(None, description="Candle data")
    next_page: Optional[int] = Field(None, description="Next page cursor")
    prev_page: Optional[int] = Field(None, description="Previous page cursor")

    def is_success(self) -> bool:
        return self.s == "ok"
    
    @property
    def dataframe(self) -> "pd.DataFrame":
        """
        Get historical candles as pandas DataFrame.
        
        Example:
            ```python
            history = await client.get_history(...)
            df = history.dataframe  # Instant conversion!
            print(df[['datetime', 'open', 'high', 'low', 'close', 'volume']])
            ```
        """
        try:
            import pandas as pd
        except ImportError:
            raise ImportError("pandas required for .dataframe property. Install: pip install pandas")
        
        if not self.candles:
            return pd.DataFrame()
        
        columns = ["epoch", "open", "high", "low", "close", "volume"]
        if self.candles and len(self.candles[0]) > 6:
            columns.append("oi")
        
        df = pd.DataFrame(self.candles, columns=columns[:len(self.candles[0])])
        df["datetime"] = pd.to_datetime(df["epoch"], unit="s", utc=True).dt.tz_convert('Asia/Kolkata')
        
        return df


# ==================== Market Data Responses ====================

class QuoteData(BaseModel):
    """Individual quote data."""
    n: str = Field(..., description="Symbol name")
    s: str = Field(..., description="Status")
    v: Dict[str, Any] = Field(..., description="Quote values")


class QuotesResponse(BaseModel):
    """Quotes API response."""
    s: str = Field(..., description="Status: ok/error")
    code: int = Field(..., description="Response code")
    d: Optional[List[QuoteData]] = Field(None, description="Quote data list")

    def is_success(self) -> bool:
        return self.s == "ok" and self.code == 200


class MarketDepthLevel(BaseModel):
    """Market depth level (bid/ask)."""
    price: float = Field(..., description="Price")
    volume: int = Field(..., description="Volume")
    ord: int = Field(..., description="Number of orders")


class MarketDepthData(BaseModel):
    """Market depth data for a symbol."""
    totalbuyqty: int = Field(..., description="Total buy quantity")
    totalsellqty: int = Field(..., description="Total sell quantity")
    bids: List[MarketDepthLevel] = Field(..., description="Bid levels")
    ask: List[MarketDepthLevel] = Field(..., description="Ask levels")
    o: float = Field(..., description="Open price")
    h: float = Field(..., description="High price")
    l: float = Field(..., description="Low price")
    c: float = Field(..., description="Close price")
    chp: float = Field(..., description="Change percentage")
    tick_Size: float = Field(..., alias="tick_Size", description="Tick size")
    ch: float = Field(..., description="Change")
    ltq: int = Field(..., description="Last traded quantity")
    ltt: int = Field(..., description="Last traded time")
    ltp: float = Field(..., description="Last traded price")
    v: int = Field(..., description="Volume")
    atp: float = Field(..., description="Average traded price")
    lower_ckt: float = Field(..., description="Lower circuit limit")
    upper_ckt: float = Field(..., description="Upper circuit limit")
    expiry: str = Field("", description="Expiry date")
    oi: float = Field(0, description="Open interest")
    oiflag: bool = Field(False, description="OI flag")
    pdoi: int = Field(0, description="Previous day OI")
    oipercent: float = Field(0, description="OI change percentage")


class MarketDepthResponse(BaseModel):
    """Market Depth API response."""
    s: str = Field(..., description="Status: ok/error")
    d: Dict[str, MarketDepthData] = Field(..., description="Depth data by symbol")
    message: str = Field("", description="Response message")

    def is_success(self) -> bool:
        return self.s == "ok"


class MarketStatusItem(BaseModel):
    """Market status for exchange/segment."""
    exchange: int = Field(..., description="Exchange code")
    market_type: str = Field(..., description="Market type")
    segment: int = Field(..., description="Segment code")
    status: str = Field(..., description="Market status")


class MarketStatusResponse(BaseModel):
    """Market Status API response."""
    s: str = Field(..., description="Status: ok/error")
    code: int = Field(..., description="Response code")
    message: str = Field("", description="Response message")
    marketStatus: Optional[List[MarketStatusItem]] = Field(None, description="Market status list")

    def is_success(self) -> bool:
        return self.s == "ok" and self.code == 200


class MarginCalculation(BaseModel):
    """Margin calculation result."""
    margin_avail: float = Field(..., description="Available margin")
    margin_total: float = Field(..., description="Total margin required")
    margin_new_order: float = Field(..., description="Margin for new order including positions")


class MarginResponse(BaseModel):
    """Margin calculator API response."""
    s: str = Field(..., description="Status: ok/error")
    code: int = Field(..., description="Response code")
    message: str = Field("", description="Response message")
    data: Optional[MarginCalculation] = Field(None, description="Margin data")

    def is_success(self) -> bool:
        return self.s == "ok" and self.code == 200


# ==================== GTT Orders ====================

class GTTOrderItem(BaseModel):
    """Individual GTT order item."""
    clientId: Optional[str] = Field(None, description="Client ID")
    exchange: int = Field(..., description="Exchange")
    fy_token: str = Field(..., description="Fytoken")
    id_fyers: str = Field(..., description="Fyers system ID")
    id: str = Field(..., description="Order ID")
    instrument: int = Field(..., description="Instrument type")
    lot_size: int = Field(..., description="Lot size")
    multiplier: int = Field(..., description="Multiplier")
    ord_status: int = Field(..., description="Order status")
    precision: int = Field(..., description="Precision")
    price_limit: float = Field(..., description="Leg1 limit price")
    price2_limit: Optional[float] = Field(None, description="Leg2 limit price")
    price_trigger: float = Field(..., description="Leg1 trigger price")
    price2_trigger: Optional[float] = Field(None, description="Leg2 trigger price")
    product_type: str = Field(..., description="Product type")
    qty: int = Field(..., description="Leg1 quantity")
    qty2: Optional[int] = Field(None, description="Leg2 quantity")
    report_type: str = Field(..., description="Report type")
    segment: int = Field(..., description="Segment")
    symbol: str = Field(..., description="Symbol")
    symbol_desc: str = Field(..., description="Symbol description")
    symbol_exch: str = Field(..., description="Exchange symbol")
    tick_size: float = Field(..., description="Tick size")
    tran_side: int = Field(..., description="Transaction side")
    gtt_oco_ind: int = Field(..., description="GTT/OCO indicator (1=GTT, 2=OCO)")
    create_time: str = Field(..., description="Creation time")
    create_time_epoch: int = Field(..., description="Creation epoch")
    oms_msg: str = Field(..., description="OMS message")
    ltp_ch: float = Field(0, description="LTP change")
    ltp_chp: float = Field(0, description="LTP change percentage")
    ltp: float = Field(0, description="Last traded price")


class GTTOrdersResponse(BaseModel):
    """GTT Orders API response."""
    s: str = Field(..., description="Status: ok/error")
    code: int = Field(..., description="Response code")
    message: str = Field("", description="Response message")
    orderBook: Optional[List[GTTOrderItem]] = Field(None, description="GTT order book")

    def is_success(self) -> bool:
        return self.s == "ok" and self.code == 200


# ==================== Option Chain ====================

class ExpiryData(BaseModel):
    """Expiry date information."""
    date: str = Field(..., description="Expiry date (DD-MM-YYYY)")
    expiry: str = Field(..., description="Expiry timestamp")


class IndiaVIXData(BaseModel):
    """India VIX data."""
    ask: float = Field(0, description="Ask price")
    bid: float = Field(0, description="Bid price")
    description: str = Field(..., description="Description")
    ex_symbol: str = Field(..., description="Exchange symbol")
    exchange: str = Field(..., description="Exchange")
    fyToken: str = Field(..., description="Fytoken")
    ltp: float = Field(..., description="Last traded price")
    ltpch: float = Field(..., description="LTP change")
    ltpchp: float = Field(..., description="LTP change percentage")
    option_type: str = Field("", description="Option type")
    strike_price: int = Field(-1, description="Strike price")
    symbol: str = Field(..., description="Symbol")


class OptionContractData(BaseModel):
    """Individual option contract data."""
    ask: float = Field(..., description="Ask price")
    bid: float = Field(..., description="Bid price")
    fyToken: str = Field(..., description="Fytoken")
    ltp: float = Field(..., description="Last traded price")
    ltpch: Optional[float] = Field(None, description="LTP change")
    ltpchp: Optional[float] = Field(None, description="LTP change percentage")
    oi: Optional[int] = Field(None, description="Open interest")
    oich: Optional[int] = Field(None, description="OI change")
    oichp: Optional[float] = Field(None, description="OI change percentage")
    option_type: str = Field(..., description="Option type (CE/PE)")
    prev_oi: Optional[int] = Field(None, description="Previous OI")
    strike_price: float = Field(..., description="Strike price")
    symbol: str = Field(..., description="Symbol")
    volume: Optional[int] = Field(None, description="Volume")
    
    # Underlying data (for first row)
    description: Optional[str] = Field(None, description="Description")
    ex_symbol: Optional[str] = Field(None, description="Exchange symbol")
    exchange: Optional[str] = Field(None, description="Exchange")
    fp: Optional[float] = Field(None, description="Future price")
    fpch: Optional[float] = Field(None, description="Future price change")
    fpchp: Optional[float] = Field(None, description="Future price change %")


class OptionChainResponse(BaseModel):
    """Option Chain API response."""
    s: str = Field(..., description="Status: ok/error")
    code: int = Field(..., description="Response code")
    message: str = Field("", description="Response message")
    data: Optional[Dict[str, Any]] = Field(None, description="Option chain data")

    def is_success(self) -> bool:
        return self.s == "ok" and self.code == 200
    
    def get_call_oi(self) -> int:
        """Get total call OI."""
        return self.data.get("callOi", 0) if self.data else 0
    
    def get_put_oi(self) -> int:
        """Get total put OI."""
        return self.data.get("putOi", 0) if self.data else 0
    
    def get_options_chain(self) -> List[Dict[str, Any]]:
        """Get options chain list."""
        return self.data.get("optionsChain", []) if self.data else []
    
    @property
    def dataframe(self) -> "pd.DataFrame":
        """
        Get options chain as pandas DataFrame.
        
        Example:
            ```python
            oc = await client.get_option_chain("NSE:NIFTY50-INDEX")
            df = oc.dataframe  # Automatic conversion!
            print(df[['strike_price', 'option_type', 'ltp', 'oi']])
            ```
        """
        try:
            import pandas as pd
        except ImportError:
            raise ImportError("pandas required for .dataframe property. Install: pip install pandas")
        
        options = self.get_options_chain()
        if not options:
            return pd.DataFrame()
        
        return pd.DataFrame(options)


# ==================== Generic API Response ====================

class GenericResponse(BaseModel):
    """Generic API response for simple operations."""
    s: str = Field(..., description="Status: ok/error")
    code: int = Field(..., description="Response code")
    message: str = Field("", description="Response message")

    def is_success(self) -> bool:
        return self.s == "ok"