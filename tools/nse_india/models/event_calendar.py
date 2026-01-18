"""Data models for NSE India event calendar."""

from datetime import date

from pydantic import BaseModel, ConfigDict, Field, field_validator


class CorporateEvent(BaseModel):
    """Corporate event from the NSE event calendar.

    This represents events like board meetings, financial results,
    dividends, bonus issues, fund raising, etc.
    """

    model_config = ConfigDict(
        populate_by_name=True,
        str_strip_whitespace=True,
    )

    symbol: str = Field(description="Stock symbol")
    company: str = Field(description="Company name")
    purpose: str = Field(description="Event purpose (e.g., Financial Results, Dividend)")
    description: str = Field(
        alias="bm_desc", description="Detailed description of the event"
    )
    event_date: date = Field(alias="date", description="Date of the event")

    @field_validator("event_date", mode="before")
    @classmethod
    def parse_date(cls, v: str | date | None) -> date | None:
        """Parse date string in DD-Mon-YYYY format."""
        if v is None:
            return None
        if isinstance(v, date):
            return v

        # Parse format like "05-Aug-2005"
        from datetime import datetime

        try:
            return datetime.strptime(v, "%d-%b-%Y").date()
        except ValueError:
            # Try other formats
            for fmt in ["%d-%B-%Y", "%Y-%m-%d", "%d-%m-%Y"]:
                try:
                    return datetime.strptime(v, fmt).date()
                except ValueError:
                    continue
            raise ValueError(f"Unable to parse date: {v}")

    @property
    def is_financial_results(self) -> bool:
        """Check if this event is related to financial results."""
        purpose_lower = self.purpose.lower()
        return "result" in purpose_lower or "financial" in purpose_lower

    @property
    def is_dividend(self) -> bool:
        """Check if this event is related to dividend."""
        return "dividend" in self.purpose.lower()

    @property
    def is_bonus(self) -> bool:
        """Check if this event is related to bonus shares."""
        return "bonus" in self.purpose.lower()

    @property
    def is_fund_raising(self) -> bool:
        """Check if this event is related to fund raising."""
        return "fund" in self.purpose.lower() and "raising" in self.purpose.lower()
