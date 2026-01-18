"""Data models for NSE India advances/declines data."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, computed_field


class MarketMover(BaseModel):
    """Individual stock data in advances/declines list."""

    model_config = ConfigDict(
        populate_by_name=True,
        str_strip_whitespace=True,
    )

    identifier: str = Field(default="", description="Unique identifier")
    symbol: str = Field(default="", description="Stock symbol")
    series: str = Field(default="EQ", description="Series (EQ, BE, etc.)")
    market_type: str = Field(alias="marketType", default="N", description="Market type")

    # Price data
    pchange: float = Field(default=0, description="Percentage change")
    change: float = Field(default=0, description="Absolute price change")
    base_price: float = Field(alias="basePrice", default=0, description="Base price")
    previous_close: float = Field(alias="previousClose", default=0, description="Previous close price")
    last_price: float = Field(alias="lastPrice", default=0, description="Last traded price")

    # Volume and market cap
    total_traded_volume: float = Field(
        alias="totalTradedVolume", default=0,
        description="Total traded volume in lakhs"
    )
    total_traded_value: float = Field(
        alias="totalTradedValue", default=0,
        description="Total traded value in crores"
    )
    issued_cap: int = Field(alias="issuedCap", default=0, description="Issued capital")
    total_market_cap: float = Field(
        alias="totalMarketCap", default=0,
        description="Total market cap in crores"
    )

    @property
    def is_advancing(self) -> bool:
        """Check if the stock is advancing (positive change)."""
        return self.pchange > 0

    @property
    def is_declining(self) -> bool:
        """Check if the stock is declining (negative change)."""
        return self.pchange < 0

    @property
    def is_unchanged(self) -> bool:
        """Check if the stock is unchanged."""
        return self.pchange == 0


class MarketBreadthCount(BaseModel):
    """Count summary for market breadth."""

    model_config = ConfigDict(
        populate_by_name=True,
        str_strip_whitespace=True,
    )

    advances: int = Field(alias="Advances", default=0, description="Number of advancing stocks")
    unchanged: int = Field(alias="Unchange", default=0, description="Number of unchanged stocks")
    declines: int = Field(alias="Declines", default=0, description="Number of declining stocks")
    total: int = Field(alias="Total", default=0, description="Total number of stocks")

    @computed_field
    @property
    def advance_decline_ratio(self) -> float:
        """Calculate advance/decline ratio."""
        if self.declines > 0:
            return self.advances / self.declines
        return float('inf') if self.advances > 0 else 0

    @computed_field
    @property
    def advance_percentage(self) -> float:
        """Percentage of stocks advancing."""
        if self.total > 0:
            return (self.advances / self.total) * 100
        return 0

    @computed_field
    @property
    def decline_percentage(self) -> float:
        """Percentage of stocks declining."""
        if self.total > 0:
            return (self.declines / self.total) * 100
        return 0

    @property
    def market_sentiment(self) -> str:
        """Determine market sentiment based on advance/decline ratio."""
        ratio = self.advance_decline_ratio
        if ratio > 1.5:
            return "Strong Bullish"
        elif ratio > 1.0:
            return "Bullish"
        elif ratio > 0.67:
            return "Neutral"
        elif ratio > 0.5:
            return "Bearish"
        else:
            return "Strong Bearish"


class AdvancesDeclinesSectionData(BaseModel):
    """Section data for advances or declines."""

    model_config = ConfigDict(
        populate_by_name=True,
        str_strip_whitespace=True,
    )

    identifier: str = Field(alias="indetifier", default="", description="Section identifier")
    count: MarketBreadthCount = Field(default_factory=MarketBreadthCount)
    data: list[MarketMover] = Field(default_factory=list, description="List of stocks")


class AdvancesResponse(BaseModel):
    """Response from the advances API."""

    model_config = ConfigDict(
        populate_by_name=True,
        str_strip_whitespace=True,
    )

    timestamp: str = Field(default="", description="Data timestamp")
    advance: AdvancesDeclinesSectionData = Field(default_factory=AdvancesDeclinesSectionData)

    @property
    def count(self) -> MarketBreadthCount:
        """Get the market breadth count."""
        return self.advance.count

    @property
    def stocks(self) -> list[MarketMover]:
        """Get the list of advancing stocks."""
        return self.advance.data

    @property
    def top_gainers(self) -> list[MarketMover]:
        """Get top gainers sorted by percentage change."""
        return sorted(self.stocks, key=lambda x: x.pchange, reverse=True)

    @property
    def top_by_value(self) -> list[MarketMover]:
        """Get stocks sorted by traded value."""
        return sorted(self.stocks, key=lambda x: x.total_traded_value, reverse=True)

    @property
    def top_by_volume(self) -> list[MarketMover]:
        """Get stocks sorted by traded volume."""
        return sorted(self.stocks, key=lambda x: x.total_traded_volume, reverse=True)

    def get_by_symbol(self, symbol: str) -> MarketMover | None:
        """Get stock data by symbol."""
        symbol_upper = symbol.upper()
        for stock in self.stocks:
            if stock.symbol == symbol_upper:
                return stock
        return None


class DeclinesResponse(BaseModel):
    """Response from the declines API."""

    model_config = ConfigDict(
        populate_by_name=True,
        str_strip_whitespace=True,
    )

    timestamp: str = Field(default="", description="Data timestamp")
    decline: AdvancesDeclinesSectionData = Field(default_factory=AdvancesDeclinesSectionData)

    @property
    def count(self) -> MarketBreadthCount:
        """Get the market breadth count."""
        return self.decline.count

    @property
    def stocks(self) -> list[MarketMover]:
        """Get the list of declining stocks."""
        return self.decline.data

    @property
    def top_losers(self) -> list[MarketMover]:
        """Get top losers sorted by percentage change (most negative first)."""
        return sorted(self.stocks, key=lambda x: x.pchange)

    @property
    def top_by_value(self) -> list[MarketMover]:
        """Get stocks sorted by traded value."""
        return sorted(self.stocks, key=lambda x: x.total_traded_value, reverse=True)

    @property
    def top_by_volume(self) -> list[MarketMover]:
        """Get stocks sorted by traded volume."""
        return sorted(self.stocks, key=lambda x: x.total_traded_volume, reverse=True)

    def get_by_symbol(self, symbol: str) -> MarketMover | None:
        """Get stock data by symbol."""
        symbol_upper = symbol.upper()
        for stock in self.stocks:
            if stock.symbol == symbol_upper:
                return stock
        return None


class MarketBreadthSnapshot(BaseModel):
    """Combined market breadth snapshot with advances and declines."""

    timestamp: str = Field(default="", description="Data timestamp")
    count: MarketBreadthCount = Field(default_factory=MarketBreadthCount)
    advances: list[MarketMover] = Field(default_factory=list)
    declines: list[MarketMover] = Field(default_factory=list)

    @property
    def top_gainers(self) -> list[MarketMover]:
        """Get top gainers sorted by percentage change."""
        return sorted(self.advances, key=lambda x: x.pchange, reverse=True)

    @property
    def top_losers(self) -> list[MarketMover]:
        """Get top losers sorted by percentage change."""
        return sorted(self.declines, key=lambda x: x.pchange)

    @property
    def market_sentiment(self) -> str:
        """Get overall market sentiment."""
        return self.count.market_sentiment

    @property
    def advance_decline_ratio(self) -> float:
        """Get advance/decline ratio."""
        return self.count.advance_decline_ratio
