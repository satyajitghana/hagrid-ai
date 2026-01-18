"""Data models for NSE India corporate announcements."""

import hashlib
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


def parse_nse_datetime(value: str) -> datetime | None:
    """Parse datetime strings from NSE India API.

    NSE uses multiple formats:
    - "18-Jan-2026 19:45:38" (broadcast/dissemination)
    - "2026-01-18 19:45:38" (receipt)
    - "18-JAN-2026 19:45:38" (debt - uppercase month)
    - "-" (missing value)
    """
    if not value or value.strip() == "" or value.strip() == "-":
        return None

    value = value.strip()

    # Try different formats
    formats = [
        "%d-%b-%Y %H:%M:%S",  # 18-Jan-2026 19:45:38
        "%d-%B-%Y %H:%M:%S",  # 18-January-2026 19:45:38
        "%Y-%m-%d %H:%M:%S",  # 2026-01-18 19:45:38
        "%d-%m-%Y %H:%M:%S",  # 18-01-2026 19:45:38
    ]

    for fmt in formats:
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            continue

    # If all formats fail, try with case-insensitive month
    try:
        # Handle uppercase months like "JAN"
        return datetime.strptime(value.title(), "%d-%b-%Y %H:%M:%S")
    except ValueError:
        pass

    raise ValueError(f"Unable to parse datetime: {value}")


class EquityAnnouncement(BaseModel):
    """Corporate announcement for equity securities."""

    model_config = ConfigDict(
        populate_by_name=True,
        str_strip_whitespace=True,
    )

    symbol: str = Field(alias="SYMBOL")
    company_name: str = Field(alias="COMPANY NAME")
    subject: str = Field(alias="SUBJECT")
    details: str = Field(alias="DETAILS")
    broadcast_datetime: datetime | None = Field(alias="BROADCAST DATE/TIME", default=None)
    receipt: datetime | None = Field(alias="RECEIPT", default=None)
    dissemination: datetime | None = Field(alias="DISSEMINATION", default=None)
    difference: str | None = Field(alias="DIFFERENCE", default=None)
    attachment_url: str | None = Field(alias="ATTACHMENT", default=None)

    @field_validator("broadcast_datetime", "receipt", "dissemination", mode="before")
    @classmethod
    def parse_datetime(cls, v: str | datetime | None) -> datetime | None:
        if v is None or isinstance(v, datetime):
            return v
        return parse_nse_datetime(v)

    @field_validator("attachment_url", mode="before")
    @classmethod
    def clean_attachment_url(cls, v: str | None) -> str | None:
        if v is None or v.strip() == "":
            return None
        return v.strip()

    @field_validator("difference", mode="before")
    @classmethod
    def clean_difference(cls, v: str | None) -> str | None:
        if v is None or v.strip() == "" or v.strip() == "-" or v.strip() == "::":
            return None
        return v.strip()

    @property
    def unique_id(self) -> str:
        """Generate unique ID for tracking processed announcements.

        Uses symbol + broadcast datetime + subject hash for uniqueness.
        """
        subject_hash = hashlib.md5(self.subject.encode()).hexdigest()[:8]
        if self.broadcast_datetime:
            dt_str = self.broadcast_datetime.strftime("%Y%m%d%H%M%S")
        else:
            # Fallback to subject hash only if no datetime
            dt_str = "00000000000000"
        return f"{self.symbol}_{dt_str}_{subject_hash}"

    @property
    def has_attachment(self) -> bool:
        """Check if announcement has a PDF attachment."""
        return self.attachment_url is not None and len(self.attachment_url) > 0


class DebtAnnouncement(BaseModel):
    """Corporate announcement for debt securities.

    Note: Debt announcements don't have a SYMBOL column.
    """

    model_config = ConfigDict(
        populate_by_name=True,
        str_strip_whitespace=True,
    )

    company_name: str = Field(alias="COMPANY NAME")
    subject: str = Field(alias="SUBJECT")
    details: str = Field(alias="DETAILS")
    broadcast_datetime: datetime | None = Field(alias="BROADCAST DATE/TIME", default=None)
    dissemination: datetime | None = Field(alias="DISSEMINATION", default=None)
    difference: str | None = Field(alias="DIFFERENCE", default=None)
    attachment_url: str | None = Field(alias="ATTACHMENT", default=None)

    @field_validator("broadcast_datetime", "dissemination", mode="before")
    @classmethod
    def parse_datetime(cls, v: str | datetime | None) -> datetime | None:
        if v is None or isinstance(v, datetime):
            return v
        return parse_nse_datetime(v)

    @field_validator("attachment_url", mode="before")
    @classmethod
    def clean_attachment_url(cls, v: str | None) -> str | None:
        if v is None or v.strip() == "":
            return None
        return v.strip()

    @field_validator("difference", mode="before")
    @classmethod
    def clean_difference(cls, v: str | None) -> str | None:
        if v is None or v.strip() == "" or v.strip() == "-" or v.strip() == "::":
            return None
        return v.strip()

    @property
    def unique_id(self) -> str:
        """Generate unique ID for tracking processed announcements.

        Uses company name + broadcast datetime + subject hash for uniqueness.
        """
        # Clean company name for ID
        clean_name = "".join(c for c in self.company_name if c.isalnum())[:20]
        subject_hash = hashlib.md5(self.subject.encode()).hexdigest()[:8]
        if self.broadcast_datetime:
            dt_str = self.broadcast_datetime.strftime("%Y%m%d%H%M%S")
        else:
            dt_str = "00000000000000"
        return f"{clean_name}_{dt_str}_{subject_hash}"

    @property
    def has_attachment(self) -> bool:
        """Check if announcement has a PDF attachment."""
        return self.attachment_url is not None and len(self.attachment_url) > 0


class AnnualReport(BaseModel):
    """Annual report data for a company."""

    model_config = ConfigDict(
        populate_by_name=True,
        str_strip_whitespace=True,
    )

    company_name: str = Field(alias="companyName")
    from_year: str = Field(alias="fromYr")
    to_year: str = Field(alias="toYr")
    submission_type: str | None = Field(alias="submission_type", default=None)
    broadcast_datetime: datetime | None = Field(alias="broadcast_dttm", default=None)
    dissemination_datetime: datetime | None = Field(alias="disseminationDateTime", default=None)
    time_taken: str | None = Field(alias="timeTaken", default=None)
    file_url: str = Field(alias="fileName")
    file_size: int | None = Field(alias="attFileSize", default=None)

    @field_validator("broadcast_datetime", "dissemination_datetime", mode="before")
    @classmethod
    def parse_datetime(cls, v: str | datetime | None) -> datetime | None:
        if v is None or v == "-" or v.strip() == "":
            return None
        if isinstance(v, datetime):
            return v
        return parse_nse_datetime(v)

    @field_validator("submission_type", "time_taken", mode="before")
    @classmethod
    def clean_optional_string(cls, v: str | None) -> str | None:
        if v is None or v == "-" or v == "::" or v.strip() == "":
            return None
        return v.strip()

    @property
    def unique_id(self) -> str:
        """Generate unique ID for tracking."""
        clean_name = "".join(c for c in self.company_name if c.isalnum())[:20]
        return f"{clean_name}_{self.from_year}_{self.to_year}"

    @property
    def financial_year(self) -> str:
        """Return the financial year string (e.g., '2024-2025')."""
        return f"{self.from_year}-{self.to_year}"

    @property
    def is_zip(self) -> bool:
        """Check if the file is a ZIP archive."""
        return self.file_url.lower().endswith(".zip")

    @property
    def is_pdf(self) -> bool:
        """Check if the file is a PDF."""
        return self.file_url.lower().endswith(".pdf")


def parse_nse_date(value: str) -> datetime | None:
    """Parse date strings from NSE India API (without time component).

    NSE uses formats like:
    - "30-SEP-2025" (shareholding pattern date)
    - "17-OCT-2025" (submission date)
    - "-" (missing value)
    """
    if not value or value.strip() == "" or value.strip() == "-":
        return None

    value = value.strip()

    # Try different formats
    formats = [
        "%d-%b-%Y",  # 30-Sep-2025
        "%d-%B-%Y",  # 30-September-2025
        "%Y-%m-%d",  # 2025-09-30
        "%d-%m-%Y",  # 30-09-2025
    ]

    for fmt in formats:
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            continue

    # Try with case-insensitive month (uppercase like "SEP")
    try:
        return datetime.strptime(value.title(), "%d-%b-%Y")
    except ValueError:
        pass

    return None


class ShareholdingPattern(BaseModel):
    """Shareholding pattern data for a company.

    Contains promoter vs public shareholding percentages for a quarter.
    """

    model_config = ConfigDict(
        populate_by_name=True,
        str_strip_whitespace=True,
    )

    symbol: str
    company_name: str = Field(alias="name")
    pattern_date: datetime | None = Field(alias="date", default=None)
    promoter_percentage: float | None = Field(alias="pr_and_prgrp", default=None)
    public_percentage: float | None = Field(alias="public_val", default=None)
    employee_trusts: float | None = Field(alias="employeeTrusts", default=None)
    xbrl_url: str | None = Field(alias="xbrl", default=None)
    xbrl_file_size: str | None = Field(alias="xbrlFileSize", default=None)
    record_id: str | None = Field(alias="recordId", default=None)
    submission_date: datetime | None = Field(alias="submissionDate", default=None)
    broadcast_datetime: datetime | None = Field(alias="broadcastDate", default=None)
    system_datetime: datetime | None = Field(alias="systemDate", default=None)
    time_difference: str | None = Field(alias="timeDifference", default=None)
    remarks: str | None = Field(alias="remarksWeb", default=None)
    is_revised: bool = Field(alias="revisedData", default=False)

    @field_validator("pattern_date", "submission_date", mode="before")
    @classmethod
    def parse_date(cls, v: str | datetime | None) -> datetime | None:
        if v is None or isinstance(v, datetime):
            return v
        return parse_nse_date(v)

    @field_validator("broadcast_datetime", "system_datetime", mode="before")
    @classmethod
    def parse_datetime(cls, v: str | datetime | None) -> datetime | None:
        if v is None or isinstance(v, datetime):
            return v
        return parse_nse_datetime(v)

    @field_validator("promoter_percentage", "public_percentage", "employee_trusts", mode="before")
    @classmethod
    def parse_percentage(cls, v: str | float | None) -> float | None:
        if v is None:
            return None
        if isinstance(v, (int, float)):
            return float(v)
        if isinstance(v, str):
            v = v.strip()
            if v == "" or v == "-":
                return None
            try:
                return float(v)
            except ValueError:
                return None
        return None

    @field_validator("is_revised", mode="before")
    @classmethod
    def parse_revised(cls, v: str | bool | None) -> bool:
        if v is None:
            return False
        if isinstance(v, bool):
            return v
        if isinstance(v, str):
            return v.upper() == "Y"
        return False

    @field_validator("time_difference", "remarks", "xbrl_url", "xbrl_file_size", mode="before")
    @classmethod
    def clean_optional_string(cls, v: str | None) -> str | None:
        if v is None:
            return None
        if isinstance(v, str):
            v = v.strip()
            if v == "" or v == "-" or v == "::":
                return None
            return v
        return str(v) if v else None

    @property
    def unique_id(self) -> str:
        """Generate unique ID for tracking."""
        date_str = self.pattern_date.strftime("%Y%m%d") if self.pattern_date else "00000000"
        return f"{self.symbol}_{date_str}_shp"

    @property
    def quarter(self) -> str | None:
        """Return the quarter string (e.g., 'Q2 FY25' for Sep 2024)."""
        if not self.pattern_date:
            return None
        month = self.pattern_date.month
        year = self.pattern_date.year
        if month in [1, 2, 3]:
            return f"Q4 FY{str(year)[2:]}"
        elif month in [4, 5, 6]:
            return f"Q1 FY{str(year + 1)[2:]}"
        elif month in [7, 8, 9]:
            return f"Q2 FY{str(year + 1)[2:]}"
        else:
            return f"Q3 FY{str(year + 1)[2:]}"


# Type alias for any announcement type
Announcement = EquityAnnouncement | DebtAnnouncement
