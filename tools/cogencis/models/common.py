"""Common response models for Cogencis API."""

from typing import Any, Generic, TypeVar
from pydantic import BaseModel, Field


class PagingInfo(BaseModel):
    """Pagination information from API responses.
    
    Note: Some API responses return null for pagination fields,
    so all fields are optional with sensible defaults.
    """

    total_records: int | None = Field(default=0, alias="totalRecords")
    page_no: int | None = Field(default=None, alias="pageNo")
    page_size: int | None = Field(default=None, alias="pageSize")
    record_count: int | None = Field(default=0, alias="recordCount")
    no_of_pages: int | None = Field(default=0, alias="noOfPages")

    class Config:
        populate_by_name = True


class ColumnDefinition(BaseModel):
    """Column definition for tabular data responses."""

    field: str
    action: str | None = None
    d_width: int | None = Field(default=None, alias="dWidth")
    format: str | None = None
    m_width: int | None = Field(default=None, alias="mWidth")
    data_type: str | None = Field(default=None, alias="dataType")
    display_name: str | None = Field(default=None, alias="displayName")

    class Config:
        populate_by_name = True


T = TypeVar("T")


class BaseResponse(BaseModel, Generic[T]):
    """Base response structure for all Cogencis API responses."""

    status: bool
    message: str
    response: T | None = None

    @property
    def is_success(self) -> bool:
        """Check if the response indicates success."""
        return self.status is True

    class Config:
        populate_by_name = True


class PaginatedData(BaseModel, Generic[T]):
    """Paginated data response structure."""

    paging_info: PagingInfo = Field(alias="pagingInfo")
    data: list[T]
    columns: list[ColumnDefinition] | None = None

    class Config:
        populate_by_name = True