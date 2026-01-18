"""Data models for NSE India market indices."""

from datetime import date, datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


class IndexCategory(StrEnum):
    """Categories of market indices."""

    DERIVATIVES_ELIGIBLE = "INDICES ELIGIBLE IN DERIVATIVES"
    BROAD_MARKET = "BROAD MARKET INDICES"
    SECTORAL = "SECTORAL INDICES"
    THEMATIC = "THEMATIC INDICES"
    STRATEGY = "STRATEGY INDICES"
    FIXED_INCOME = "FIXED INCOME INDICES"


def _parse_float(v: Any) -> float | None:
    """Parse a float value, handling empty strings and dashes."""
    if v is None:
        return None
    if isinstance(v, (int, float)):
        return float(v)
    if isinstance(v, str):
        v = v.strip()
        if v == "" or v == "-" or v == "null":
            return None
        try:
            return float(v.replace(",", ""))
        except ValueError:
            return None
    return None


def _parse_int(v: Any) -> int | None:
    """Parse an int value, handling empty strings and dashes."""
    if v is None:
        return None
    if isinstance(v, int):
        return v
    if isinstance(v, float):
        return int(v)
    if isinstance(v, str):
        v = v.strip()
        if v == "" or v == "-" or v == "null":
            return None
        try:
            return int(float(v.replace(",", "")))
        except ValueError:
            return None
    return None


class IndexData(BaseModel):
    """Market index data from NSE India.

    Contains real-time and historical data for NSE indices including
    price data, valuation metrics, market breadth, and performance metrics.
    """

    model_config = ConfigDict(
        populate_by_name=True,
        str_strip_whitespace=True,
    )

    # Index identification
    category: str = Field(alias="key", description="Index category/group")
    index_name: str = Field(alias="index", description="Full index name")
    symbol: str = Field(alias="indexSymbol", description="Index symbol/short name")

    # Price data
    last: float = Field(description="Last traded price/value")
    variation: float = Field(description="Absolute change from previous close")
    percent_change: float = Field(alias="percentChange", description="Percentage change")
    open: float = Field(description="Opening value")
    high: float = Field(description="Day high")
    low: float = Field(description="Day low")
    previous_close: float = Field(alias="previousClose", description="Previous day close")
    indicative_close: float | None = Field(
        alias="indicativeClose", default=None, description="Indicative closing value"
    )

    # 52-week range
    year_high: float = Field(alias="yearHigh", description="52-week high")
    year_low: float = Field(alias="yearLow", description="52-week low")

    # Valuation metrics (may be empty for some indices like VIX)
    pe: float | None = Field(default=None, description="Price to Earnings ratio")
    pb: float | None = Field(default=None, description="Price to Book ratio")
    dy: float | None = Field(default=None, description="Dividend Yield percentage")

    # Market breadth
    advances: int | None = Field(default=None, description="Number of advancing stocks")
    declines: int | None = Field(default=None, description="Number of declining stocks")
    unchanged: int | None = Field(default=None, description="Number of unchanged stocks")

    # Performance metrics
    percent_change_365d: float | None = Field(
        alias="perChange365d", default=None, description="1-year percentage change"
    )
    percent_change_30d: float | None = Field(
        alias="perChange30d", default=None, description="30-day percentage change"
    )

    # Historical reference dates
    date_365d_ago: str | None = Field(alias="date365dAgo", default=None)
    date_30d_ago: str | None = Field(alias="date30dAgo", default=None)
    previous_day: str | None = Field(alias="previousDay", default=None)
    one_week_ago: str | None = Field(alias="oneWeekAgo", default=None)

    # Historical values
    one_month_ago_val: float | None = Field(alias="oneMonthAgoVal", default=None)
    one_week_ago_val: float | None = Field(alias="oneWeekAgoVal", default=None)
    one_year_ago_val: float | None = Field(alias="oneYearAgoVal", default=None)
    previous_day_val: float | None = Field(alias="previousDayVal", default=None)

    # Chart URLs
    chart_365d_path: str | None = Field(
        alias="chart365dPath", default=None, description="URL to 365-day chart SVG"
    )
    chart_30d_path: str | None = Field(
        alias="chart30dPath", default=None, description="URL to 30-day chart SVG"
    )
    chart_today_path: str | None = Field(
        alias="chartTodayPath", default=None, description="URL to today's chart SVG"
    )

    @field_validator("pe", "pb", "dy", mode="before")
    @classmethod
    def parse_valuation(cls, v: Any) -> float | None:
        return _parse_float(v)

    @field_validator("advances", "declines", "unchanged", mode="before")
    @classmethod
    def parse_breadth(cls, v: Any) -> int | None:
        return _parse_int(v)

    @property
    def is_positive(self) -> bool:
        """Check if index is in positive territory."""
        return self.variation >= 0

    @property
    def day_range(self) -> tuple[float, float]:
        """Get the day's trading range."""
        return (self.low, self.high)

    @property
    def year_range(self) -> tuple[float, float]:
        """Get the 52-week range."""
        return (self.year_low, self.year_high)

    @property
    def distance_from_52w_high(self) -> float:
        """Calculate percentage distance from 52-week high."""
        if self.year_high > 0:
            return ((self.year_high - self.last) / self.year_high) * 100
        return 0.0

    @property
    def distance_from_52w_low(self) -> float:
        """Calculate percentage distance from 52-week low."""
        if self.year_low > 0:
            return ((self.last - self.year_low) / self.year_low) * 100
        return 0.0

    @property
    def market_breadth_ratio(self) -> float | None:
        """Calculate advance/decline ratio."""
        if self.advances is not None and self.declines is not None and self.declines > 0:
            return self.advances / self.declines
        return None

    @property
    def is_derivatives_eligible(self) -> bool:
        """Check if index is eligible for derivatives trading."""
        return self.category == IndexCategory.DERIVATIVES_ELIGIBLE

    @property
    def is_sectoral(self) -> bool:
        """Check if this is a sectoral index."""
        return self.category == IndexCategory.SECTORAL

    @property
    def is_broad_market(self) -> bool:
        """Check if this is a broad market index."""
        return self.category == IndexCategory.BROAD_MARKET

    @property
    def weekly_change(self) -> float | None:
        """Calculate weekly percentage change."""
        if self.one_week_ago_val and self.one_week_ago_val > 0:
            return ((self.last - self.one_week_ago_val) / self.one_week_ago_val) * 100
        return None


class AllIndicesResponse(BaseModel):
    """Response container for all indices data."""

    model_config = ConfigDict(str_strip_whitespace=True)

    indices: list[IndexData] = Field(default_factory=list, description="List of all indices")
    timestamp: datetime | None = Field(default=None, description="Data timestamp")

    @property
    def derivatives_eligible(self) -> list[IndexData]:
        """Get indices eligible for derivatives trading."""
        return [i for i in self.indices if i.is_derivatives_eligible]

    @property
    def broad_market(self) -> list[IndexData]:
        """Get broad market indices."""
        return [i for i in self.indices if i.is_broad_market]

    @property
    def sectoral(self) -> list[IndexData]:
        """Get sectoral indices."""
        return [i for i in self.indices if i.is_sectoral]

    @property
    def gainers(self) -> list[IndexData]:
        """Get indices with positive change, sorted by percent change."""
        return sorted(
            [i for i in self.indices if i.percent_change > 0],
            key=lambda x: x.percent_change,
            reverse=True,
        )

    @property
    def losers(self) -> list[IndexData]:
        """Get indices with negative change, sorted by percent change."""
        return sorted(
            [i for i in self.indices if i.percent_change < 0],
            key=lambda x: x.percent_change,
        )

    def get_by_symbol(self, symbol: str) -> IndexData | None:
        """Get index by symbol."""
        symbol_upper = symbol.upper()
        for index in self.indices:
            if index.symbol.upper() == symbol_upper:
                return index
        return None

    def get_by_category(self, category: str | IndexCategory) -> list[IndexData]:
        """Get indices by category."""
        cat_str = category.value if isinstance(category, IndexCategory) else category
        return [i for i in self.indices if i.category == cat_str]

    def filter_by_pe_range(self, min_pe: float = 0, max_pe: float = 100) -> list[IndexData]:
        """Filter indices by PE ratio range."""
        return [
            i for i in self.indices
            if i.pe is not None and min_pe <= i.pe <= max_pe
        ]

    def get_categories(self) -> list[str]:
        """Get list of unique categories."""
        return list(set(i.category for i in self.indices))
