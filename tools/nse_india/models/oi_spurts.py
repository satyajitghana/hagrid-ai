"""Data models for OI Spurts (Open Interest changes)."""

from pydantic import BaseModel, Field


class OISpurtData(BaseModel):
    """Model for OI spurt data showing unusual open interest changes.

    This data comes from NSE's live analysis API and shows stocks with
    significant changes in open interest, which can indicate unusual
    derivative activity.
    """

    symbol: str = Field(description="Stock symbol")
    latest_oi: int = Field(alias="latestOI", description="Latest open interest")
    prev_oi: int = Field(alias="prevOI", description="Previous open interest")
    change_in_oi: int = Field(alias="changeInOI", description="Change in open interest")
    avg_in_oi: float = Field(alias="avgInOI", description="Average % change in OI")
    volume: int = Field(description="Trading volume")
    fut_value: float = Field(alias="futValue", description="Futures value in lakhs")
    opt_value: float = Field(alias="optValue", description="Options value in lakhs")
    total: float = Field(description="Total value in lakhs")
    prem_value: float = Field(alias="premValue", description="Premium value in lakhs")
    underlying_value: float = Field(alias="underlyingValue", description="Underlying spot price")

    model_config = {"populate_by_name": True}

    @property
    def oi_change_percent(self) -> float:
        """Calculate percentage change in OI."""
        if self.prev_oi == 0:
            return 0.0
        return ((self.latest_oi - self.prev_oi) / self.prev_oi) * 100

    @property
    def is_oi_buildup(self) -> bool:
        """Check if this represents OI buildup (increase in OI)."""
        return self.change_in_oi > 0

    @property
    def is_long_unwinding(self) -> bool:
        """Check if this could represent long unwinding (OI decrease)."""
        return self.change_in_oi < 0


class OISpurtsResponse(BaseModel):
    """Response containing list of OI spurt data."""

    data: list[OISpurtData] = Field(default_factory=list)

    @property
    def oi_gainers(self) -> list[OISpurtData]:
        """Get stocks with OI buildup (increasing OI), sorted by % change."""
        gainers = [d for d in self.data if d.change_in_oi > 0]
        return sorted(gainers, key=lambda x: x.avg_in_oi, reverse=True)

    @property
    def oi_losers(self) -> list[OISpurtData]:
        """Get stocks with OI unwinding (decreasing OI), sorted by % change."""
        losers = [d for d in self.data if d.change_in_oi < 0]
        return sorted(losers, key=lambda x: x.avg_in_oi)

    @property
    def top_by_volume(self) -> list[OISpurtData]:
        """Get stocks sorted by trading volume."""
        return sorted(self.data, key=lambda x: x.volume, reverse=True)

    @property
    def top_by_total_value(self) -> list[OISpurtData]:
        """Get stocks sorted by total derivative value."""
        return sorted(self.data, key=lambda x: x.total, reverse=True)

    def get_by_symbol(self, symbol: str) -> OISpurtData | None:
        """Get OI spurt data for a specific symbol."""
        symbol = symbol.upper()
        for item in self.data:
            if item.symbol.upper() == symbol:
                return item
        return None
