"""Block deal models for Cogencis API."""

from datetime import datetime
from enum import Enum
from typing import Any
from pydantic import BaseModel, Field, field_validator

from .common import PagingInfo, ColumnDefinition


class BlockDealType(int, Enum):
    """Block deal types."""

    BLOCK_DEAL = 1  # Regular block deals
    BULK_DEAL = 2   # Bulk deals


class TransactionType(str, Enum):
    """Transaction type for block deals."""

    BUY = "BUY"
    SELL = "SELL"


class BlockDeal(BaseModel):
    """Individual block/bulk deal data.
    
    Field mappings from API:
    - f_32: client_name
    - f_33: transaction_type (BUY/SELL)
    - f_34: quantity
    - f_36: weighted_avg_price
    - f_35: date (format: "DD MMM YY")
    - f_25008: path
    """

    client_name: str = Field(alias="f_32")
    transaction_type: str = Field(alias="f_33")
    quantity: int = Field(alias="f_34")
    weighted_avg_price: float = Field(alias="f_36")
    date: str = Field(alias="f_35")
    path: str = Field(alias="f_25008")

    @field_validator("quantity", mode="before")
    @classmethod
    def parse_quantity(cls, v: Any) -> int:
        """Parse quantity which may come as string or int."""
        if isinstance(v, str):
            return int(v.replace(",", ""))
        return int(v) if v is not None else 0

    @field_validator("weighted_avg_price", mode="before")
    @classmethod
    def parse_price(cls, v: Any) -> float:
        """Parse price which may come as string."""
        if isinstance(v, str):
            return float(v.replace(",", ""))
        return float(v) if v is not None else 0.0

    @property
    def is_buy(self) -> bool:
        """Check if this is a buy transaction."""
        return self.transaction_type.upper() == "BUY"

    @property
    def is_sell(self) -> bool:
        """Check if this is a sell transaction."""
        return self.transaction_type.upper() == "SELL"

    @property
    def deal_value(self) -> float:
        """Calculate total deal value (quantity * price)."""
        return self.quantity * self.weighted_avg_price

    @property
    def date_parsed(self) -> datetime | None:
        """Parse date string to datetime object."""
        try:
            # Format: "28 May 13" or "19 Nov 25"
            return datetime.strptime(self.date, "%d %b %y")
        except (ValueError, TypeError):
            return None

    class Config:
        populate_by_name = True


class BlockDealResponseData(BaseModel):
    """Paginated block deal response data from API."""

    paging_info: PagingInfo = Field(alias="pagingInfo")
    columns: list[ColumnDefinition]
    data: list[BlockDeal]

    class Config:
        populate_by_name = True


class BlockDealResponse(BaseModel):
    """Response model for block deals API."""

    status: bool
    message: str
    response: BlockDealResponseData | None = None

    @property
    def is_success(self) -> bool:
        """Check if the response indicates success."""
        return self.status is True

    @property
    def deals(self) -> list[BlockDeal]:
        """Get list of block deals."""
        if self.response:
            return self.response.data
        return []

    @property
    def total_results(self) -> int:
        """Get total number of deals available."""
        if self.response:
            return self.response.paging_info.total_records
        return 0

    @property
    def buy_deals(self) -> list[BlockDeal]:
        """Get only buy transactions."""
        return [d for d in self.deals if d.is_buy]

    @property
    def sell_deals(self) -> list[BlockDeal]:
        """Get only sell transactions."""
        return [d for d in self.deals if d.is_sell]

    class Config:
        populate_by_name = True