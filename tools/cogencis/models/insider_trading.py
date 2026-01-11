"""Insider trading models for Cogencis API."""

from datetime import datetime
from typing import Any
from pydantic import BaseModel, Field, field_validator

from .common import PagingInfo, ColumnDefinition


class InsiderTrade(BaseModel):
    """Individual insider trading transaction data.
    
    Field mappings from API:
    - f_28: date (format: "DD MMM YY")
    - f_4: acquirer_name (acquirer/disposer name)
    - f_5: category (Promoter Group, Immediate relative, etc.)
    - f_7: shares_before (number of shares held before transaction)
    - f_8: percentage_before (% shareholding before)
    - f_10: quantity (number of shares in transaction)
    - f_12: transaction_type (Buy/Sell/Pledge Invoke/etc.)
    - f_14: shares_after (number of shares held after)
    - f_15: percentage_after (% shareholding after)
    - f_19: acquisition_mode (Market Sale, Gift, Off Market, etc.)
    - f_25008: path
    """

    date: str = Field(alias="f_28")
    acquirer_name: str = Field(alias="f_4")
    category: str = Field(alias="f_5")
    shares_before: float | None = Field(default=None, alias="f_7")
    percentage_before: float = Field(default=0.0, alias="f_8")
    quantity: int = Field(alias="f_10")
    transaction_type: str = Field(alias="f_12")
    shares_after: float | None = Field(default=None, alias="f_14")
    percentage_after: float = Field(default=0.0, alias="f_15")
    acquisition_mode: str = Field(alias="f_19")
    path: str = Field(alias="f_25008")

    @field_validator("quantity", mode="before")
    @classmethod
    def parse_quantity(cls, v: Any) -> int:
        """Parse quantity which may come as string or int."""
        if v is None:
            return 0
        if isinstance(v, str):
            return int(v.replace(",", ""))
        return int(v)

    @field_validator("shares_before", "shares_after", mode="before")
    @classmethod
    def parse_shares(cls, v: Any) -> float | None:
        """Parse shares which may come as string or be null."""
        if v is None:
            return None
        if isinstance(v, str):
            return float(v.replace(",", ""))
        return float(v)

    @field_validator("percentage_before", "percentage_after", mode="before")
    @classmethod
    def parse_percentage(cls, v: Any) -> float:
        """Parse percentage which may come as string."""
        if v is None:
            return 0.0
        if isinstance(v, str):
            return float(v.replace(",", ""))
        return float(v)

    @property
    def is_buy(self) -> bool:
        """Check if this is a buy transaction."""
        return self.transaction_type.lower() == "buy"

    @property
    def is_sell(self) -> bool:
        """Check if this is a sell transaction."""
        return self.transaction_type.lower() == "sell"

    @property
    def is_pledge(self) -> bool:
        """Check if this is a pledge-related transaction."""
        return "pledge" in self.transaction_type.lower()

    @property
    def is_promoter(self) -> bool:
        """Check if this is from promoter/promoter group."""
        return "promoter" in self.category.lower()

    @property
    def date_parsed(self) -> datetime | None:
        """Parse date string to datetime object."""
        try:
            # Format: "14 Dec 23" or "22 Aug 23"
            return datetime.strptime(self.date, "%d %b %y")
        except (ValueError, TypeError):
            return None

    @property
    def net_change(self) -> float:
        """Calculate net change in shareholding percentage."""
        return self.percentage_after - self.percentage_before

    class Config:
        populate_by_name = True


class InsiderTradingResponseData(BaseModel):
    """Paginated insider trading response data from API."""

    paging_info: PagingInfo = Field(alias="pagingInfo")
    columns: list[ColumnDefinition]
    data: list[InsiderTrade]

    class Config:
        populate_by_name = True


class InsiderTradingResponse(BaseModel):
    """Response model for insider trading API."""

    status: bool
    message: str
    response: InsiderTradingResponseData | None = None

    @property
    def is_success(self) -> bool:
        """Check if the response indicates success."""
        return self.status is True

    @property
    def trades(self) -> list[InsiderTrade]:
        """Get list of insider trades."""
        if self.response:
            return self.response.data
        return []

    @property
    def total_results(self) -> int:
        """Get total number of trades available."""
        if self.response:
            return self.response.paging_info.total_records
        return 0

    @property
    def buy_trades(self) -> list[InsiderTrade]:
        """Get only buy transactions."""
        return [t for t in self.trades if t.is_buy]

    @property
    def sell_trades(self) -> list[InsiderTrade]:
        """Get only sell transactions."""
        return [t for t in self.trades if t.is_sell]

    @property
    def promoter_trades(self) -> list[InsiderTrade]:
        """Get only promoter transactions."""
        return [t for t in self.trades if t.is_promoter]

    class Config:
        populate_by_name = True