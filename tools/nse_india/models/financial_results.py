"""Data models for NSE India corporate financial results."""

from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

from .announcement import parse_nse_date


class FinancialResult(BaseModel):
    """Corporate financial result from NSE India.

    This represents quarterly/annual financial results filed by companies,
    including both consolidated and non-consolidated reports.
    """

    model_config = ConfigDict(
        populate_by_name=True,
        str_strip_whitespace=True,
    )

    symbol: str = Field(description="Stock symbol")
    company_name: str = Field(alias="companyName", description="Company name")
    industry: str = Field(description="Industry sector")
    audited: str = Field(description="Audit status (Audited/Un-Audited)")
    cumulative: str = Field(description="Cumulative status (Cumulative/Non-cumulative)")
    ind_as: str = Field(alias="indAs", description="Ind-AS reporting format")
    re_ind: str = Field(alias="reInd", description="Re-submission indicator")
    period: str = Field(description="Result period (Quarterly/Annual)")
    relating_to: str = Field(
        alias="relatingTo", description="Quarter/period (e.g., First Quarter, Fourth Quarter)"
    )
    financial_year: str = Field(
        alias="financialYear", description="Financial year range (e.g., 01-Apr-2024 To 31-Mar-2025)"
    )
    filing_date: datetime = Field(alias="filingDate", description="Date and time of filing")
    seq_number: str = Field(alias="seqNumber", description="Sequence number for the record")
    bank: str = Field(description="Bank indicator (Y/N)")
    from_date: date = Field(alias="fromDate", description="Period start date")
    to_date: date = Field(alias="toDate", description="Period end date")
    old_new_flag: str = Field(alias="oldNewFlag", description="Old/New format flag")
    xbrl_url: str | None = Field(alias="xbrl", default=None, description="URL to XBRL file")
    format: str = Field(description="Result format (Old/New)")
    params: str = Field(description="Internal parameter string")
    result_description: str | None = Field(
        alias="resultDescription", default=None, description="Description of result"
    )
    result_detailed_data_link: str | None = Field(
        alias="resultDetailedDataLink", default=None, description="Link to detailed data"
    )
    exchange_dissemination_time: str = Field(
        alias="exchdisstime", description="Exchange dissemination time"
    )
    difference: str = Field(description="Time difference between filing and dissemination")
    broadcast_date: str = Field(alias="broadCastDate", description="Broadcast date and time")
    consolidated: str = Field(
        description="Report type (Consolidated/Non-Consolidated)"
    )
    isin: str = Field(description="ISIN code")

    @field_validator("filing_date", mode="before")
    @classmethod
    def parse_filing_date(cls, v: str | datetime | None) -> datetime | None:
        """Parse filing date in DD-Mon-YYYY HH:MM format."""
        if v is None:
            return None
        if isinstance(v, datetime):
            return v

        # Parse format like "16-Jan-2025 20:20"
        try:
            return datetime.strptime(v, "%d-%b-%Y %H:%M")
        except ValueError:
            # Try other formats
            for fmt in ["%d-%B-%Y %H:%M", "%d-%m-%Y %H:%M", "%Y-%m-%d %H:%M"]:
                try:
                    return datetime.strptime(v, fmt)
                except ValueError:
                    continue
            raise ValueError(f"Unable to parse filing date: {v}")

    @field_validator("from_date", "to_date", mode="before")
    @classmethod
    def parse_date(cls, v: str | date | None) -> date | None:
        """Parse date in DD-Mon-YYYY format."""
        if v is None:
            return None
        if isinstance(v, date):
            return v

        # Parse format like "01-Oct-2024"
        try:
            return datetime.strptime(v, "%d-%b-%Y").date()
        except ValueError:
            # Try other formats
            for fmt in ["%d-%B-%Y", "%Y-%m-%d", "%d-%m-%Y"]:
                try:
                    return datetime.strptime(v, fmt).date()
                except ValueError:
                    continue
            raise ValueError(f"Unable to parse date: {v}")

    @property
    def is_consolidated(self) -> bool:
        """Check if this is a consolidated report."""
        return "consolidated" in self.consolidated.lower() and "non" not in self.consolidated.lower()

    @property
    def is_audited(self) -> bool:
        """Check if this result is audited."""
        return self.audited.lower() == "audited"

    @property
    def is_quarterly(self) -> bool:
        """Check if this is a quarterly result."""
        return self.period.lower() == "quarterly"

    @property
    def is_annual(self) -> bool:
        """Check if this is an annual result."""
        return self.period.lower() == "annual"

    @property
    def quarter(self) -> str | None:
        """Get the quarter (Q1, Q2, Q3, Q4) if quarterly result."""
        if not self.is_quarterly:
            return None
        relating = self.relating_to.lower()
        if "first" in relating:
            return "Q1"
        elif "second" in relating:
            return "Q2"
        elif "third" in relating:
            return "Q3"
        elif "fourth" in relating:
            return "Q4"
        return None

    @property
    def has_xbrl(self) -> bool:
        """Check if XBRL data is available."""
        return bool(self.xbrl_url)

    @property
    def fy_start_year(self) -> int | None:
        """Extract the starting year of the financial year."""
        try:
            # Parse "01-Apr-2024 To 31-Mar-2025"
            parts = self.financial_year.split(" To ")
            if parts:
                start_date = datetime.strptime(parts[0].strip(), "%d-%b-%Y")
                return start_date.year
        except (ValueError, IndexError):
            pass
        return None

    @property
    def fy_end_year(self) -> int | None:
        """Extract the ending year of the financial year."""
        try:
            # Parse "01-Apr-2024 To 31-Mar-2025"
            parts = self.financial_year.split(" To ")
            if len(parts) > 1:
                end_date = datetime.strptime(parts[1].strip(), "%d-%b-%Y")
                return end_date.year
        except (ValueError, IndexError):
            pass
        return None


def _parse_lakhs(v: Any) -> float | None:
    """Parse a value in lakhs (₹00,000) from NSE API."""
    if v is None:
        return None
    if isinstance(v, (int, float)):
        return float(v)
    if isinstance(v, str):
        v = v.strip()
        if v == "" or v == "-" or v == "null":
            return None
        try:
            return float(v.replace(",", ""))
        except ValueError:
            return None
    return None


def _parse_ratio(v: Any) -> float | None:
    """Parse a ratio/percentage value from NSE API."""
    if v is None:
        return None
    if isinstance(v, (int, float)):
        return float(v)
    if isinstance(v, str):
        v = v.strip()
        if v == "" or v == "-" or v == "null":
            return None
        try:
            return float(v.replace(",", "").replace("%", ""))
        except ValueError:
            return None
    return None


class FinancialResultPeriodData(BaseModel):
    """Financial data for a single period (quarter/year) from comparison API.

    All monetary values are in ₹ Lakhs (1 Lakh = ₹1,00,000).
    """

    model_config = ConfigDict(
        populate_by_name=True,
        str_strip_whitespace=True,
    )

    # Period information
    from_date: date | None = Field(alias="re_from_dt", default=None)
    to_date: date | None = Field(alias="re_to_dt", default=None)
    filing_date: date | None = Field(alias="re_create_dt", default=None)
    result_type: str | None = Field(alias="re_res_type", default=None)  # A=Audited, U=Unaudited
    seq_number: str | None = Field(alias="re_seq_num", default=None)

    # Revenue & Income (in Lakhs)
    net_sales: float | None = Field(alias="re_net_sale", default=None)
    total_income: float | None = Field(alias="re_total_inc", default=None)
    total_income_new: float | None = Field(alias="re_total_inc", default=None)  # Alternative field
    other_income: float | None = Field(alias="re_oth_inc_new", default=None)
    interest_income: float | None = Field(alias="re_int_earned", default=None)
    income_from_investments: float | None = Field(alias="re_income_inv", default=None)

    # Expenses (in Lakhs)
    raw_material_consumed: float | None = Field(alias="re_rawmat_consump", default=None)
    purchase_traded_goods: float | None = Field(alias="re_pur_trd_goods", default=None)
    stock_in_trade_change: float | None = Field(alias="re_inc_dre_sttr", default=None)
    staff_cost: float | None = Field(alias="re_staff_cost", default=None)
    depreciation: float | None = Field(alias="re_depr_und_exp", default=None)
    interest_expense: float | None = Field(alias="re_int_new", default=None)
    other_expenses: float | None = Field(alias="re_oth_exp", default=None)
    total_expenses: float | None = Field(alias="re_oth_tot_exp", default=None)

    # Profit & Loss (in Lakhs)
    profit_before_tax: float | None = Field(alias="re_pro_loss_bef_tax", default=None)
    current_tax: float | None = Field(alias="re_curr_tax", default=None)
    deferred_tax: float | None = Field(alias="re_deff_tax", default=None)
    total_tax: float | None = Field(alias="re_tax", default=None)
    net_profit: float | None = Field(alias="re_net_profit", default=None)
    profit_from_continuing_ops: float | None = Field(alias="re_con_pro_loss", default=None)
    profit_from_discontinued_ops: float | None = Field(alias="re_prolos_dis_opr_aftr_tax", default=None)
    profit_ordinary_activities: float | None = Field(alias="re_proloss_ord_act", default=None)
    exceptional_items: float | None = Field(alias="re_excepn_items_new", default=None)
    extraordinary_items: float | None = Field(alias="re_extraord_items", default=None)
    share_of_associates: float | None = Field(alias="re_share_associate", default=None)
    minority_interest: float | None = Field(alias="re_minority_int", default=None)

    # Per Share Data
    face_value: float | None = Field(alias="re_face_val", default=None)
    paid_up_capital: float | None = Field(alias="re_pdup", default=None)
    basic_eps: float | None = Field(alias="re_basic_eps", default=None)
    diluted_eps: float | None = Field(alias="re_diluted_eps", default=None)
    basic_eps_continuing: float | None = Field(alias="re_basic_eps_for_cont_dic_opr", default=None)
    diluted_eps_continuing: float | None = Field(alias="re_dilut_eps_for_cont_dic_opr", default=None)

    # Financial Ratios
    debt_equity_ratio: float | None = Field(alias="re_debt_eqt_rat", default=None)
    interest_service_coverage: float | None = Field(alias="re_int_ser_cov", default=None)
    debt_service_coverage: float | None = Field(alias="re_debt_ser_cov", default=None)
    return_on_assets: float | None = Field(alias="re_ret_asset", default=None)

    # Banking specific (may be null for non-banking)
    gross_npa: float | None = Field(alias="re_grs_npa", default=None)
    gross_npa_percentage: float | None = Field(alias="re_grs_npa_per", default=None)
    capital_adequacy_ratio: float | None = Field(alias="re_cap_ade_rat", default=None)
    cet1_ratio: float | None = Field(alias="re_cet_1_ret", default=None)

    # Notes and Remarks
    notes: str | None = Field(alias="re_notes_to_ac", default=None)
    remarks: str | None = Field(alias="re_remarks", default=None)
    segment_notes: str | None = Field(alias="re_desc_note_seg", default=None)
    financial_notes: str | None = Field(alias="re_desc_note_fin", default=None)

    @field_validator("from_date", "to_date", "filing_date", mode="before")
    @classmethod
    def parse_date_field(cls, v: Any) -> date | None:
        if v is None:
            return None
        if isinstance(v, date):
            return v
        if isinstance(v, datetime):
            return v.date()
        dt = parse_nse_date(str(v))
        return dt.date() if dt else None

    @field_validator(
        "net_sales", "total_income", "total_income_new", "other_income",
        "interest_income", "income_from_investments",
        "raw_material_consumed", "purchase_traded_goods", "stock_in_trade_change",
        "staff_cost", "depreciation", "interest_expense", "other_expenses", "total_expenses",
        "profit_before_tax", "current_tax", "deferred_tax", "total_tax",
        "net_profit", "profit_from_continuing_ops", "profit_from_discontinued_ops",
        "profit_ordinary_activities", "exceptional_items", "extraordinary_items",
        "share_of_associates", "minority_interest",
        "paid_up_capital", "gross_npa",
        mode="before"
    )
    @classmethod
    def parse_lakhs_field(cls, v: Any) -> float | None:
        return _parse_lakhs(v)

    @field_validator(
        "face_value", "basic_eps", "diluted_eps",
        "basic_eps_continuing", "diluted_eps_continuing",
        "debt_equity_ratio", "interest_service_coverage", "debt_service_coverage",
        "return_on_assets", "gross_npa_percentage", "capital_adequacy_ratio", "cet1_ratio",
        mode="before"
    )
    @classmethod
    def parse_ratio_field(cls, v: Any) -> float | None:
        return _parse_ratio(v)

    @field_validator("notes", "remarks", "segment_notes", "financial_notes", mode="before")
    @classmethod
    def clean_notes(cls, v: Any) -> str | None:
        if v is None:
            return None
        s = str(v).strip()
        if s == "" or s == "-" or s == "null":
            return None
        return s

    @property
    def is_audited(self) -> bool:
        """Check if this result is audited."""
        return self.result_type == "A"

    @property
    def quarter(self) -> str | None:
        """Get the quarter string (e.g., 'Q3 FY25')."""
        if not self.to_date:
            return None
        month = self.to_date.month
        year = self.to_date.year
        if month in [3]:
            return f"Q4 FY{str(year)[2:]}"
        elif month in [6]:
            return f"Q1 FY{str(year + 1)[2:]}"
        elif month in [9]:
            return f"Q2 FY{str(year + 1)[2:]}"
        elif month in [12]:
            return f"Q3 FY{str(year + 1)[2:]}"
        return None

    @property
    def period_label(self) -> str:
        """Get a human-readable period label."""
        if self.to_date:
            return self.to_date.strftime("%b %Y")
        return "Unknown"

    @property
    def operating_profit(self) -> float | None:
        """Calculate operating profit (EBIT) if possible."""
        if self.profit_before_tax is not None and self.interest_expense is not None:
            return self.profit_before_tax + self.interest_expense
        return None

    @property
    def ebitda(self) -> float | None:
        """Calculate EBITDA if possible."""
        op = self.operating_profit
        if op is not None and self.depreciation is not None:
            return op + self.depreciation
        return None

    @property
    def net_profit_margin(self) -> float | None:
        """Calculate net profit margin percentage."""
        if self.net_profit is not None and self.net_sales is not None and self.net_sales > 0:
            return (self.net_profit / self.net_sales) * 100
        return None

    @property
    def operating_margin(self) -> float | None:
        """Calculate operating margin percentage."""
        op = self.operating_profit
        if op is not None and self.net_sales is not None and self.net_sales > 0:
            return (op / self.net_sales) * 100
        return None


class FinancialResultsComparison(BaseModel):
    """Container for financial results comparison data across multiple periods."""

    model_config = ConfigDict(str_strip_whitespace=True)

    symbol: str
    company_name: str | None = None
    is_banking: bool = False
    periods: list[FinancialResultPeriodData] = Field(default_factory=list)

    @property
    def latest(self) -> FinancialResultPeriodData | None:
        """Get the most recent period data."""
        if self.periods:
            return self.periods[0]
        return None

    @property
    def previous(self) -> FinancialResultPeriodData | None:
        """Get the previous period data (for QoQ comparison)."""
        if len(self.periods) > 1:
            return self.periods[1]
        return None

    @property
    def year_ago(self) -> FinancialResultPeriodData | None:
        """Get the same quarter from previous year (for YoY comparison)."""
        if len(self.periods) >= 4:
            # Usually 4th element is same quarter last year
            return self.periods[4] if len(self.periods) > 4 else self.periods[-1]
        return None

    def get_revenue_trend(self) -> list[tuple[str, float]]:
        """Get revenue trend across all periods."""
        return [
            (p.period_label, p.net_sales)
            for p in self.periods
            if p.net_sales is not None
        ]

    def get_profit_trend(self) -> list[tuple[str, float]]:
        """Get net profit trend across all periods."""
        return [
            (p.period_label, p.net_profit)
            for p in self.periods
            if p.net_profit is not None
        ]

    def get_eps_trend(self) -> list[tuple[str, float]]:
        """Get EPS trend across all periods."""
        return [
            (p.period_label, p.basic_eps_continuing or p.basic_eps)
            for p in self.periods
            if (p.basic_eps_continuing or p.basic_eps) is not None
        ]

    def get_margin_trend(self) -> list[tuple[str, float]]:
        """Get net profit margin trend across all periods."""
        return [
            (p.period_label, p.net_profit_margin)
            for p in self.periods
            if p.net_profit_margin is not None
        ]

    def calculate_growth(self, metric: str, periods_back: int = 1) -> float | None:
        """Calculate growth rate for a metric.

        Args:
            metric: Attribute name (e.g., 'net_sales', 'net_profit')
            periods_back: Number of periods to compare against (1=QoQ, 4=YoY)

        Returns:
            Growth percentage or None if calculation not possible
        """
        if len(self.periods) <= periods_back:
            return None

        current = getattr(self.periods[0], metric, None)
        previous = getattr(self.periods[periods_back], metric, None)

        if current is None or previous is None or previous == 0:
            return None

        return ((current - previous) / abs(previous)) * 100

    @property
    def revenue_growth_qoq(self) -> float | None:
        """Quarter-over-quarter revenue growth."""
        return self.calculate_growth("net_sales", 1)

    @property
    def revenue_growth_yoy(self) -> float | None:
        """Year-over-year revenue growth."""
        return self.calculate_growth("net_sales", 4)

    @property
    def profit_growth_qoq(self) -> float | None:
        """Quarter-over-quarter profit growth."""
        return self.calculate_growth("net_profit", 1)

    @property
    def profit_growth_yoy(self) -> float | None:
        """Year-over-year profit growth."""
        return self.calculate_growth("net_profit", 4)
