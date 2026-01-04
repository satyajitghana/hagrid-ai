from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime

class MarketRegime(str, Enum):
    CALM = "CALM"
    NORMAL = "NORMAL"
    ELEVATED = "ELEVATED"
    CRISIS = "CRISIS"

class SignalType(str, Enum):
    BUY = "BUY"
    SELL = "SELL"
    NEUTRAL = "NEUTRAL"
    NO_TRADE = "NO_TRADE"

class AgentSignal(BaseModel):
    department: str
    symbol: str
    signal: SignalType
    score: float = Field(ge=-3.0, le=3.0)
    confidence: float = Field(ge=0.0, le=1.0)
    reasoning: str
    metadata: Dict[str, Any] = {}
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class MarketData(BaseModel):
    symbol: str
    price: float
    timestamp: datetime
    volume: Optional[float] = None
    # Add OHLC if needed

class TradeCandidate(BaseModel):
    symbol: str
    direction: str  # LONG or SHORT
    entry_price_range: tuple[float, float]
    stop_loss: float
    target_price: float
    confidence_score: float
    rationale: str
    regime: MarketRegime

class OrderStatus(str, Enum):
    PENDING = "PENDING"
    FILLED = "FILLED"
    REJECTED = "REJECTED"
    CANCELLED = "CANCELLED"

class Order(BaseModel):
    order_id: Optional[str] = None
    symbol: str
    quantity: int
    side: str  # BUY or SELL
    order_type: str = "MARKET"
    price: Optional[float] = None
    status: OrderStatus = OrderStatus.PENDING
    timestamp: datetime = Field(default_factory=datetime.utcnow)