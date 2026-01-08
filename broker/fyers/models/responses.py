"""
Pydantic models for Fyers API responses.
"""

from pydantic import BaseModel, Field
from typing import Optional, List

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
    """User profile data."""
    name: str = Field(..., description="Name of the client")
    display_name: Optional[str] = Field(None, description="Display name")
    fy_id: str = Field(..., description="Client ID of the fyers user")
    image: Optional[str] = Field(None, description="URL to profile picture")
    email_id: str = Field(..., description="Email address")
    pan: Optional[str] = Field(None, alias="PAN", description="PAN of the client")
    pin_change_date: Optional[str] = Field(None, description="Last PIN change date")
    pwd_change_date: Optional[str] = Field(None, description="Last password change date")
    mobile_number: Optional[str] = Field(None, description="Registered mobile number")
    totp: Optional[bool] = Field(None, description="TOTP status")
    pwd_to_expire: Optional[int] = Field(None, description="Days until password expires")
    ddpi_enabled: Optional[bool] = Field(None, description="DDPI status")
    mtf_enabled: Optional[bool] = Field(None, description="MTF status")


class ProfileResponse(BaseModel):
    """Profile API response."""
    s: str = Field(..., description="Status: ok/error")
    code: int = Field(..., description="Response code")
    message: Optional[str] = Field("", description="Response message")
    data: Optional[ProfileData] = Field(None, description="Profile data")

    def is_success(self) -> bool:
        return self.s == "ok" and self.code == 200


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


# ==================== Generic API Response ====================

class GenericResponse(BaseModel):
    """Generic API response for simple operations."""
    s: str = Field(..., description="Status: ok/error")
    code: int = Field(..., description="Response code")
    message: str = Field("", description="Response message")

    def is_success(self) -> bool:
        return self.s == "ok"