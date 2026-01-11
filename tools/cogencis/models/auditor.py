"""Auditor models for Cogencis API."""

from datetime import datetime
from pydantic import BaseModel, Field, field_validator

from .common import PagingInfo, ColumnDefinition


class AuditorData(BaseModel):
    """Parsed auditor data from API response.
    
    The API returns auditor data in a tabular format with:
    - f_120: appointment_date (format: "DD MMM YYYY")
    - f_121: auditor_personnel (name of the auditor)
    """

    appointment_date: str
    auditor_personnel: str

    @classmethod
    def from_raw_data(cls, data: list[str]) -> "AuditorData":
        """
        Parse auditor data from raw API response format.
        
        The API returns data as a list of lists where:
        - First list is field names: ["f_120", "f_121"]
        - Second list is values: ["01 Apr 2021", "T P Ostwal"]
        """
        if len(data) >= 2:
            return cls(
                appointment_date=data[0] if len(data) > 0 else "",
                auditor_personnel=data[1] if len(data) > 1 else "",
            )
        return cls(appointment_date="", auditor_personnel="")

    @property
    def appointment_datetime(self) -> datetime | None:
        """Parse appointment date string to datetime object."""
        try:
            return datetime.strptime(self.appointment_date, "%d %b %Y")
        except (ValueError, TypeError):
            return None


class AuditorResponseData(BaseModel):
    """Raw auditor response data from API."""

    paging_info: PagingInfo = Field(alias="pagingInfo")
    columns: list[ColumnDefinition]
    data: list[list[str]]

    class Config:
        populate_by_name = True

    def get_auditors(self) -> list[AuditorData]:
        """
        Parse the raw data into AuditorData objects.
        
        The data comes as:
        [["f_120", "f_121"], ["01 Apr 2021", "T P Ostwal"]]
        
        First element contains field names, subsequent elements contain data.
        """
        if len(self.data) < 2:
            return []
        
        # Skip the first row (field names) and parse the rest
        auditors = []
        for row in self.data[1:]:
            auditors.append(AuditorData.from_raw_data(row))
        return auditors


class AuditorResponse(BaseModel):
    """Response model for auditor API."""

    status: bool
    message: str
    response: AuditorResponseData | None = None

    @property
    def is_success(self) -> bool:
        """Check if the response indicates success."""
        return self.status is True

    @property
    def auditors(self) -> list[AuditorData]:
        """Get parsed list of auditors."""
        if self.response:
            return self.response.get_auditors()
        return []

    class Config:
        populate_by_name = True