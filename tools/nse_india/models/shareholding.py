"""Detailed shareholding pattern models for NSE India API."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from .announcement import parse_nse_date, parse_nse_datetime


class ShareholdingSummary(BaseModel):
    """Summary of shareholding pattern by category."""

    model_config = ConfigDict(str_strip_whitespace=True)

    category_code: str = Field(alias="COL_I")
    category_name: str = Field(alias="COL_II")
    num_shareholders: int = Field(alias="COL_III", default=0)
    num_shares_fully_paid: int = Field(alias="COL_IV", default=0)
    num_shares_partly_paid: int = Field(alias="COL_V", default=0)
    num_shares_underlying_dr: int = Field(alias="COL_VI", default=0)
    total_shares: int = Field(alias="COL_VII", default=0)
    shareholding_percentage: float = Field(alias="COL_VIII", default=0.0)
    voting_rights_total: int = Field(alias="COL_IX_Total", default=0)
    voting_rights_percentage: float = Field(alias="COL_IX_TotalABC", default=0.0)
    shares_underlying_outstanding: int = Field(alias="COL_X", default=0)
    shareholding_diluted_percentage: float = Field(alias="COL_XI", default=0.0)
    shares_locked_in: int = Field(alias="COL_XII_A", default=0)
    shares_pledged: int = Field(alias="COL_XIII_A", default=0)
    shares_in_demat: int = Field(alias="COL_XIV", default=0)

    @field_validator("num_shareholders", "num_shares_fully_paid", "num_shares_partly_paid",
                     "num_shares_underlying_dr", "total_shares", "voting_rights_total",
                     "shares_underlying_outstanding", "shares_locked_in", "shares_pledged",
                     "shares_in_demat", mode="before")
    @classmethod
    def parse_int(cls, v) -> int:
        if v is None or v == "" or v == "-":
            return 0
        if isinstance(v, int):
            return v
        try:
            return int(str(v).replace(",", ""))
        except ValueError:
            return 0

    @field_validator("shareholding_percentage", "voting_rights_percentage",
                     "shareholding_diluted_percentage", mode="before")
    @classmethod
    def parse_float(cls, v) -> float:
        if v is None or v == "" or v == "-":
            return 0.0
        if isinstance(v, (int, float)):
            return float(v)
        try:
            return float(str(v).replace(",", ""))
        except ValueError:
            return 0.0


class ShareholderDetail(BaseModel):
    """Individual shareholder details (promoter or public)."""

    model_config = ConfigDict(str_strip_whitespace=True)

    name: str = Field(alias="COL_I")
    category: str | None = Field(alias="category", default=None)
    entity_type: str | None = Field(alias="ENTITY_TYPE", default=None)
    num_shareholders: int = Field(alias="COL_III", default=0)
    num_shares_fully_paid: int = Field(alias="COL_IV", default=0)
    num_shares_partly_paid: int = Field(alias="COL_V", default=0)
    num_shares_underlying_dr: int = Field(alias="COL_VI", default=0)
    total_shares: int = Field(alias="COL_VII", default=0)
    shareholding_percentage: float = Field(alias="COL_VIII", default=0.0)
    voting_rights_total: int = Field(alias="COL_IX_Total", default=0)
    voting_rights_percentage: float = Field(alias="COL_IX_TotalABC", default=0.0)
    shares_underlying_outstanding: int = Field(alias="COL_X", default=0)
    shareholding_diluted_percentage: float = Field(alias="COL_XI", default=0.0)
    shares_locked_in: int = Field(alias="COL_XII_A", default=0)
    shares_pledged: int = Field(alias="COL_XIII_A", default=0)
    shares_in_demat: int = Field(alias="COL_XIV", default=0)

    @field_validator("num_shareholders", "num_shares_fully_paid", "num_shares_partly_paid",
                     "num_shares_underlying_dr", "total_shares", "voting_rights_total",
                     "shares_underlying_outstanding", "shares_locked_in", "shares_pledged",
                     "shares_in_demat", mode="before")
    @classmethod
    def parse_int(cls, v) -> int:
        if v is None or v == "" or v == "-":
            return 0
        if isinstance(v, int):
            return v
        try:
            return int(str(v).replace(",", ""))
        except ValueError:
            return 0

    @field_validator("shareholding_percentage", "voting_rights_percentage",
                     "shareholding_diluted_percentage", mode="before")
    @classmethod
    def parse_float(cls, v) -> float:
        if v is None or v == "" or v == "-":
            return 0.0
        if isinstance(v, (int, float)):
            return float(v)
        try:
            return float(str(v).replace(",", ""))
        except ValueError:
            return 0.0

    @field_validator("category", "entity_type", mode="before")
    @classmethod
    def clean_string(cls, v) -> str | None:
        if v is None or str(v).strip() in ["", "-", " "]:
            return None
        return str(v).strip()

    @property
    def is_individual(self) -> bool:
        """Check if this is an individual shareholder (not a category header)."""
        return self.entity_type is not None or (
            self.total_shares > 0 and self.category in [None, "", " "]
        )


class BeneficialOwner(BaseModel):
    """Significant Beneficial Owner (SBO) details."""

    model_config = ConfigDict(str_strip_whitespace=True)

    sr_no: str = Field(alias="srNo")
    sbo_name: str = Field(alias="ssName")
    sbo_nationality: str | None = Field(alias="ssNationality", default=None)
    sbo_pan: str | None = Field(alias="ssPan", default=None)
    registered_owner_name: str = Field(alias="ssrName")
    registered_owner_nationality: str | None = Field(alias="ssrNationality", default=None)
    registered_owner_pan: str | None = Field(alias="ssrPan", default=None)
    shareholding_percentage: float = Field(alias="ssrShare", default=0.0)
    voting_rights_percentage: float = Field(alias="ssrVotingRes", default=0.0)
    rights_percentage: float = Field(alias="ssrRights", default=0.0)
    has_executive_control: bool = Field(alias="ssrExecControl", default=False)
    has_significant_influence: bool = Field(alias="ssrExecSignInflu", default=False)
    acquisition_date: datetime | None = Field(alias="ssrCreationAcqDate", default=None)

    @field_validator("shareholding_percentage", "voting_rights_percentage",
                     "rights_percentage", mode="before")
    @classmethod
    def parse_float(cls, v) -> float:
        if v is None or v == "" or v == "-":
            return 0.0
        if isinstance(v, (int, float)):
            return float(v)
        try:
            return float(str(v).replace(",", ""))
        except ValueError:
            return 0.0

    @field_validator("has_executive_control", "has_significant_influence", mode="before")
    @classmethod
    def parse_bool(cls, v) -> bool:
        if v is None:
            return False
        if isinstance(v, bool):
            return v
        return str(v).lower() == "yes"

    @field_validator("acquisition_date", mode="before")
    @classmethod
    def parse_date(cls, v) -> datetime | None:
        if v is None or isinstance(v, datetime):
            return v
        return parse_nse_date(v)


class ShareholdingDeclaration(BaseModel):
    """Declaration items in shareholding pattern."""

    model_config = ConfigDict(str_strip_whitespace=True)

    particulars: str
    promoter_group: str | None = Field(alias="promoter_group", default=None)
    public: str | None = Field(alias="public", default=None)
    non_public: str | None = Field(alias="non_public", default=None)


class DetailedShareholdingPattern(BaseModel):
    """Complete detailed shareholding pattern for a quarter."""

    model_config = ConfigDict(str_strip_whitespace=True)

    # Metadata
    symbol: str
    company_name: str
    nds_id: str
    period_ended: datetime | None = None

    # Summary data
    summary: list[ShareholdingSummary] = Field(default_factory=list)

    # Promoter details
    promoter_indian: list[ShareholderDetail] = Field(default_factory=list)
    promoter_foreign: list[ShareholderDetail] = Field(default_factory=list)

    # Public shareholder details
    public_institutions: list[ShareholderDetail] = Field(default_factory=list)
    public_non_institutions: list[ShareholderDetail] = Field(default_factory=list)

    # Non-public shareholders
    non_public_shareholders: list[ShareholderDetail] = Field(default_factory=list)

    # Beneficial owners
    beneficial_owners: list[BeneficialOwner] = Field(default_factory=list)

    # Declarations
    declarations: list[ShareholdingDeclaration] = Field(default_factory=list)

    @property
    def promoter_total_percentage(self) -> float:
        """Get total promoter holding percentage."""
        for s in self.summary:
            if "promoter" in s.category_name.lower():
                return s.shareholding_percentage
        return 0.0

    @property
    def public_total_percentage(self) -> float:
        """Get total public holding percentage."""
        for s in self.summary:
            if s.category_name.lower() == "public":
                return s.shareholding_percentage
        return 0.0

    @property
    def top_promoters(self) -> list[ShareholderDetail]:
        """Get top promoter shareholders sorted by holding."""
        all_promoters = [
            p for p in self.promoter_indian + self.promoter_foreign
            if p.is_individual
        ]
        return sorted(all_promoters, key=lambda x: x.shareholding_percentage, reverse=True)

    @property
    def top_beneficial_owners(self) -> list[BeneficialOwner]:
        """Get top beneficial owners sorted by holding."""
        return sorted(
            [bo for bo in self.beneficial_owners if bo.shareholding_percentage > 0],
            key=lambda x: x.shareholding_percentage,
            reverse=True
        )
