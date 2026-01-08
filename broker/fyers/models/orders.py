"""
Pydantic models for Fyers order requests.
"""

from pydantic import BaseModel, Field, field_validator
from typing import Optional, List

# Import enums from the enums module
from broker.fyers.models.enums import OrderType, OrderSide, ProductType, OrderValidity


class SingleOrderRequest(BaseModel):
    """Request model for placing a single order."""
    
    symbol: str = Field(
        ...,
        description="Symbol (e.g., NSE:SBIN-EQ)"
    )
    qty: int = Field(
        ...,
        gt=0,
        description="Quantity (multiples of lot size for derivatives)"
    )
    type: int = Field(
        ...,
        ge=1,
        le=4,
        description="Order type: 1=Limit, 2=Market, 3=Stop, 4=StopLimit"
    )
    side: int = Field(
        ...,
        description="Side: 1=Buy, -1=Sell"
    )
    productType: str = Field(
        ...,
        description="Product type: CNC, INTRADAY, MARGIN, CO, BO, MTF"
    )
    limitPrice: float = Field(
        default=0,
        ge=0,
        description="Limit price (required for Limit and StopLimit orders)"
    )
    stopPrice: float = Field(
        default=0,
        ge=0,
        description="Stop price (required for Stop and StopLimit orders)"
    )
    disclosedQty: int = Field(
        default=0,
        ge=0,
        description="Disclosed quantity (equity only)"
    )
    validity: str = Field(
        default="DAY",
        description="Order validity: DAY, IOC"
    )
    offlineOrder: bool = Field(
        default=False,
        description="True for AMO orders"
    )
    stopLoss: float = Field(
        default=0,
        ge=0,
        description="Stop loss for CO/BO orders (in points)"
    )
    takeProfit: float = Field(
        default=0,
        ge=0,
        description="Take profit for BO orders (in rupees)"
    )
    orderTag: Optional[str] = Field(
        default=None,
        max_length=30,
        description="Order tag (alphanumeric, max 30 chars)"
    )
    isSliceOrder: bool = Field(
        default=False,
        description="Auto-slice large orders"
    )
    
    @field_validator("side")
    @classmethod
    def validate_side(cls, v: int) -> int:
        if v not in [1, -1]:
            raise ValueError("side must be 1 (Buy) or -1 (Sell)")
        return v
    
    @field_validator("productType")
    @classmethod
    def validate_product_type(cls, v: str) -> str:
        valid = ["CNC", "INTRADAY", "MARGIN", "CO", "BO", "MTF"]
        if v.upper() not in valid:
            raise ValueError(f"productType must be one of: {valid}")
        return v.upper()
    
    @field_validator("validity")
    @classmethod
    def validate_validity(cls, v: str) -> str:
        if v.upper() not in ["DAY", "IOC"]:
            raise ValueError("validity must be DAY or IOC")
        return v.upper()
    
    @field_validator("orderTag")
    @classmethod
    def validate_order_tag(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            if not v.isalnum():
                raise ValueError("orderTag must be alphanumeric")
            if len(v) < 1:
                raise ValueError("orderTag must be at least 1 character")
        return v

    class Config:
        use_enum_values = True


class ModifyOrderRequest(BaseModel):
    """Request model for modifying an order."""
    
    id: str = Field(
        ...,
        description="Order ID to modify"
    )
    qty: Optional[int] = Field(
        default=None,
        gt=0,
        description="New quantity"
    )
    type: Optional[int] = Field(
        default=None,
        ge=1,
        le=4,
        description="New order type"
    )
    limitPrice: Optional[float] = Field(
        default=None,
        ge=0,
        description="New limit price"
    )
    stopPrice: Optional[float] = Field(
        default=None,
        ge=0,
        description="New stop price"
    )

    def to_request_dict(self) -> dict:
        """Convert to dict, excluding None values."""
        return {k: v for k, v in self.model_dump().items() if v is not None}


class CancelOrderRequest(BaseModel):
    """Request model for cancelling an order."""
    
    id: str = Field(
        ...,
        description="Order ID to cancel"
    )


class MultiLegOrderLeg(BaseModel):
    """Individual leg in a multi-leg order."""
    
    symbol: str = Field(
        ...,
        description="Symbol (e.g., NSE:SBIN24JUNFUT)"
    )
    qty: int = Field(
        ...,
        gt=0,
        description="Quantity (multiples of lot size)"
    )
    side: int = Field(
        ...,
        description="Side: 1=Buy, -1=Sell"
    )
    type: int = Field(
        default=1,
        description="Order type (1=Limit for multi-leg)"
    )
    limitPrice: float = Field(
        ...,
        ge=0,
        description="Limit price"
    )
    
    @field_validator("side")
    @classmethod
    def validate_side(cls, v: int) -> int:
        if v not in [1, -1]:
            raise ValueError("side must be 1 (Buy) or -1 (Sell)")
        return v


class MultiLegOrderRequest(BaseModel):
    """Request model for multi-leg orders (2L or 3L)."""
    
    orderTag: Optional[str] = Field(
        default=None,
        description="Order tag"
    )
    productType: str = Field(
        ...,
        description="Product type: INTRADAY, MARGIN"
    )
    offlineOrder: bool = Field(
        default=False,
        description="True for AMO orders"
    )
    orderType: str = Field(
        ...,
        description="Order type: 2L or 3L"
    )
    validity: str = Field(
        default="IOC",
        description="Order validity (IOC for multi-leg)"
    )
    legs: dict = Field(
        ...,
        description="Legs: {leg1: {...}, leg2: {...}, leg3: {...}}"
    )
    
    @field_validator("productType")
    @classmethod
    def validate_product_type(cls, v: str) -> str:
        if v.upper() not in ["INTRADAY", "MARGIN"]:
            raise ValueError("productType must be INTRADAY or MARGIN for multi-leg")
        return v.upper()
    
    @field_validator("orderType")
    @classmethod
    def validate_order_type(cls, v: str) -> str:
        if v.upper() not in ["2L", "3L"]:
            raise ValueError("orderType must be 2L or 3L")
        return v.upper()


class ExitPositionRequest(BaseModel):
    """Request model for exiting position(s)."""
    
    id: Optional[str] = Field(
        default=None,
        description="Position ID to exit (None to exit all)"
    )


class ConvertPositionRequest(BaseModel):
    """Request model for converting a position."""
    
    symbol: str = Field(
        ...,
        description="Symbol"
    )
    positionSide: int = Field(
        ...,
        description="Position side: 1=Long, -1=Short"
    )
    convertQty: int = Field(
        ...,
        gt=0,
        description="Quantity to convert"
    )
    convertFrom: str = Field(
        ...,
        description="Convert from product type"
    )
    convertTo: str = Field(
        ...,
        description="Convert to product type"
    )
    
    @field_validator("positionSide")
    @classmethod
    def validate_position_side(cls, v: int) -> int:
        if v not in [1, -1]:
            raise ValueError("positionSide must be 1 (Long) or -1 (Short)")
        return v


# Helper functions for creating orders

def create_market_order(
    symbol: str,
    qty: int,
    side: int,
    product_type: str = "INTRADAY",
    order_tag: Optional[str] = None,
) -> SingleOrderRequest:
    """Create a market order."""
    return SingleOrderRequest(
        symbol=symbol,
        qty=qty,
        type=OrderType.MARKET,
        side=side,
        productType=product_type,
        limitPrice=0,
        stopPrice=0,
        orderTag=order_tag,
    )


def create_limit_order(
    symbol: str,
    qty: int,
    side: int,
    limit_price: float,
    product_type: str = "INTRADAY",
    order_tag: Optional[str] = None,
) -> SingleOrderRequest:
    """Create a limit order."""
    return SingleOrderRequest(
        symbol=symbol,
        qty=qty,
        type=OrderType.LIMIT,
        side=side,
        productType=product_type,
        limitPrice=limit_price,
        stopPrice=0,
        orderTag=order_tag,
    )


def create_stop_order(
    symbol: str,
    qty: int,
    side: int,
    stop_price: float,
    product_type: str = "INTRADAY",
    order_tag: Optional[str] = None,
) -> SingleOrderRequest:
    """Create a stop (SL-M) order."""
    return SingleOrderRequest(
        symbol=symbol,
        qty=qty,
        type=OrderType.STOP,
        side=side,
        productType=product_type,
        limitPrice=0,
        stopPrice=stop_price,
        orderTag=order_tag,
    )


def create_stop_limit_order(
    symbol: str,
    qty: int,
    side: int,
    limit_price: float,
    stop_price: float,
    product_type: str = "INTRADAY",
    order_tag: Optional[str] = None,
) -> SingleOrderRequest:
    """Create a stop-limit (SL-L) order."""
    return SingleOrderRequest(
        symbol=symbol,
        qty=qty,
        type=OrderType.STOP_LIMIT,
        side=side,
        productType=product_type,
        limitPrice=limit_price,
        stopPrice=stop_price,
        orderTag=order_tag,
    )


def create_bracket_order(
    symbol: str,
    qty: int,
    side: int,
    limit_price: float,
    stop_loss: float,
    take_profit: float,
    order_tag: Optional[str] = None,
) -> SingleOrderRequest:
    """Create a bracket order."""
    return SingleOrderRequest(
        symbol=symbol,
        qty=qty,
        type=OrderType.LIMIT,
        side=side,
        productType="BO",
        limitPrice=limit_price,
        stopPrice=0,
        stopLoss=stop_loss,
        takeProfit=take_profit,
        orderTag=order_tag,
    )


def create_cover_order(
    symbol: str,
    qty: int,
    side: int,
    limit_price: float,
    stop_loss: float,
    order_tag: Optional[str] = None,
) -> SingleOrderRequest:
    """Create a cover order."""
    return SingleOrderRequest(
        symbol=symbol,
        qty=qty,
        type=OrderType.LIMIT,
        side=side,
        productType="CO",
        limitPrice=limit_price,
        stopPrice=0,
        stopLoss=stop_loss,
        orderTag=order_tag,
    )