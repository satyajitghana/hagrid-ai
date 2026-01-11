"""Key shareholder models for Cogencis API."""

from typing import Any
from pydantic import BaseModel, Field

from .common import PagingInfo, ColumnDefinition


class ShareholdingValue(BaseModel):
    """Shareholding value for a specific period."""

    percentage: float = Field(alias="per")
    value: int = Field(alias="val")

    class Config:
        populate_by_name = True


class KeyShareholder(BaseModel):
    """Key shareholder data with historical shareholding patterns.
    
    Represents a single shareholder (promoter/public) with their
    shareholding percentages and values across multiple periods.
    """

    id: int
    parent_id: int | None
    is_expanded: bool
    description: str
    holdings: dict[str, ShareholdingValue | None]  # period -> holding value

    @classmethod
    def from_raw_row(cls, row: list[Any], periods: list[str]) -> "KeyShareholder":
        """
        Parse a raw row from API response.
        
        The row format is:
        [ID, ParentID, IsExpanded, Description, Sep-25, Jun-25, ...]
        
        Where each period value is either null or {"per": float, "val": int}
        """
        holdings = {}
        for i, period in enumerate(periods):
            # Period values start at index 4
            idx = i + 4
            if idx < len(row):
                val = row[idx]
                if val is not None and isinstance(val, dict):
                    holdings[period] = ShareholdingValue.model_validate(val)
                else:
                    holdings[period] = None
        
        return cls(
            id=row[0],
            parent_id=row[1],
            is_expanded=row[2] if isinstance(row[2], bool) else False,
            description=row[3] or "",
            holdings=holdings,
        )

    @property
    def is_group(self) -> bool:
        """Check if this is a group header (Promoter/Public)."""
        return self.parent_id is None

    @property
    def is_promoter(self) -> bool:
        """Check if this shareholder is part of promoter group."""
        # Parent ID 501 is Promoter group
        return self.parent_id == 501 or self.id == 501

    @property
    def is_public(self) -> bool:
        """Check if this shareholder is part of public group."""
        # Parent ID 502 is Public group
        return self.parent_id == 502 or self.id == 502

    def get_latest_holding(self) -> ShareholdingValue | None:
        """Get the most recent non-null shareholding value."""
        for val in self.holdings.values():
            if val is not None:
                return val
        return None

    def get_holding(self, period: str) -> ShareholdingValue | None:
        """Get shareholding for a specific period."""
        return self.holdings.get(period)


class KeyShareholderResponseData(BaseModel):
    """Raw key shareholder response data from API."""

    paging_info: PagingInfo = Field(alias="pagingInfo")
    columns: list[ColumnDefinition]
    data: list[list[Any]]

    class Config:
        populate_by_name = True

    def get_periods(self) -> list[str]:
        """
        Extract period headers from the first row of data.
        
        First row format: ["ID", "ParentID", "IsExpanded", "Description", "Sep-25", "Jun-25", ...]
        """
        if not self.data or len(self.data) < 1:
            return []
        
        header_row = self.data[0]
        # Periods start from index 4 onwards
        return [str(p) for p in header_row[4:] if p is not None]

    def get_shareholders(self) -> list[KeyShareholder]:
        """Parse all shareholder data from the response."""
        if len(self.data) < 2:
            return []
        
        periods = self.get_periods()
        shareholders = []
        
        # Skip the header row (index 0)
        for row in self.data[1:]:
            if row and len(row) >= 4:
                shareholders.append(KeyShareholder.from_raw_row(row, periods))
        
        return shareholders


class KeyShareholderResponse(BaseModel):
    """Response model for key shareholders API."""

    status: bool
    message: str
    response: KeyShareholderResponseData | None = None

    @property
    def is_success(self) -> bool:
        """Check if the response indicates success."""
        return self.status is True

    @property
    def shareholders(self) -> list[KeyShareholder]:
        """Get parsed list of shareholders."""
        if self.response:
            return self.response.get_shareholders()
        return []

    @property
    def periods(self) -> list[str]:
        """Get list of available periods."""
        if self.response:
            return self.response.get_periods()
        return []

    @property
    def promoters(self) -> list[KeyShareholder]:
        """Get only promoter shareholders (excludes group header)."""
        return [s for s in self.shareholders if s.is_promoter and not s.is_group]

    @property
    def public_shareholders(self) -> list[KeyShareholder]:
        """Get only public shareholders (excludes group header)."""
        return [s for s in self.shareholders if s.is_public and not s.is_group]

    class Config:
        populate_by_name = True