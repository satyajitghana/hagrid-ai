"""Capital history models for Cogencis API."""

from datetime import datetime
from typing import Any
from pydantic import BaseModel, Field, field_validator

from .common import PagingInfo, ColumnDefinition


class CapitalHistoryEntry(BaseModel):
    """Individual capital history entry.
    
    Field mappings from API:
    - f_139: date (format: "DD MMM YY")
    - f_140: type (SHP/ESOP/Bonus/Rights/Forfeiture of Shares/etc.)
    - f_141: current_shares (no. of shares current)
    - f_142: face_value_old
    - f_143: face_value_new
    - f_144: change_in_shares
    - f_145: outstanding_shares
    """

    date: str = Field(alias="f_139")
    event_type: str = Field(alias="f_140")
    current_shares: float | None = Field(default=None, alias="f_141")
    face_value_old: float | None = Field(default=None, alias="f_142")
    face_value_new: float | None = Field(default=None, alias="f_143")
    change_in_shares: float | None = Field(default=None, alias="f_144")
    outstanding_shares: float | None = Field(default=None, alias="f_145")

    @field_validator(
        "current_shares", "face_value_old", "face_value_new",
        "change_in_shares", "outstanding_shares", mode="before"
    )
    @classmethod
    def parse_float(cls, v: Any) -> float | None:
        """Parse numeric values which may come as string or be null."""
        if v is None:
            return None
        if isinstance(v, str):
            try:
                return float(v.replace(",", ""))
            except ValueError:
                return None
        return float(v)

    @property
    def date_parsed(self) -> datetime | None:
        """Parse date string to datetime object."""
        try:
            # Format: "20 Oct 25" or "30 Apr 25"
            return datetime.strptime(self.date, "%d %b %y")
        except (ValueError, TypeError):
            return None

    @property
    def is_bonus(self) -> bool:
        """Check if this is a bonus issue."""
        return self.event_type.lower() == "bonus"

    @property
    def is_split(self) -> bool:
        """Check if this is a stock split."""
        return "split" in self.event_type.lower()

    @property
    def is_esop(self) -> bool:
        """Check if this is ESOP allotment."""
        return self.event_type.lower() == "esop"

    @property
    def is_rights(self) -> bool:
        """Check if this is a rights issue."""
        return self.event_type.lower() == "rights"

    class Config:
        populate_by_name = True


class CapitalHistoryResponseData(BaseModel):
    """Paginated capital history response data from API."""

    paging_info: PagingInfo = Field(alias="pagingInfo")
    columns: list[ColumnDefinition]
    data: list[CapitalHistoryEntry]

    class Config:
        populate_by_name = True


class CapitalHistoryResponse(BaseModel):
    """Response model for capital history API."""

    status: bool
    message: str
    response: CapitalHistoryResponseData | None = None

    @property
    def is_success(self) -> bool:
        """Check if the response indicates success."""
        return self.status is True

    @property
    def entries(self) -> list[CapitalHistoryEntry]:
        """Get list of capital history entries."""
        if self.response:
            return self.response.data
        return []

    @property
    def total_results(self) -> int:
        """Get total number of entries available."""
        if self.response:
            return self.response.paging_info.total_records
        return 0

    @property
    def bonus_issues(self) -> list[CapitalHistoryEntry]:
        """Get only bonus issue entries."""
        return [e for e in self.entries if e.is_bonus]

    @property
    def rights_issues(self) -> list[CapitalHistoryEntry]:
        """Get only rights issue entries."""
        return [e for e in self.entries if e.is_rights]

    class Config:
        populate_by_name = True