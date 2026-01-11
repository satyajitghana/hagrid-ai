"""News models for Cogencis API."""

from datetime import datetime
from pydantic import BaseModel, Field, field_validator

from .common import PagingInfo, ColumnDefinition


class NewsStory(BaseModel):
    """Individual news story from Cogencis API."""

    headline: str
    synopsis: str = ""
    categories: str = ""
    isins: str = ""
    cins: str = ""
    sections: str = ""
    source_link: str = Field(alias="sourceLink")
    thumbnail_image: str = Field(default="", alias="thumbNailImage")
    is_web_news: bool = Field(default=False, alias="isWebNews")
    source: str = ""
    source_date_time: str | None = Field(default=None, alias="sourceDateTime")
    status: str = ""
    entered_date_time: str | None = Field(default=None, alias="enteredDateTime")
    schedule: str | None = None
    sub_sections: str = Field(default="", alias="subSections")
    views: int = 0
    isin_array: list[str] = Field(default_factory=list, alias="isinArray")
    source_name: str = Field(default="", alias="sourceName")
    id: str = ""

    @property
    def source_datetime_parsed(self) -> datetime | None:
        """Parse source datetime string to datetime object."""
        if not self.source_date_time:
            return None
        try:
            # Format: "2026-01-07T07:20:00.000000+0530"
            # Need to handle the timezone format
            dt_str = self.source_date_time
            # Remove microseconds for easier parsing
            if "." in dt_str:
                dt_str = dt_str.split(".")[0]
            return datetime.fromisoformat(dt_str)
        except (ValueError, TypeError):
            return None

    @property
    def isin_list(self) -> list[str]:
        """Parse ISINs string into a list of individual ISINs."""
        if not self.isins:
            return []
        # ISINs are separated by commas, and each group may have multiple identifiers
        # e.g., "INE002A01018 RELINDUS.BS 532611.BS RELINDUS.NS"
        isin_groups = self.isins.split(",")
        unique_isins = set()
        for group in isin_groups:
            # Extract just the ISIN (starts with INE or IN)
            for part in group.strip().split():
                if part.startswith("INE") or part.startswith("IN"):
                    unique_isins.add(part)
        return list(unique_isins)

    @property
    def sections_list(self) -> list[str]:
        """Parse sections into a list."""
        if not self.sections:
            return []
        return [s.strip() for s in self.sections.split("|")]

    @property
    def sub_sections_list(self) -> list[str]:
        """Parse sub-sections into a list."""
        if not self.sub_sections:
            return []
        return [s.strip() for s in self.sub_sections.split("|")]

    class Config:
        populate_by_name = True


class NewsResponseData(BaseModel):
    """Paginated news response data from API."""

    paging_info: PagingInfo = Field(alias="pagingInfo")
    columns: list[ColumnDefinition]
    data: list[NewsStory]

    class Config:
        populate_by_name = True


class NewsResponse(BaseModel):
    """Response model for news API."""

    status: bool
    message: str
    response: NewsResponseData | None = None

    @property
    def is_success(self) -> bool:
        """Check if the response indicates success."""
        return self.status is True

    @property
    def stories(self) -> list[NewsStory]:
        """Get list of news stories."""
        if self.response:
            return self.response.data
        return []

    @property
    def total_results(self) -> int:
        """Get total number of news stories available."""
        if self.response:
            return self.response.paging_info.total_records
        return 0

    @property
    def total_pages(self) -> int:
        """Get total number of pages available."""
        if self.response:
            return self.response.paging_info.no_of_pages
        return 0

    class Config:
        populate_by_name = True