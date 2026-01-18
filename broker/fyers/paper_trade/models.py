"""
Pydantic models for paper trading state.

These models define the structure for simulated orders, trades, positions,
holdings, and funds that are persisted to JSON.
"""

from pydantic import BaseModel, Field
from typing import Dict, List, Optional
from enum import IntEnum


class PaperOrderStatus(IntEnum):
    """Paper order statuses matching Fyers OrderStatus."""

    CANCELLED = 1
    TRADED = 2
    TRANSIT = 4
    REJECTED = 5
    PENDING = 6
    EXPIRED = 7


class PaperOrder(BaseModel):
    """Simulated order in paper trading."""

    id: str = Field(..., description="Order ID (format: PT-{timestamp}-{counter})")
    exchOrdId: str = Field(default="", description="Exchange order ID (empty for paper)")
    symbol: str = Field(..., description="Symbol (e.g., NSE:SBIN-EQ)")
    qty: int = Field(..., description="Order quantity")
    remainingQuantity: int = Field(..., description="Remaining unfilled quantity")
    filledQty: int = Field(default=0, description="Filled quantity")
    status: int = Field(default=PaperOrderStatus.PENDING, description="Order status")
    segment: int = Field(default=10, description="Segment (10=CM, 11=FO, 12=CD, 20=COM)")
    limitPrice: float = Field(default=0.0, description="Limit price for limit orders")
    stopPrice: float = Field(default=0.0, description="Stop/trigger price")
    productType: str = Field(..., description="Product type (CNC, INTRADAY, MARGIN, etc.)")
    type: int = Field(..., description="Order type (1=Limit, 2=Market, 3=Stop, 4=StopLimit)")
    side: int = Field(..., description="Order side (1=Buy, -1=Sell)")
    orderValidity: str = Field(default="DAY", description="Order validity (DAY, IOC)")
    orderDateTime: str = Field(..., description="Order placement time")
    tradedPrice: float = Field(default=0.0, description="Average traded price")
    exchange: int = Field(default=10, description="Exchange (10=NSE, 11=MCX, 12=BSE)")
    orderTag: Optional[str] = Field(default=None, description="Order tag (max 30 chars)")
    message: str = Field(default="", description="Status message or error")
    created_at: str = Field(..., description="Creation timestamp")
    updated_at: str = Field(..., description="Last update timestamp")


class PaperTrade(BaseModel):
    """Executed trade record."""

    tradeNumber: str = Field(..., description="Trade ID (format: PTT-{timestamp}-{counter})")
    orderNumber: str = Field(..., description="Associated order ID")
    symbol: str = Field(..., description="Symbol")
    tradePrice: float = Field(..., description="Execution price")
    tradeValue: float = Field(..., description="Trade value (price * qty)")
    tradedQty: int = Field(..., description="Traded quantity")
    side: int = Field(..., description="Trade side (1=Buy, -1=Sell)")
    productType: str = Field(..., description="Product type")
    orderDateTime: str = Field(..., description="Trade execution time")
    segment: int = Field(default=10, description="Segment")
    exchange: int = Field(default=10, description="Exchange")


class PaperPosition(BaseModel):
    """Aggregated position from orders."""

    id: str = Field(..., description="Position ID (format: {symbol}-{productType})")
    symbol: str = Field(..., description="Symbol")
    productType: str = Field(..., description="Product type")
    buyAvg: float = Field(default=0.0, description="Average buy price")
    buyQty: int = Field(default=0, description="Total buy quantity")
    sellAvg: float = Field(default=0.0, description="Average sell price")
    sellQty: int = Field(default=0, description="Total sell quantity")
    netAvg: float = Field(default=0.0, description="Net average price")
    netQty: int = Field(default=0, description="Net quantity (buyQty - sellQty)")
    side: int = Field(default=0, description="Position side (1=Long, -1=Short, 0=Closed)")
    qty: int = Field(default=0, description="Absolute net quantity")
    realized_profit: float = Field(default=0.0, description="Realized P&L")
    unrealized_profit: float = Field(default=0.0, description="Unrealized P&L")
    pl: float = Field(default=0.0, description="Total P&L (realized + unrealized)")
    segment: int = Field(default=10, description="Segment")
    exchange: int = Field(default=10, description="Exchange")
    ltp: float = Field(default=0.0, description="Last traded price")
    dayBuyQty: int = Field(default=0, description="Day buy quantity")
    daySellQty: int = Field(default=0, description="Day sell quantity")
    cfBuyQty: int = Field(default=0, description="Carry forward buy quantity")
    cfSellQty: int = Field(default=0, description="Carry forward sell quantity")


class PaperHolding(BaseModel):
    """CNC holding (delivery positions)."""

    id: int = Field(..., description="Unique holding ID")
    symbol: str = Field(..., description="Symbol")
    holdingType: str = Field(default="HLD", description="Holding type (T1 or HLD)")
    quantity: int = Field(..., description="Total quantity")
    remainingQuantity: int = Field(..., description="Remaining quantity after sales")
    costPrice: float = Field(..., description="Average cost price")
    marketVal: float = Field(default=0.0, description="Current market value")
    ltp: float = Field(default=0.0, description="Last traded price")
    pl: float = Field(default=0.0, description="Profit/loss")
    exchange: int = Field(default=10, description="Exchange")
    segment: int = Field(default=10, description="Segment")
    isin: Optional[str] = Field(default=None, description="ISIN code")


class PaperFunds(BaseModel):
    """Fund/margin tracking."""

    total_balance: float = Field(..., description="Total balance (initial + realized P&L)")
    available_balance: float = Field(..., description="Available balance for trading")
    utilized_margin: float = Field(default=0.0, description="Margin used by open positions")
    realized_pnl: float = Field(default=0.0, description="Realized profit/loss")
    unrealized_pnl: float = Field(default=0.0, description="Unrealized profit/loss")


class PaperTradeState(BaseModel):
    """Complete paper trading state - persisted to JSON."""

    version: str = Field(default="1.0", description="State schema version")
    created_at: str = Field(..., description="State creation timestamp")
    updated_at: str = Field(..., description="Last update timestamp")

    # Core state
    funds: PaperFunds = Field(..., description="Funds and margin info")
    orders: Dict[str, PaperOrder] = Field(default_factory=dict, description="Order ID -> Order")
    trades: List[PaperTrade] = Field(default_factory=list, description="Trade history")
    positions: Dict[str, PaperPosition] = Field(
        default_factory=dict, description="Position ID -> Position"
    )
    holdings: Dict[str, PaperHolding] = Field(
        default_factory=dict, description="Symbol -> Holding"
    )

    # Counters for ID generation
    order_counter: int = Field(default=0, description="Counter for unique order IDs")
    trade_counter: int = Field(default=0, description="Counter for unique trade IDs")
    holding_counter: int = Field(default=0, description="Counter for unique holding IDs")

    # Daily reset tracking
    last_trading_date: Optional[str] = Field(
        default=None, description="Last trading date for intraday position reset"
    )
