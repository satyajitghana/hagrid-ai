"""Data models for NSE India insider trading (PIT) data."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


def parse_pit_datetime(value: str) -> datetime | None:
    """Parse datetime strings from PIT API.

    Formats:
    - "10-Dec-2025 17:27:46"
    - "17-Jan-2026 21:36"
    """
    if not value or value.strip() == "" or value.strip() == "-":
        return None

    value = value.strip()

    formats = [
        "%d-%b-%Y %H:%M:%S",  # 10-Dec-2025 17:27:46
        "%d-%b-%Y %H:%M",  # 17-Jan-2026 21:36
        "%d-%B-%Y %H:%M:%S",
        "%d-%B-%Y %H:%M",
    ]

    for fmt in formats:
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            continue

    # Try with case normalization
    try:
        return datetime.strptime(value.title(), "%d-%b-%Y %H:%M:%S")
    except ValueError:
        pass

    try:
        return datetime.strptime(value.title(), "%d-%b-%Y %H:%M")
    except ValueError:
        pass

    raise ValueError(f"Unable to parse datetime: {value}")


class InsiderTradingPlan(BaseModel):
    """Insider trading plan disclosure.

    These are pre-announced trading plans submitted by company insiders
    under SEBI's Prohibition of Insider Trading regulations.
    """

    model_config = ConfigDict(
        populate_by_name=True,
        str_strip_whitespace=True,
    )

    app_id: str = Field(alias="appid", description="Application ID")
    symbol: str = Field(description="Stock symbol")
    company_name: str = Field(alias="smName", description="Company name")
    submission_date: datetime | None = Field(
        alias="submissionDate", description="Date when plan was submitted"
    )
    ixbrl_url: str | None = Field(
        alias="ixbrl", description="URL to iXBRL document"
    )
    attachment_url: str | None = Field(
        alias="attachment", description="URL to XML attachment"
    )
    system_time: datetime | None = Field(
        alias="systym", description="System timestamp"
    )
    processing_diff: str | None = Field(
        alias="diff", description="Processing time difference"
    )
    xbrl_file_size: str | None = Field(
        alias="xbrlFileSize", description="Size of XBRL file"
    )
    ixbrl_file_size: str | None = Field(
        alias="ixbrlFileSize", description="Size of iXBRL file"
    )

    @field_validator("submission_date", "system_time", mode="before")
    @classmethod
    def parse_datetime(cls, v: str | datetime | None) -> datetime | None:
        if v is None or isinstance(v, datetime):
            return v
        return parse_pit_datetime(v)


class InsiderTransaction(BaseModel):
    """Individual insider transaction record.

    Records buy/sell transactions by company insiders (promoters, directors,
    key managerial personnel, designated employees).
    """

    model_config = ConfigDict(
        populate_by_name=True,
        str_strip_whitespace=True,
    )

    symbol: str = Field(description="Stock symbol")
    company: str = Field(description="Company name")
    annexure: str = Field(alias="anex", description="Annexure type (e.g., '7(2)')")
    acquirer_name: str = Field(alias="acqName", description="Name of the acquirer/disposer")
    disclosure_date: datetime | None = Field(alias="date", description="Disclosure date")
    pid: str = Field(description="Process ID")
    transaction_type: str = Field(
        alias="tdpTransactionType", description="Transaction type (Buy/Sell)"
    )
    security_type: str = Field(alias="secType", description="Type of security")
    securities_acquired: str = Field(
        alias="secAcq", description="Number of securities acquired/disposed"
    )
    security_value: str = Field(alias="secVal", description="Value of securities")
    person_category: str = Field(
        alias="personCategory",
        description="Category (Promoters, Director, KMP, etc.)"
    )

    # Before acquisition
    before_shares: str = Field(
        alias="befAcqSharesNo", description="Shares held before transaction"
    )
    before_percentage: str = Field(
        alias="befAcqSharesPer", description="Percentage held before"
    )

    # After acquisition
    after_shares: str = Field(
        alias="afterAcqSharesNo", description="Shares held after transaction"
    )
    after_percentage: str = Field(
        alias="afterAcqSharesPer", description="Percentage held after"
    )

    # Transaction dates
    acquisition_from_date: str = Field(
        alias="acqfromDt", description="Transaction start date"
    )
    acquisition_to_date: str = Field(
        alias="acqtoDt", description="Transaction end date"
    )
    intimation_date: str = Field(
        alias="intimDt", description="Intimation date"
    )

    # Other details
    acquisition_mode: str = Field(
        alias="acqMode", description="Mode (Market Sale, Market Purchase, etc.)"
    )
    exchange: str = Field(description="Exchange (NSE/BSE)")
    xbrl_url: str | None = Field(alias="xbrl", default=None, description="URL to XBRL document")
    remarks: str | None = Field(default=None, description="Additional remarks")

    @field_validator("disclosure_date", mode="before")
    @classmethod
    def parse_datetime(cls, v: str | datetime | None) -> datetime | None:
        if v is None or isinstance(v, datetime):
            return v
        return parse_pit_datetime(v)

    @property
    def is_buy(self) -> bool:
        """Check if this is a buy transaction."""
        return self.transaction_type.lower() == "buy"

    @property
    def is_sell(self) -> bool:
        """Check if this is a sell transaction."""
        return self.transaction_type.lower() == "sell"

    @property
    def is_promoter(self) -> bool:
        """Check if the acquirer is a promoter."""
        return "promoter" in self.person_category.lower()

    @property
    def is_director(self) -> bool:
        """Check if the acquirer is a director."""
        return "director" in self.person_category.lower()

    @property
    def shares_count(self) -> int:
        """Get the number of shares as integer."""
        try:
            return int(self.securities_acquired.replace(",", ""))
        except (ValueError, AttributeError):
            return 0

    @property
    def value_amount(self) -> float:
        """Get the transaction value as float."""
        try:
            return float(self.security_value.replace(",", ""))
        except (ValueError, AttributeError):
            return 0.0


class InsiderTransactionResponse(BaseModel):
    """Response from the corporates-pit API."""

    model_config = ConfigDict(
        populate_by_name=True,
        str_strip_whitespace=True,
    )

    acquirer_names: list[str] = Field(
        alias="acqNameList", default_factory=list,
        description="List of all acquirer/disposer names"
    )
    transactions: list[InsiderTransaction] = Field(
        alias="data", default_factory=list,
        description="List of insider transactions"
    )

    @property
    def total_transactions(self) -> int:
        """Get total number of transactions."""
        return len(self.transactions)

    @property
    def buy_transactions(self) -> list[InsiderTransaction]:
        """Get only buy transactions."""
        return [t for t in self.transactions if t.is_buy]

    @property
    def sell_transactions(self) -> list[InsiderTransaction]:
        """Get only sell transactions."""
        return [t for t in self.transactions if t.is_sell]

    @property
    def promoter_transactions(self) -> list[InsiderTransaction]:
        """Get only promoter transactions."""
        return [t for t in self.transactions if t.is_promoter]

    @property
    def director_transactions(self) -> list[InsiderTransaction]:
        """Get only director transactions."""
        return [t for t in self.transactions if t.is_director]
