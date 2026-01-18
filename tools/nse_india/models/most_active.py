"""Data models for most active securities from NSE India."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field, field_validator


def _parse_float(v: Any) -> float | None:
    """Parse a float value from NSE API."""
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


class MostActiveEquity(BaseModel):
    """Most active equity security by value or volume."""

    symbol: str
    identifier: str | None = None
    last_price: float = Field(alias="lastPrice")
    percent_change: float = Field(alias="pChange")
    quantity_traded: int | None = Field(alias="quantityTraded", default=None)
    total_traded_volume: int = Field(alias="totalTradedVolume")
    total_traded_value: float = Field(alias="totalTradedValue")
    previous_close: float = Field(alias="previousClose")
    ex_date: str | None = Field(alias="exDate", default=None)
    purpose: str | None = None
    year_high: float | None = Field(alias="yearHigh", default=None)
    year_low: float | None = Field(alias="yearLow", default=None)
    change: float | None = None
    open: float | None = None
    close_price: float | None = Field(alias="closePrice", default=None)
    day_high: float | None = Field(alias="dayHigh", default=None)
    day_low: float | None = Field(alias="dayLow", default=None)
    last_update_time: str | None = Field(alias="lastUpdateTime", default=None)

    model_config = {"populate_by_name": True}

    @property
    def is_gainer(self) -> bool:
        """Check if this is a gainer."""
        return self.percent_change > 0

    @property
    def value_in_crores(self) -> float:
        """Get traded value in crores."""
        return self.total_traded_value / 10000000


class MostActiveSME(BaseModel):
    """Most active SME security by volume."""

    symbol: str
    identifier: str | None = None
    last_price: float = Field(alias="lastPrice")
    percent_change: float = Field(alias="pChange")
    total_traded_volume: int = Field(alias="totalTradedVolume")
    total_traded_value: float = Field(alias="totalTradedValue")
    open: float | None = None
    day_high: float | None = Field(alias="dayHigh", default=None)
    day_low: float | None = Field(alias="dayLow", default=None)
    year_high: float | None = Field(alias="yearHigh", default=None)
    year_low: float | None = Field(alias="yearLow", default=None)
    previous_close: float = Field(alias="previousClose")
    purpose: str | None = None
    ex_date: str | None = Field(alias="exDate", default=None)

    model_config = {"populate_by_name": True}

    @property
    def is_gainer(self) -> bool:
        """Check if this is a gainer."""
        return self.percent_change > 0


class MostActiveETF(BaseModel):
    """Most active ETF by volume."""

    symbol: str
    identifier: str | None = None
    last_price: float = Field(alias="lastPrice")
    percent_change: float = Field(alias="pChange")
    total_traded_volume: int = Field(alias="totalTradedVolume")
    total_traded_value: float = Field(alias="totalTradedValue")
    nav: float | None = None
    open: float | None = None
    day_high: float | None = Field(alias="dayHigh", default=None)
    day_low: float | None = Field(alias="dayLow", default=None)
    close_price: float | None = Field(alias="closePrice", default=None)
    previous_close: float = Field(alias="previousClose")

    model_config = {"populate_by_name": True}

    @property
    def premium_discount(self) -> float | None:
        """Calculate premium/discount to NAV."""
        if self.nav and self.nav > 0:
            return ((self.last_price - self.nav) / self.nav) * 100
        return None

    @property
    def is_gainer(self) -> bool:
        """Check if this is a gainer."""
        return self.percent_change > 0


class PriceVariation(BaseModel):
    """Stock with significant price variation (gainer/loser)."""

    symbol: str
    series: str | None = None
    open_price: float = Field(alias="open_price")
    high_price: float = Field(alias="high_price")
    low_price: float = Field(alias="low_price")
    ltp: float
    prev_price: float = Field(alias="prev_price")
    net_price: float = Field(alias="net_price")  # Same as perChange
    trade_quantity: int = Field(alias="trade_quantity")
    turnover: float
    market_type: str | None = Field(alias="market_type", default=None)
    ca_ex_date: str | None = Field(alias="ca_ex_dt", default=None)
    ca_purpose: str | None = Field(alias="ca_purpose", default=None)
    percent_change: float = Field(alias="perChange")

    model_config = {"populate_by_name": True}

    @property
    def is_gainer(self) -> bool:
        """Check if this is a gainer."""
        return self.percent_change > 0

    @property
    def has_corporate_action(self) -> bool:
        """Check if there's an upcoming corporate action."""
        return self.ca_purpose is not None and self.ca_purpose != "-"


class VolumeGainer(BaseModel):
    """Stock with significant volume increase compared to average."""

    symbol: str
    company_name: str = Field(alias="companyName")
    volume: int
    week1_avg_volume: int = Field(alias="week1AvgVolume")
    week1_vol_change: float = Field(alias="week1volChange")
    week2_avg_volume: int = Field(alias="week2AvgVolume")
    week2_vol_change: float = Field(alias="week2volChange")
    ltp: float
    percent_change: float = Field(alias="pChange")
    turnover: float

    model_config = {"populate_by_name": True}

    @property
    def volume_spike_ratio(self) -> float:
        """Get the volume spike ratio (current vs 1-week avg)."""
        return self.week1_vol_change

    @property
    def is_price_gainer(self) -> bool:
        """Check if price is also up."""
        return self.percent_change > 0


class MostActiveResponse(BaseModel):
    """Response containing most active securities data."""

    equities: list[MostActiveEquity] = Field(default_factory=list)
    timestamp: str | None = None

    @property
    def by_value(self) -> list[MostActiveEquity]:
        """Get securities sorted by traded value."""
        return sorted(self.equities, key=lambda x: x.total_traded_value, reverse=True)

    @property
    def by_volume(self) -> list[MostActiveEquity]:
        """Get securities sorted by traded volume."""
        return sorted(self.equities, key=lambda x: x.total_traded_volume, reverse=True)

    @property
    def gainers(self) -> list[MostActiveEquity]:
        """Get only gainers."""
        return [e for e in self.equities if e.is_gainer]

    @property
    def losers(self) -> list[MostActiveEquity]:
        """Get only losers."""
        return [e for e in self.equities if not e.is_gainer]


class MostActiveSMEResponse(BaseModel):
    """Response containing most active SME data."""

    data: list[MostActiveSME] = Field(default_factory=list)
    timestamp: str | None = None


class MostActiveETFResponse(BaseModel):
    """Response containing most active ETF data."""

    data: list[MostActiveETF] = Field(default_factory=list)
    nav_date: str | None = Field(alias="navDate", default=None)
    timestamp: str | None = None
    nav_data: dict[str, float] = Field(alias="navData", default_factory=dict)

    model_config = {"populate_by_name": True}


class PriceVariationsResponse(BaseModel):
    """Response containing price gainers/losers."""

    data: list[PriceVariation] = Field(default_factory=list)
    timestamp: str | None = None


class VolumeGainersResponse(BaseModel):
    """Response containing volume gainers."""

    data: list[VolumeGainer] = Field(default_factory=list)
    timestamp: str | None = None

    @property
    def top_volume_spikes(self) -> list[VolumeGainer]:
        """Get stocks with highest volume spike."""
        return sorted(self.data, key=lambda x: x.week1_vol_change, reverse=True)

    @property
    def price_and_volume_gainers(self) -> list[VolumeGainer]:
        """Get stocks where both price and volume are up."""
        return [v for v in self.data if v.is_price_gainer]
