"""Announcement models for Cogencis API."""

from datetime import datetime
from typing import Any
from pydantic import BaseModel, Field

from .common import PagingInfo, ColumnDefinition


class Announcement(BaseModel):
    """Individual company announcement.
    
    Field mappings from API:
    - f_156: datetime (ISO format)
    - f_158: details (announcement type/description)
    - f_159: pdf_link (link to PDF document)
    - f_25008: path
    """

    datetime_str: str = Field(alias="f_156")
    details: str = Field(alias="f_158")
    pdf_link: str = Field(alias="f_159")
    path: str = Field(alias="f_25008")

    @property
    def datetime_parsed(self) -> datetime | None:
        """Parse datetime string to datetime object."""
        try:
            # Format: "2025-12-04T20:47:05"
            return datetime.fromisoformat(self.datetime_str)
        except (ValueError, TypeError):
            return None

    @property
    def announcement_type(self) -> str:
        """Get the type of announcement from details."""
        return self.details

    @property
    def is_board_meeting(self) -> bool:
        """Check if this is a board meeting related announcement."""
        return "board meeting" in self.details.lower()

    @property
    def is_credit_rating(self) -> bool:
        """Check if this is a credit rating announcement."""
        return "credit rating" in self.details.lower()

    @property
    def is_dividend(self) -> bool:
        """Check if this is dividend related."""
        return "dividend" in self.details.lower()

    @property
    def is_result(self) -> bool:
        """Check if this is a financial result announcement."""
        return "result" in self.details.lower() or "outcome" in self.details.lower()

    @property
    def is_investor_presentation(self) -> bool:
        """Check if this is an investor presentation."""
        return "investor presentation" in self.details.lower()

    @property
    def has_pdf(self) -> bool:
        """Check if PDF link is available."""
        return bool(self.pdf_link and self.pdf_link.strip())

    class Config:
        populate_by_name = True


class AnnouncementResponseData(BaseModel):
    """Paginated announcement response data from API."""

    paging_info: PagingInfo = Field(alias="pagingInfo")
    columns: list[ColumnDefinition]
    data: list[Announcement]

    class Config:
        populate_by_name = True


class AnnouncementResponse(BaseModel):
    """Response model for announcements API."""

    status: bool
    message: str
    response: AnnouncementResponseData | None = None

    @property
    def is_success(self) -> bool:
        """Check if the response indicates success."""
        return self.status is True

    @property
    def announcements(self) -> list[Announcement]:
        """Get list of announcements."""
        if self.response:
            return self.response.data
        return []

    @property
    def total_results(self) -> int:
        """Get total number of announcements available."""
        if self.response:
            return self.response.paging_info.total_records
        return 0

    @property
    def total_pages(self) -> int:
        """Get total number of pages."""
        if self.response:
            return self.response.paging_info.no_of_pages
        return 0

    class Config:
        populate_by_name = True