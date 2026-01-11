"""SAST (Substantial Acquisition of Shares and Takeovers) models for Cogencis API."""

from datetime import datetime
from typing import Any
from pydantic import BaseModel, Field, field_validator

from .common import PagingInfo, ColumnDefinition


class SASTTransaction(BaseModel):
    """Individual SAST transaction data.
    
    Field mappings from API:
    - f_162: date (format: "DD-MMM-YY")
    - f_48: acquirer_name
    - f_57: transaction_type (Sale/Acquisition)
    - f_52: quantity
    - f_53: shares_post (shares after transaction)
    - f_58: acquisition_mode (Others/Interse transfer/Open Market)
    - f_59: acquisition_type (Equity shares)
    - f_25008: path
    """

    date: str = Field(alias="f_162")
    acquirer_name: str = Field(alias="f_48")
    transaction_type: str = Field(alias="f_57")
    quantity: int = Field(alias="f_52")
    shares_post: int = Field(alias="f_53")
    acquisition_mode: str = Field(alias="f_58")
    acquisition_type: str = Field(alias="f_59")
    path: str = Field(alias="f_25008")

    @field_validator("quantity", "shares_post", mode="before")
    @classmethod
    def parse_quantity(cls, v: Any) -> int:
        """Parse quantity which may come as string or int."""
        if v is None:
            return 0
        if isinstance(v, str):
            return int(v.replace(",", ""))
        return int(v)

    @property
    def is_acquisition(self) -> bool:
        """Check if this is an acquisition."""
        return self.transaction_type.lower() == "acquisition"

    @property
    def is_sale(self) -> bool:
        """Check if this is a sale."""
        return self.transaction_type.lower() == "sale"

    @property
    def date_parsed(self) -> datetime | None:
        """Parse date string to datetime object."""
        try:
            # Format: "01-Apr-24" or "25-Aug-23"
            return datetime.strptime(self.date, "%d-%b-%y")
        except (ValueError, TypeError):
            return None

    class Config:
        populate_by_name = True


class SASTResponseData(BaseModel):
    """Paginated SAST response data from API."""

    paging_info: PagingInfo = Field(alias="pagingInfo")
    columns: list[ColumnDefinition]
    data: list[SASTTransaction]

    class Config:
        populate_by_name = True


class SASTResponse(BaseModel):
    """Response model for SAST API."""

    status: bool
    message: str
    response: SASTResponseData | None = None

    @property
    def is_success(self) -> bool:
        """Check if the response indicates success."""
        return self.status is True

    @property
    def transactions(self) -> list[SASTTransaction]:
        """Get list of SAST transactions."""
        if self.response:
            return self.response.data
        return []

    @property
    def total_results(self) -> int:
        """Get total number of transactions available."""
        if self.response:
            return self.response.paging_info.total_records
        return 0

    @property
    def acquisitions(self) -> list[SASTTransaction]:
        """Get only acquisition transactions."""
        return [t for t in self.transactions if t.is_acquisition]

    @property
    def sales(self) -> list[SASTTransaction]:
        """Get only sale transactions."""
        return [t for t in self.transactions if t.is_sale]

    class Config:
        populate_by_name = True