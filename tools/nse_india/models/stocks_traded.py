"""Data models for NSE India stocks traded (live analysis)."""

from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


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


class StockTraded(BaseModel):
    """Individual stock trading data from NSE live analysis.

    Contains real-time trading metrics including price, volume,
    and market capitalization data.
    """

    model_config = ConfigDict(
        populate_by_name=True,
        str_strip_whitespace=True,
    )

    identifier: str = Field(description="Unique identifier (e.g., 'HDFCBANKEQN')")
    symbol: str = Field(description="Stock symbol")
    series: str = Field(description="Trading series (e.g., 'EQ')")
    market_type: str = Field(alias="marketType", description="Market type (N=Normal)")

    # Price data
    previous_close: float = Field(alias="previousClose", description="Previous closing price")
    last_price: float = Field(alias="lastPrice", description="Last traded price")
    change: float = Field(description="Absolute price change")
    pchange: float = Field(description="Percentage price change")
    base_price: float = Field(alias="basePrice", default=0, description="Base price")

    # Volume and value
    total_traded_volume: float = Field(
        alias="totalTradedVolume",
        description="Total traded volume (in lakhs)",
    )
    total_traded_value: float = Field(
        alias="totalTradedValue",
        description="Total traded value (in crores)",
    )

    # Market cap
    issued_cap: int = Field(alias="issuedCap", description="Issued capital (number of shares)")
    total_market_cap: float = Field(
        alias="totalMarketCap",
        description="Total market capitalization (in crores)",
    )

    @field_validator("previous_close", "last_price", "change", "pchange", "base_price",
                     "total_traded_volume", "total_traded_value", "total_market_cap",
                     mode="before")
    @classmethod
    def parse_float_field(cls, v: Any) -> float | None:
        return _parse_float(v)

    @field_validator("issued_cap", mode="before")
    @classmethod
    def parse_issued_cap(cls, v: Any) -> int | None:
        if v is None:
            return 0
        if isinstance(v, int):
            return v
        if isinstance(v, float):
            return int(v)
        if isinstance(v, str):
            try:
                return int(v.replace(",", ""))
            except ValueError:
                return 0
        return 0

    @property
    def is_gainer(self) -> bool:
        """Check if stock is gaining."""
        return self.pchange > 0

    @property
    def is_loser(self) -> bool:
        """Check if stock is losing."""
        return self.pchange < 0

    @property
    def is_unchanged(self) -> bool:
        """Check if stock is unchanged."""
        return self.pchange == 0

    @property
    def volume_lakhs(self) -> float:
        """Get volume in lakhs."""
        return self.total_traded_volume

    @property
    def value_crores(self) -> float:
        """Get traded value in crores."""
        return self.total_traded_value

    @property
    def market_cap_crores(self) -> float:
        """Get market cap in crores."""
        return self.total_market_cap


class StocksTradedCount(BaseModel):
    """Stock trading count statistics (advances, declines, unchanged)."""

    model_config = ConfigDict(
        populate_by_name=True,
        str_strip_whitespace=True,
    )

    advances: int = Field(alias="Advances", description="Number of advancing stocks")
    unchanged: int = Field(alias="Unchange", description="Number of unchanged stocks")
    declines: int = Field(alias="Declines", description="Number of declining stocks")
    total: int = Field(alias="Total", description="Total number of stocks traded")

    @property
    def advance_decline_ratio(self) -> float | None:
        """Calculate advance/decline ratio."""
        if self.declines == 0:
            return None
        return self.advances / self.declines

    @property
    def breadth_percentage(self) -> float:
        """Calculate breadth as percentage of advances."""
        if self.total == 0:
            return 0
        return (self.advances / self.total) * 100


class StocksTradedResponse(BaseModel):
    """Response from NSE stocks traded API.

    Contains market breadth statistics and list of all traded stocks.
    """

    model_config = ConfigDict(str_strip_whitespace=True)

    count: StocksTradedCount = Field(description="Market breadth counts")
    data: list[StockTraded] = Field(default_factory=list, description="List of traded stocks")

    @property
    def advances(self) -> list[StockTraded]:
        """Get all advancing stocks."""
        return [s for s in self.data if s.is_gainer]

    @property
    def declines(self) -> list[StockTraded]:
        """Get all declining stocks."""
        return [s for s in self.data if s.is_loser]

    @property
    def unchanged(self) -> list[StockTraded]:
        """Get all unchanged stocks."""
        return [s for s in self.data if s.is_unchanged]

    def get_top_gainers(self, limit: int = 20) -> list[StockTraded]:
        """Get top gaining stocks by percentage change."""
        return sorted(self.data, key=lambda s: s.pchange, reverse=True)[:limit]

    def get_top_losers(self, limit: int = 20) -> list[StockTraded]:
        """Get top losing stocks by percentage change."""
        return sorted(self.data, key=lambda s: s.pchange)[:limit]

    def get_most_traded_by_value(self, limit: int = 20) -> list[StockTraded]:
        """Get most traded stocks by value."""
        return sorted(self.data, key=lambda s: s.total_traded_value, reverse=True)[:limit]

    def get_most_traded_by_volume(self, limit: int = 20) -> list[StockTraded]:
        """Get most traded stocks by volume."""
        return sorted(self.data, key=lambda s: s.total_traded_volume, reverse=True)[:limit]

    def get_by_symbol(self, symbol: str) -> StockTraded | None:
        """Get stock data by symbol."""
        symbol_upper = symbol.upper()
        for stock in self.data:
            if stock.symbol.upper() == symbol_upper:
                return stock
        return None

    def get_large_caps(self, min_mcap_cr: float = 50000) -> list[StockTraded]:
        """Get large cap stocks (market cap > threshold in crores)."""
        return [s for s in self.data if s.total_market_cap >= min_mcap_cr]

    def get_mid_caps(
        self, min_mcap_cr: float = 10000, max_mcap_cr: float = 50000
    ) -> list[StockTraded]:
        """Get mid cap stocks (market cap between thresholds in crores)."""
        return [
            s for s in self.data
            if min_mcap_cr <= s.total_market_cap < max_mcap_cr
        ]

    def get_small_caps(self, max_mcap_cr: float = 10000) -> list[StockTraded]:
        """Get small cap stocks (market cap < threshold in crores)."""
        return [s for s in self.data if s.total_market_cap < max_mcap_cr]

    @property
    def total_traded_value_cr(self) -> float:
        """Get total traded value across all stocks in crores."""
        return sum(s.total_traded_value for s in self.data)

    @property
    def total_market_cap_cr(self) -> float:
        """Get total market cap of all traded stocks in crores."""
        return sum(s.total_market_cap for s in self.data)
