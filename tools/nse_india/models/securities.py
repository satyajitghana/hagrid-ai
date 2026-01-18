"""Data models for NSE India listed securities."""

from datetime import date, datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


class TradingSeries(StrEnum):
    """Trading series on NSE."""

    EQ = "EQ"  # Equity - Normal trading
    BE = "BE"  # Book Entry - Trade-to-trade settlement
    BZ = "BZ"  # Trade-to-trade settlement (suspended companies)
    SM = "SM"  # SME segment
    ST = "ST"  # SME trade-to-trade


def _parse_listing_date(v: Any) -> date | None:
    """Parse listing date from NSE format (DD-MMM-YYYY)."""
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
        # Try DD-MMM-YYYY format (e.g., "06-OCT-2008")
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
    """Parse integer value."""
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


class Security(BaseModel):
    """Listed security on NSE.

    Represents a stock/security available for trading on the National Stock Exchange.
    """

    model_config = ConfigDict(
        populate_by_name=True,
        str_strip_whitespace=True,
    )

    symbol: str = Field(alias="SYMBOL", description="Trading symbol")
    company_name: str = Field(alias="NAME OF COMPANY", description="Company name")
    series: str = Field(alias=" SERIES", description="Trading series (EQ, BE, BZ, etc.)")
    listing_date: date | None = Field(
        alias=" DATE OF LISTING",
        default=None,
        description="Date when security was listed",
    )
    paid_up_value: int | None = Field(
        alias=" PAID UP VALUE",
        default=None,
        description="Paid up value per share",
    )
    market_lot: int = Field(
        alias=" MARKET LOT",
        default=1,
        description="Market lot size",
    )
    isin: str = Field(alias=" ISIN NUMBER", description="ISIN identifier")
    face_value: int | None = Field(
        alias=" FACE VALUE",
        default=None,
        description="Face value per share",
    )

    @field_validator("listing_date", mode="before")
    @classmethod
    def parse_listing_date(cls, v: Any) -> date | None:
        return _parse_listing_date(v)

    @field_validator("paid_up_value", "market_lot", "face_value", mode="before")
    @classmethod
    def parse_int_field(cls, v: Any) -> int | None:
        return _parse_int(v)

    @field_validator("series", mode="before")
    @classmethod
    def clean_series(cls, v: Any) -> str:
        if v is None:
            return "EQ"
        return str(v).strip()

    @property
    def is_equity(self) -> bool:
        """Check if this is a regular equity security."""
        return self.series == "EQ"

    @property
    def is_trade_to_trade(self) -> bool:
        """Check if this security is in trade-to-trade segment."""
        return self.series in ["BE", "BZ"]

    @property
    def is_sme(self) -> bool:
        """Check if this is an SME security."""
        return self.series in ["SM", "ST"]

    @property
    def years_listed(self) -> int | None:
        """Calculate years since listing."""
        if self.listing_date:
            today = date.today()
            return today.year - self.listing_date.year
        return None


class SecuritiesResponse(BaseModel):
    """Response containing all listed securities on NSE."""

    model_config = ConfigDict(str_strip_whitespace=True)

    securities: list[Security] = Field(
        default_factory=list,
        description="List of all listed securities",
    )
    total_count: int = Field(default=0, description="Total number of securities")

    @property
    def equity_securities(self) -> list[Security]:
        """Get all regular equity securities."""
        return [s for s in self.securities if s.is_equity]

    @property
    def trade_to_trade_securities(self) -> list[Security]:
        """Get all trade-to-trade securities."""
        return [s for s in self.securities if s.is_trade_to_trade]

    @property
    def sme_securities(self) -> list[Security]:
        """Get all SME securities."""
        return [s for s in self.securities if s.is_sme]

    def get_by_symbol(self, symbol: str) -> Security | None:
        """Get security by symbol."""
        symbol_upper = symbol.upper()
        for sec in self.securities:
            if sec.symbol.upper() == symbol_upper:
                return sec
        return None

    def get_by_isin(self, isin: str) -> Security | None:
        """Get security by ISIN."""
        isin_upper = isin.upper()
        for sec in self.securities:
            if sec.isin.upper() == isin_upper:
                return sec
        return None

    def search_by_name(self, query: str) -> list[Security]:
        """Search securities by company name (case-insensitive partial match)."""
        query_lower = query.lower()
        return [s for s in self.securities if query_lower in s.company_name.lower()]

    def get_by_series(self, series: str) -> list[Security]:
        """Get all securities of a specific series."""
        series_upper = series.upper()
        return [s for s in self.securities if s.series.upper() == series_upper]

    def get_recently_listed(self, days: int = 30) -> list[Security]:
        """Get securities listed within the specified days."""
        from datetime import timedelta

        cutoff = date.today() - timedelta(days=days)
        return [
            s for s in self.securities
            if s.listing_date and s.listing_date >= cutoff
        ]

    def get_listed_in_year(self, year: int) -> list[Security]:
        """Get securities listed in a specific year."""
        return [
            s for s in self.securities
            if s.listing_date and s.listing_date.year == year
        ]

    def get_symbols(self) -> list[str]:
        """Get list of all symbols."""
        return [s.symbol for s in self.securities]

    def get_series_counts(self) -> dict[str, int]:
        """Get count of securities by series."""
        counts: dict[str, int] = {}
        for sec in self.securities:
            counts[sec.series] = counts.get(sec.series, 0) + 1
        return counts
