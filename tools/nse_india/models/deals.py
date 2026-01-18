"""Data models for NSE India bulk deals, block deals, and short selling."""

from datetime import date, datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


class DealType(StrEnum):
    """Type of deal."""

    BUY = "BUY"
    SELL = "SELL"


def _parse_date(v: Any) -> date | None:
    """Parse date from NSE format."""
    if v is None:
        return None
    if isinstance(v, date):
        return v
    if isinstance(v, datetime):
        return v.date()
    if isinstance(v, str):
        v = v.strip()
        if not v:
            return None
        # Try DD-Mon-YYYY format (e.g., "16-Jan-2026")
        try:
            return datetime.strptime(v, "%d-%b-%Y").date()
        except ValueError:
            pass
        # Try other formats
        for fmt in ["%d-%B-%Y", "%Y-%m-%d", "%d-%m-%Y"]:
            try:
                return datetime.strptime(v, fmt).date()
            except ValueError:
                continue
    return None


def _parse_int(v: Any) -> int | None:
    """Parse integer value, handling strings with commas."""
    if v is None:
        return None
    if isinstance(v, int):
        return v
    if isinstance(v, float):
        return int(v)
    if isinstance(v, str):
        v = v.strip()
        if not v or v == "-":
            return None
        try:
            return int(v.replace(",", ""))
        except ValueError:
            return None
    return None


def _parse_float(v: Any) -> float | None:
    """Parse float value, handling strings with commas."""
    if v is None:
        return None
    if isinstance(v, (int, float)):
        return float(v)
    if isinstance(v, str):
        v = v.strip()
        if not v or v == "-":
            return None
        try:
            return float(v.replace(",", ""))
        except ValueError:
            return None
    return None


class BulkDeal(BaseModel):
    """Bulk deal transaction from NSE.

    Bulk deals are transactions where the total quantity traded is more than
    0.5% of the number of equity shares of the company listed on the exchange.
    """

    model_config = ConfigDict(
        populate_by_name=True,
        str_strip_whitespace=True,
    )

    deal_date: date = Field(alias="date", description="Date of the deal")
    symbol: str = Field(description="Stock symbol")
    company_name: str = Field(alias="name", description="Company name")
    client_name: str = Field(alias="clientName", description="Name of the buyer/seller")
    deal_type: str = Field(alias="buySell", description="BUY or SELL")
    quantity: int = Field(alias="qty", description="Number of shares traded")
    weighted_avg_price: float = Field(alias="watp", description="Weighted average trade price")
    remarks: str | None = Field(default=None, description="Additional remarks")

    @field_validator("deal_date", mode="before")
    @classmethod
    def parse_deal_date(cls, v: Any) -> date | None:
        return _parse_date(v)

    @field_validator("quantity", mode="before")
    @classmethod
    def parse_quantity(cls, v: Any) -> int | None:
        return _parse_int(v)

    @field_validator("weighted_avg_price", mode="before")
    @classmethod
    def parse_price(cls, v: Any) -> float | None:
        return _parse_float(v)

    @field_validator("remarks", mode="before")
    @classmethod
    def clean_remarks(cls, v: Any) -> str | None:
        if v is None or v == "-" or v == "":
            return None
        return str(v).strip()

    @property
    def is_buy(self) -> bool:
        """Check if this is a buy deal."""
        return self.deal_type.upper() == "BUY"

    @property
    def is_sell(self) -> bool:
        """Check if this is a sell deal."""
        return self.deal_type.upper() == "SELL"

    @property
    def trade_value(self) -> float:
        """Calculate total trade value."""
        return self.quantity * self.weighted_avg_price

    @property
    def trade_value_cr(self) -> float:
        """Calculate total trade value in crores."""
        return self.trade_value / 10_000_000


class BlockDeal(BaseModel):
    """Block deal transaction from NSE.

    Block deals are single transactions with a minimum quantity of 5 lakh shares
    or minimum value of Rs. 10 crore, executed through a separate trading window.
    """

    model_config = ConfigDict(
        populate_by_name=True,
        str_strip_whitespace=True,
    )

    deal_date: date = Field(alias="date", description="Date of the deal")
    symbol: str = Field(description="Stock symbol")
    company_name: str = Field(alias="name", description="Company name")
    client_name: str = Field(alias="clientName", description="Name of the buyer/seller")
    deal_type: str = Field(alias="buySell", description="BUY or SELL")
    quantity: int = Field(alias="qty", description="Number of shares traded")
    weighted_avg_price: float = Field(alias="watp", description="Weighted average trade price")
    remarks: str | None = Field(default=None, description="Additional remarks")

    @field_validator("deal_date", mode="before")
    @classmethod
    def parse_deal_date(cls, v: Any) -> date | None:
        return _parse_date(v)

    @field_validator("quantity", mode="before")
    @classmethod
    def parse_quantity(cls, v: Any) -> int | None:
        return _parse_int(v)

    @field_validator("weighted_avg_price", mode="before")
    @classmethod
    def parse_price(cls, v: Any) -> float | None:
        return _parse_float(v)

    @field_validator("remarks", mode="before")
    @classmethod
    def clean_remarks(cls, v: Any) -> str | None:
        if v is None or v == "-" or v == "":
            return None
        return str(v).strip()

    @property
    def is_buy(self) -> bool:
        """Check if this is a buy deal."""
        return self.deal_type.upper() == "BUY"

    @property
    def is_sell(self) -> bool:
        """Check if this is a sell deal."""
        return self.deal_type.upper() == "SELL"

    @property
    def trade_value(self) -> float:
        """Calculate total trade value."""
        return self.quantity * self.weighted_avg_price

    @property
    def trade_value_cr(self) -> float:
        """Calculate total trade value in crores."""
        return self.trade_value / 10_000_000


class ShortSelling(BaseModel):
    """Short selling data from NSE.

    Short selling occurs when an investor borrows a security and sells it
    on the open market, planning to buy it back later for less money.
    """

    model_config = ConfigDict(
        populate_by_name=True,
        str_strip_whitespace=True,
    )

    deal_date: date = Field(alias="date", description="Date of short selling")
    symbol: str = Field(description="Stock symbol")
    company_name: str = Field(alias="name", description="Company name")
    quantity: int = Field(alias="qty", description="Number of shares short sold")

    @field_validator("deal_date", mode="before")
    @classmethod
    def parse_deal_date(cls, v: Any) -> date | None:
        return _parse_date(v)

    @field_validator("quantity", mode="before")
    @classmethod
    def parse_quantity(cls, v: Any) -> int | None:
        return _parse_int(v)


class LargeDealsSnapshot(BaseModel):
    """Snapshot of all large deals (bulk, block, short selling) from NSE."""

    model_config = ConfigDict(str_strip_whitespace=True)

    as_on_date: date | None = Field(default=None, description="Data as of date")
    bulk_deals: list[BulkDeal] = Field(default_factory=list, description="List of bulk deals")
    block_deals: list[BlockDeal] = Field(default_factory=list, description="List of block deals")
    short_selling: list[ShortSelling] = Field(
        default_factory=list, description="List of short selling data"
    )
    bulk_deals_count: int = Field(default=0, description="Total bulk deals count")
    block_deals_count: int = Field(default=0, description="Total block deals count")
    short_deals_count: int = Field(default=0, description="Total short selling count")

    @field_validator("as_on_date", mode="before")
    @classmethod
    def parse_as_on_date(cls, v: Any) -> date | None:
        return _parse_date(v)

    @property
    def bulk_buys(self) -> list[BulkDeal]:
        """Get all bulk buy deals."""
        return [d for d in self.bulk_deals if d.is_buy]

    @property
    def bulk_sells(self) -> list[BulkDeal]:
        """Get all bulk sell deals."""
        return [d for d in self.bulk_deals if d.is_sell]

    @property
    def block_buys(self) -> list[BlockDeal]:
        """Get all block buy deals."""
        return [d for d in self.block_deals if d.is_buy]

    @property
    def block_sells(self) -> list[BlockDeal]:
        """Get all block sell deals."""
        return [d for d in self.block_deals if d.is_sell]

    def get_bulk_deals_by_symbol(self, symbol: str) -> list[BulkDeal]:
        """Get bulk deals for a specific symbol."""
        symbol_upper = symbol.upper()
        return [d for d in self.bulk_deals if d.symbol.upper() == symbol_upper]

    def get_block_deals_by_symbol(self, symbol: str) -> list[BlockDeal]:
        """Get block deals for a specific symbol."""
        symbol_upper = symbol.upper()
        return [d for d in self.block_deals if d.symbol.upper() == symbol_upper]

    def get_short_selling_by_symbol(self, symbol: str) -> list[ShortSelling]:
        """Get short selling data for a specific symbol."""
        symbol_upper = symbol.upper()
        return [d for d in self.short_selling if d.symbol.upper() == symbol_upper]

    def get_bulk_deals_by_client(self, client_name: str) -> list[BulkDeal]:
        """Get bulk deals by client name (partial match)."""
        client_lower = client_name.lower()
        return [d for d in self.bulk_deals if client_lower in d.client_name.lower()]

    def get_top_bulk_deals_by_value(self, limit: int = 10) -> list[BulkDeal]:
        """Get top bulk deals by trade value."""
        return sorted(self.bulk_deals, key=lambda d: d.trade_value, reverse=True)[:limit]

    def get_top_block_deals_by_value(self, limit: int = 10) -> list[BlockDeal]:
        """Get top block deals by trade value."""
        return sorted(self.block_deals, key=lambda d: d.trade_value, reverse=True)[:limit]

    def get_top_shorted_stocks(self, limit: int = 10) -> list[ShortSelling]:
        """Get top shorted stocks by quantity."""
        return sorted(self.short_selling, key=lambda d: d.quantity, reverse=True)[:limit]

    @property
    def total_bulk_buy_value(self) -> float:
        """Total value of all bulk buy deals."""
        return sum(d.trade_value for d in self.bulk_buys)

    @property
    def total_bulk_sell_value(self) -> float:
        """Total value of all bulk sell deals."""
        return sum(d.trade_value for d in self.bulk_sells)

    @property
    def total_block_buy_value(self) -> float:
        """Total value of all block buy deals."""
        return sum(d.trade_value for d in self.block_buys)

    @property
    def total_block_sell_value(self) -> float:
        """Total value of all block sell deals."""
        return sum(d.trade_value for d in self.block_sells)

    def get_unique_symbols(self) -> set[str]:
        """Get all unique symbols with deals."""
        symbols = set()
        for d in self.bulk_deals:
            symbols.add(d.symbol)
        for d in self.block_deals:
            symbols.add(d.symbol)
        for d in self.short_selling:
            symbols.add(d.symbol)
        return symbols
