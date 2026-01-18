"""Data models for price band hitters from NSE India."""

from pydantic import BaseModel, Field


class PriceBandHitter(BaseModel):
    """Stock hitting upper or lower price band."""

    symbol: str
    series: str | None = None
    ltp: float = Field(description="Last traded price")
    change: float = Field(description="Absolute price change")
    percent_change: float = Field(alias="pChange", description="Percentage change")
    price_band: str = Field(alias="priceBand", description="Price band percentage")
    high_price: float = Field(alias="highPrice")
    low_price: float = Field(alias="lowPrice")
    year_high: float | None = Field(alias="yearHigh", default=None)
    year_low: float | None = Field(alias="yearLow", default=None)
    total_traded_volume: int = Field(alias="totalTradedVol")
    turnover: float = Field(description="Turnover in lakhs")

    model_config = {"populate_by_name": True}

    @property
    def turnover_in_crores(self) -> float:
        """Get turnover in crores."""
        return self.turnover / 100

    @property
    def is_at_year_high(self) -> bool:
        """Check if LTP equals year high."""
        return self.year_high is not None and abs(self.ltp - self.year_high) < 0.01

    @property
    def is_at_year_low(self) -> bool:
        """Check if LTP equals year low."""
        return self.year_low is not None and abs(self.ltp - self.year_low) < 0.01


class PriceBandCategory(BaseModel):
    """Category of price band hitters (AllSec, SecGtr20, etc.)."""

    all_securities: list[PriceBandHitter] = Field(alias="AllSec", default_factory=list)
    securities_gt_20cr: list[PriceBandHitter] = Field(alias="SecGtr20", default_factory=list)
    securities_gt_10cr: list[PriceBandHitter] = Field(alias="SecGtr10", default_factory=list)
    securities_lt_10cr: list[PriceBandHitter] = Field(alias="SecLwr10", default_factory=list)

    model_config = {"populate_by_name": True}

    @property
    def count(self) -> int:
        """Total count of all securities."""
        return len(self.all_securities)


class PriceBandCount(BaseModel):
    """Count summary for price band hitters."""

    total: int = Field(alias="TOTAL")
    upper: int = Field(alias="UPPER")
    lower: int = Field(alias="LOWER")
    both: int = Field(alias="BOTH", description="Stocks at both upper and lower band (rare)")

    model_config = {"populate_by_name": True}


class PriceBandResponse(BaseModel):
    """Response containing price band hitters data."""

    upper: PriceBandCategory = Field(default_factory=PriceBandCategory)
    lower: PriceBandCategory = Field(default_factory=PriceBandCategory)
    count: PriceBandCount | None = None
    timestamp: str | None = None

    @property
    def upper_band_hitters(self) -> list[PriceBandHitter]:
        """Get all stocks hitting upper price band."""
        return self.upper.all_securities

    @property
    def lower_band_hitters(self) -> list[PriceBandHitter]:
        """Get all stocks hitting lower price band."""
        return self.lower.all_securities

    @property
    def upper_count(self) -> int:
        """Count of upper band hitters."""
        return len(self.upper.all_securities)

    @property
    def lower_count(self) -> int:
        """Count of lower band hitters."""
        return len(self.lower.all_securities)

    @property
    def upper_large_cap(self) -> list[PriceBandHitter]:
        """Get upper band hitters with turnover > 20 crores."""
        return self.upper.securities_gt_20cr

    @property
    def lower_large_cap(self) -> list[PriceBandHitter]:
        """Get lower band hitters with turnover > 20 crores."""
        return self.lower.securities_gt_20cr

    def get_by_symbol(self, symbol: str) -> tuple[PriceBandHitter | None, str | None]:
        """Find a symbol in upper or lower band.

        Returns:
            Tuple of (PriceBandHitter, band_type) where band_type is 'upper' or 'lower'.
            Returns (None, None) if not found.
        """
        symbol_upper = symbol.upper()
        for hitter in self.upper.all_securities:
            if hitter.symbol.upper() == symbol_upper:
                return hitter, "upper"
        for hitter in self.lower.all_securities:
            if hitter.symbol.upper() == symbol_upper:
                return hitter, "lower"
        return None, None

    def get_top_by_turnover(self, band: str = "both", limit: int = 10) -> list[PriceBandHitter]:
        """Get top stocks by turnover.

        Args:
            band: 'upper', 'lower', or 'both'
            limit: Maximum number of results
        """
        if band == "upper":
            stocks = self.upper.all_securities
        elif band == "lower":
            stocks = self.lower.all_securities
        else:
            stocks = self.upper.all_securities + self.lower.all_securities

        return sorted(stocks, key=lambda x: x.turnover, reverse=True)[:limit]
