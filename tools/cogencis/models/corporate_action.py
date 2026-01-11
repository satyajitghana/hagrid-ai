"""Corporate action models for Cogencis API."""

from datetime import datetime
from typing import Any
from pydantic import BaseModel, Field, field_validator

from .common import PagingInfo, ColumnDefinition


class CorporateAction(BaseModel):
    """Individual corporate action.
    
    Field mappings from API:
    - f_79: purpose (Dividend/Bonus/Rights/Demerger/etc.)
    - f_81: ex_date (ISO format)
    - f_80: face_value
    - f_82: record_date (ISO format)
    - f_25008: path
    - isin: ISIN code
    - exchangesymbol: Exchange symbol
    - xface_value: Face value (alternative)
    - xEx_Date: Ex date (alternative)
    - xPurpose: Purpose (alternative)
    - xRecord_Date: Record date (alternative)
    - xBC_Start_Date: Book closure start date
    - xBC_End_Date: Book closure end date
    """

    purpose: str = Field(alias="f_79")
    ex_date: str | None = Field(default=None, alias="f_81")
    face_value: float | None = Field(default=None, alias="f_80")
    record_date: str | None = Field(default=None, alias="f_82")
    path: str = Field(alias="f_25008")
    isin: str | None = None
    exchange_symbol: str | None = Field(default=None, alias="exchangesymbol")
    book_closure_start: str | None = Field(default=None, alias="xBC_Start_Date")
    book_closure_end: str | None = Field(default=None, alias="xBC_End_Date")

    @field_validator("face_value", mode="before")
    @classmethod
    def parse_face_value(cls, v: Any) -> float | None:
        """Parse face value which may come as string."""
        if v is None:
            return None
        if isinstance(v, str):
            try:
                return float(v.replace(",", ""))
            except ValueError:
                return None
        return float(v)

    @property
    def ex_date_parsed(self) -> datetime | None:
        """Parse ex_date to datetime object."""
        if not self.ex_date:
            return None
        try:
            # Format: "2025-08-13T18:30:00.000Z"
            return datetime.fromisoformat(self.ex_date.replace("Z", "+00:00"))
        except (ValueError, TypeError):
            return None

    @property
    def record_date_parsed(self) -> datetime | None:
        """Parse record_date to datetime object."""
        if not self.record_date:
            return None
        try:
            return datetime.fromisoformat(self.record_date.replace("Z", "+00:00"))
        except (ValueError, TypeError):
            return None

    @property
    def is_dividend(self) -> bool:
        """Check if this is a dividend action."""
        return "dividend" in self.purpose.lower()

    @property
    def is_bonus(self) -> bool:
        """Check if this is a bonus issue."""
        return "bonus" in self.purpose.lower()

    @property
    def is_rights(self) -> bool:
        """Check if this is a rights issue."""
        return "rights" in self.purpose.lower()

    @property
    def is_split(self) -> bool:
        """Check if this is a stock split."""
        return "split" in self.purpose.lower()

    @property
    def is_demerger(self) -> bool:
        """Check if this is a demerger."""
        return "demerger" in self.purpose.lower()

    @property
    def dividend_amount(self) -> float | None:
        """Extract dividend amount from purpose string if it's a dividend."""
        if not self.is_dividend:
            return None
        # Try to extract amount from purpose like "Dividend - Rs 5.5 Per Share"
        import re
        match = re.search(r"rs\.?\s*([\d.]+)", self.purpose.lower())
        if match:
            try:
                return float(match.group(1))
            except ValueError:
                return None
        return None

    @property
    def bonus_ratio(self) -> str | None:
        """Extract bonus ratio from purpose string if it's a bonus."""
        if not self.is_bonus:
            return None
        # Try to extract ratio from purpose like "Bonus 1:1"
        import re
        match = re.search(r"bonus\s*([\d:]+)", self.purpose.lower())
        if match:
            return match.group(1)
        return None

    class Config:
        populate_by_name = True


class CorporateActionResponseData(BaseModel):
    """Paginated corporate action response data from API."""

    paging_info: PagingInfo = Field(alias="pagingInfo")
    columns: list[ColumnDefinition]
    data: list[CorporateAction]

    class Config:
        populate_by_name = True


class CorporateActionResponse(BaseModel):
    """Response model for corporate action API."""

    status: bool
    message: str
    response: CorporateActionResponseData | None = None

    @property
    def is_success(self) -> bool:
        """Check if the response indicates success."""
        return self.status is True

    @property
    def actions(self) -> list[CorporateAction]:
        """Get list of corporate actions."""
        if self.response:
            return self.response.data
        return []

    @property
    def total_results(self) -> int:
        """Get total number of actions available."""
        if self.response:
            return self.response.paging_info.total_records
        return 0

    @property
    def dividends(self) -> list[CorporateAction]:
        """Get only dividend actions."""
        return [a for a in self.actions if a.is_dividend]

    @property
    def bonuses(self) -> list[CorporateAction]:
        """Get only bonus issues."""
        return [a for a in self.actions if a.is_bonus]

    @property
    def rights_issues(self) -> list[CorporateAction]:
        """Get only rights issues."""
        return [a for a in self.actions if a.is_rights]

    class Config:
        populate_by_name = True