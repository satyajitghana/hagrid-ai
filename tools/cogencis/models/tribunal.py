"""Tribunal models for Cogencis API."""

from datetime import datetime
from pydantic import BaseModel, Field

from .common import PagingInfo, ColumnDefinition


class TribunalCase(BaseModel):
    """Individual tribunal case.
    
    Field mappings from API:
    - f_108: date (format: "DD MMM YY")
    - f_110: tribunal_name (EPFO/APTEL/NGT/NCLT/SAT/CESTAT/NCLAT)
    - f_111: tribunal_bench
    - f_112: order_type (Interim/Final)
    - f_113: case_type
    - f_114: case_title
    - f_116: link (URL to order document)
    """

    date: str = Field(alias="f_108")
    tribunal_name: str = Field(alias="f_110")
    tribunal_bench: str = Field(alias="f_111")
    order_type: str = Field(alias="f_112")
    case_type: str = Field(alias="f_113")
    case_title: str = Field(alias="f_114")
    link: str = Field(alias="f_116")

    @property
    def date_parsed(self) -> datetime | None:
        """Parse date string to datetime object."""
        try:
            # Format: "06 Nov 25" or "30 Oct 25"
            return datetime.strptime(self.date, "%d %b %y")
        except (ValueError, TypeError):
            return None

    @property
    def is_interim(self) -> bool:
        """Check if this is an interim order."""
        return self.order_type.lower() == "interim"

    @property
    def is_final(self) -> bool:
        """Check if this is a final order."""
        return self.order_type.lower() == "final"

    @property
    def is_nclt(self) -> bool:
        """Check if this is from NCLT."""
        return "nclt" in self.tribunal_name.lower()

    @property
    def is_nclat(self) -> bool:
        """Check if this is from NCLAT."""
        return "nclat" in self.tribunal_name.lower()

    @property
    def is_sat(self) -> bool:
        """Check if this is from SAT."""
        return "sat" in self.tribunal_name.lower()

    @property
    def is_ngt(self) -> bool:
        """Check if this is from NGT."""
        return "ngt" in self.tribunal_name.lower()

    @property
    def has_link(self) -> bool:
        """Check if order link is available."""
        return bool(self.link and self.link.strip())

    class Config:
        populate_by_name = True


class TribunalResponseData(BaseModel):
    """Paginated tribunal response data from API."""

    paging_info: PagingInfo = Field(alias="pagingInfo")
    columns: list[ColumnDefinition]
    data: list[TribunalCase]

    class Config:
        populate_by_name = True


class TribunalResponse(BaseModel):
    """Response model for tribunal API."""

    status: bool
    message: str
    response: TribunalResponseData | None = None

    @property
    def is_success(self) -> bool:
        """Check if the response indicates success."""
        return self.status is True

    @property
    def cases(self) -> list[TribunalCase]:
        """Get list of tribunal cases."""
        if self.response:
            return self.response.data
        return []

    @property
    def total_results(self) -> int:
        """Get total number of cases available."""
        if self.response:
            return self.response.paging_info.total_records
        return 0

    @property
    def interim_orders(self) -> list[TribunalCase]:
        """Get only interim orders."""
        return [c for c in self.cases if c.is_interim]

    @property
    def final_orders(self) -> list[TribunalCase]:
        """Get only final orders."""
        return [c for c in self.cases if c.is_final]

    class Config:
        populate_by_name = True