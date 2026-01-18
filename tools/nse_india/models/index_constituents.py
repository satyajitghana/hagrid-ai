"""Data models for NSE India index constituents data."""

from datetime import date

from pydantic import BaseModel, ConfigDict, Field, computed_field


class IndexMaster(BaseModel):
    """Master list of all available indices on NSE."""

    model_config = ConfigDict(
        populate_by_name=True,
        str_strip_whitespace=True,
    )

    derivatives_eligible: list[str] = Field(
        alias="Indices Eligible In Derivatives",
        default_factory=list,
        description="Indices eligible for derivatives trading"
    )
    broad_market: list[str] = Field(
        alias="Broad Market Indices",
        default_factory=list,
        description="Broad market indices"
    )
    sectoral: list[str] = Field(
        alias="Sectoral Market Indices",
        default_factory=list,
        description="Sectoral market indices"
    )
    thematic: list[str] = Field(
        alias="Thematic Market Indices",
        default_factory=list,
        description="Thematic market indices"
    )
    strategy: list[str] = Field(
        alias="Strategy Market Indices",
        default_factory=list,
        description="Strategy market indices"
    )
    others: list[str] = Field(
        alias="Others",
        default_factory=list,
        description="Other indices (F&O securities, etc.)"
    )

    @property
    def all_indices(self) -> list[str]:
        """Get all index names."""
        return (
            self.derivatives_eligible +
            self.broad_market +
            self.sectoral +
            self.thematic +
            self.strategy +
            self.others
        )

    @property
    def total_count(self) -> int:
        """Get total number of indices."""
        return len(self.all_indices)

    def get_category(self, index_name: str) -> str | None:
        """Get the category of an index."""
        if index_name in self.derivatives_eligible:
            return "Derivatives Eligible"
        elif index_name in self.broad_market:
            return "Broad Market"
        elif index_name in self.sectoral:
            return "Sectoral"
        elif index_name in self.thematic:
            return "Thematic"
        elif index_name in self.strategy:
            return "Strategy"
        elif index_name in self.others:
            return "Others"
        return None


class StockMeta(BaseModel):
    """Metadata for a stock in an index."""

    model_config = ConfigDict(
        populate_by_name=True,
        str_strip_whitespace=True,
    )

    symbol: str = Field(default="", description="Stock symbol")
    company_name: str = Field(alias="companyName", default="", description="Company name")
    industry: str = Field(default="", description="Industry sector")
    active_series: list[str] = Field(alias="activeSeries", default_factory=list)
    is_fno_sec: bool = Field(alias="isFNOSec", default=False, description="Is F&O security")
    is_slb_sec: bool = Field(alias="isSLBSec", default=False, description="Is SLB security")
    is_etf_sec: bool = Field(alias="isETFSec", default=False, description="Is ETF")
    is_delisted: bool = Field(alias="isDelisted", default=False, description="Is delisted")
    is_suspended: bool = Field(alias="isSuspended", default=False, description="Is suspended")
    isin: str = Field(default="", description="ISIN code")
    listing_date: str = Field(alias="listingDate", default="", description="Listing date")
    segment: str = Field(default="", description="Market segment")


class IndexConstituent(BaseModel):
    """Individual stock constituent of an index."""

    model_config = ConfigDict(
        populate_by_name=True,
        str_strip_whitespace=True,
    )

    priority: int = Field(default=0, description="Priority (1 for index itself)")
    symbol: str = Field(default="", description="Stock symbol")
    identifier: str = Field(default="", description="Unique identifier")
    series: str = Field(default="", description="Series (EQ, BE, etc.)")

    # Price data
    open: float = Field(default=0, description="Opening price")
    day_high: float = Field(alias="dayHigh", default=0, description="Day high")
    day_low: float = Field(alias="dayLow", default=0, description="Day low")
    last_price: float = Field(alias="lastPrice", default=0, description="Last traded price")
    previous_close: float = Field(alias="previousClose", default=0, description="Previous close")
    change: float = Field(default=0, description="Absolute change")
    pchange: float = Field(alias="pChange", default=0, description="Percentage change")

    # Volume and market cap
    total_traded_volume: int = Field(
        alias="totalTradedVolume", default=0,
        description="Total traded volume"
    )
    total_traded_value: float = Field(
        alias="totalTradedValue", default=0,
        description="Total traded value"
    )
    ffmc: float = Field(default=0, description="Free float market cap")

    # 52-week data
    year_high: float = Field(alias="yearHigh", default=0, description="52-week high")
    year_low: float = Field(alias="yearLow", default=0, description="52-week low")
    near_wkh: float = Field(alias="nearWKH", default=0, description="% away from 52-week high")
    near_wkl: float = Field(alias="nearWKL", default=0, description="% away from 52-week low")

    # Performance
    per_change_365d: float = Field(alias="perChange365d", default=0, description="1 year % change")
    per_change_30d: float = Field(alias="perChange30d", default=0, description="30 day % change")
    date_365d_ago: str | None = Field(alias="date365dAgo", default=None)
    date_30d_ago: str | None = Field(alias="date30dAgo", default=None)

    # Chart paths
    chart_today_path: str | None = Field(alias="chartTodayPath", default=None)
    chart_30d_path: str | None = Field(alias="chart30dPath", default=None)
    chart_365d_path: str | None = Field(alias="chart365dPath", default=None)

    # Last update
    last_update_time: str = Field(alias="lastUpdateTime", default="")

    # Stock metadata (optional, may not be present for index row)
    meta: StockMeta | None = Field(default=None, description="Stock metadata")

    @property
    def is_index_row(self) -> bool:
        """Check if this is the index row (not a constituent)."""
        return self.priority == 1

    @property
    def company_name(self) -> str:
        """Get company name from metadata."""
        return self.meta.company_name if self.meta else ""

    @property
    def industry(self) -> str:
        """Get industry from metadata."""
        return self.meta.industry if self.meta else ""

    @property
    def is_fno(self) -> bool:
        """Check if stock is F&O eligible."""
        return self.meta.is_fno_sec if self.meta else False

    @property
    def isin(self) -> str:
        """Get ISIN code."""
        return self.meta.isin if self.meta else ""

    @property
    def is_advancing(self) -> bool:
        """Check if stock is advancing."""
        return self.pchange > 0

    @property
    def is_declining(self) -> bool:
        """Check if stock is declining."""
        return self.pchange < 0

    @property
    def near_52_week_high(self) -> bool:
        """Check if within 5% of 52-week high."""
        return self.near_wkh <= 5 if self.near_wkh else False

    @property
    def near_52_week_low(self) -> bool:
        """Check if within 5% of 52-week low."""
        return abs(self.near_wkl) <= 5 if self.near_wkl else False


class IndexAdvanceDecline(BaseModel):
    """Advance/decline data for an index."""

    model_config = ConfigDict(
        populate_by_name=True,
        str_strip_whitespace=True,
    )

    advances: str = Field(default="0", description="Number of advancing stocks")
    declines: str = Field(default="0", description="Number of declining stocks")
    unchanged: str = Field(default="0", description="Number of unchanged stocks")

    @property
    def advances_int(self) -> int:
        """Get advances as integer."""
        return int(self.advances) if self.advances else 0

    @property
    def declines_int(self) -> int:
        """Get declines as integer."""
        return int(self.declines) if self.declines else 0

    @property
    def unchanged_int(self) -> int:
        """Get unchanged as integer."""
        return int(self.unchanged) if self.unchanged else 0

    @property
    def total(self) -> int:
        """Get total count."""
        return self.advances_int + self.declines_int + self.unchanged_int

    @computed_field
    @property
    def advance_decline_ratio(self) -> float:
        """Calculate A/D ratio."""
        if self.declines_int > 0:
            return self.advances_int / self.declines_int
        return float('inf') if self.advances_int > 0 else 0

    @property
    def market_sentiment(self) -> str:
        """Get market sentiment based on A/D ratio."""
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


class IndexConstituentsResponse(BaseModel):
    """Response from the index constituents API."""

    model_config = ConfigDict(
        populate_by_name=True,
        str_strip_whitespace=True,
    )

    name: str = Field(default="", description="Index name")
    advance: IndexAdvanceDecline = Field(default_factory=IndexAdvanceDecline)
    timestamp: str = Field(default="", description="Data timestamp")
    data: list[IndexConstituent] = Field(default_factory=list, description="Index data")

    @property
    def index_data(self) -> IndexConstituent | None:
        """Get the index row (first row with priority=1)."""
        for item in self.data:
            if item.is_index_row:
                return item
        return None

    @property
    def constituents(self) -> list[IndexConstituent]:
        """Get only the stock constituents (excluding index row)."""
        return [item for item in self.data if not item.is_index_row]

    @property
    def constituent_count(self) -> int:
        """Get number of constituents."""
        return len(self.constituents)

    @property
    def symbols(self) -> list[str]:
        """Get list of all constituent symbols."""
        return [c.symbol for c in self.constituents]

    @property
    def top_gainers(self) -> list[IndexConstituent]:
        """Get constituents sorted by % change (descending)."""
        return sorted(self.constituents, key=lambda x: x.pchange, reverse=True)

    @property
    def top_losers(self) -> list[IndexConstituent]:
        """Get constituents sorted by % change (ascending)."""
        return sorted(self.constituents, key=lambda x: x.pchange)

    @property
    def advancing_stocks(self) -> list[IndexConstituent]:
        """Get advancing stocks."""
        return [c for c in self.constituents if c.is_advancing]

    @property
    def declining_stocks(self) -> list[IndexConstituent]:
        """Get declining stocks."""
        return [c for c in self.constituents if c.is_declining]

    @property
    def near_52_week_highs(self) -> list[IndexConstituent]:
        """Get stocks near 52-week high."""
        return [c for c in self.constituents if c.near_52_week_high]

    @property
    def near_52_week_lows(self) -> list[IndexConstituent]:
        """Get stocks near 52-week low."""
        return [c for c in self.constituents if c.near_52_week_low]

    @property
    def fno_stocks(self) -> list[IndexConstituent]:
        """Get F&O eligible stocks."""
        return [c for c in self.constituents if c.is_fno]

    @property
    def total_market_cap(self) -> float:
        """Get total free float market cap of all constituents."""
        return sum(c.ffmc for c in self.constituents)

    @property
    def total_traded_value(self) -> float:
        """Get total traded value of all constituents."""
        return sum(c.total_traded_value for c in self.constituents)

    def get_by_symbol(self, symbol: str) -> IndexConstituent | None:
        """Get constituent by symbol."""
        symbol_upper = symbol.upper()
        for c in self.constituents:
            if c.symbol == symbol_upper:
                return c
        return None

    def filter_by_industry(self, industry: str) -> list[IndexConstituent]:
        """Filter constituents by industry."""
        industry_lower = industry.lower()
        return [
            c for c in self.constituents
            if industry_lower in c.industry.lower()
        ]

    def top_by_market_cap(self, limit: int = 10) -> list[IndexConstituent]:
        """Get top constituents by market cap."""
        return sorted(self.constituents, key=lambda x: x.ffmc, reverse=True)[:limit]

    def top_by_volume(self, limit: int = 10) -> list[IndexConstituent]:
        """Get top constituents by volume."""
        return sorted(
            self.constituents,
            key=lambda x: x.total_traded_volume,
            reverse=True
        )[:limit]

    def top_by_value(self, limit: int = 10) -> list[IndexConstituent]:
        """Get top constituents by traded value."""
        return sorted(
            self.constituents,
            key=lambda x: x.total_traded_value,
            reverse=True
        )[:limit]

    def top_yearly_performers(self, limit: int = 10) -> list[IndexConstituent]:
        """Get top performers by 1-year return."""
        return sorted(
            self.constituents,
            key=lambda x: x.per_change_365d,
            reverse=True
        )[:limit]

    def worst_yearly_performers(self, limit: int = 10) -> list[IndexConstituent]:
        """Get worst performers by 1-year return."""
        return sorted(self.constituents, key=lambda x: x.per_change_365d)[:limit]
