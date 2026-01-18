from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field
from datetime import datetime


class TickerInfo(BaseModel):
    """
    Model for Ticker Information.
    Captures the dictionary returned by yfinance.Ticker.info
    """
    symbol: str
    info: Dict[str, Any] = Field(default_factory=dict, description="Raw info dictionary from yfinance")


class PriceHistoryEntry(BaseModel):
    """
    Single entry for historical price data.
    """
    date: datetime
    open: float
    high: float
    low: float
    close: float
    volume: int
    dividends: Optional[float] = 0.0
    stock_splits: Optional[float] = 0.0


class TickerHistory(BaseModel):
    """
    Model for Ticker History.
    """
    symbol: str
    period: str
    interval: str
    history: List[PriceHistoryEntry]


class TickerFinancials(BaseModel):
    """
    Model for Ticker Financials (Income Statement, Balance Sheet, Cash Flow).
    """
    symbol: str
    income_statement: List[Dict[str, Any]] = Field(default_factory=list)
    balance_sheet: List[Dict[str, Any]] = Field(default_factory=list)
    cash_flow: List[Dict[str, Any]] = Field(default_factory=list)
    quarterly_income_statement: List[Dict[str, Any]] = Field(default_factory=list)
    quarterly_balance_sheet: List[Dict[str, Any]] = Field(default_factory=list)
    quarterly_cash_flow: List[Dict[str, Any]] = Field(default_factory=list)
    ttm_income_statement: List[Dict[str, Any]] = Field(default_factory=list)
    ttm_cash_flow: List[Dict[str, Any]] = Field(default_factory=list)


class TickerHolders(BaseModel):
    """
    Model for Ticker Holders (Major, Institutional, Mutual Fund, Insider).
    """
    symbol: str
    major_holders: List[Dict[str, Any]] = Field(default_factory=list)
    institutional_holders: List[Dict[str, Any]] = Field(default_factory=list)
    mutualfund_holders: List[Dict[str, Any]] = Field(default_factory=list)
    insider_roster_holders: List[Dict[str, Any]] = Field(default_factory=list)
    insider_purchases: List[Dict[str, Any]] = Field(default_factory=list)
    insider_transactions: List[Dict[str, Any]] = Field(default_factory=list)


class TickerAnalysis(BaseModel):
    """
    Model for Ticker Analysis (Recommendations, Upgrades/Downgrades, etc).
    """
    symbol: str
    recommendations: List[Dict[str, Any]] = Field(default_factory=list)
    recommendations_summary: List[Dict[str, Any]] = Field(default_factory=list)
    upgrades_downgrades: List[Dict[str, Any]] = Field(default_factory=list)
    analyst_price_targets: Dict[str, Any] = Field(default_factory=dict)
    earnings_estimate: List[Dict[str, Any]] = Field(default_factory=list)
    revenue_estimate: List[Dict[str, Any]] = Field(default_factory=list)
    earnings_history: List[Dict[str, Any]] = Field(default_factory=list)
    eps_trend: List[Dict[str, Any]] = Field(default_factory=list)
    eps_revisions: List[Dict[str, Any]] = Field(default_factory=list)
    growth_estimates: List[Dict[str, Any]] = Field(default_factory=list)


class TickerCalendar(BaseModel):
    """
    Model for Ticker Calendar (Earnings, etc).
    """
    symbol: str
    calendar: Dict[str, Any] = Field(default_factory=dict)
    earnings_dates: List[Dict[str, Any]] = Field(default_factory=list)


class TickerOptions(BaseModel):
    """
    Model for Ticker Options Chain (Summary).
    """
    symbol: str
    expiration_dates: List[str] = Field(default_factory=list)
    calls: List[Dict[str, Any]] = Field(default_factory=list)
    puts: List[Dict[str, Any]] = Field(default_factory=list)


class TickerSustainability(BaseModel):
    """
    Model for Ticker Sustainability.
    """
    symbol: str
    sustainability: Dict[str, Any] = Field(default_factory=dict)


class DividendEntry(BaseModel):
    """Single dividend entry."""
    date: datetime
    dividend: float


class TickerDividends(BaseModel):
    """Model for Ticker Dividends."""
    symbol: str
    dividends: List[DividendEntry] = Field(default_factory=list)


class SplitEntry(BaseModel):
    """Single stock split entry."""
    date: datetime
    split_ratio: float


class TickerSplits(BaseModel):
    """Model for Ticker Stock Splits."""
    symbol: str
    splits: List[SplitEntry] = Field(default_factory=list)


class ActionEntry(BaseModel):
    """Single corporate action entry."""
    date: datetime
    dividends: float = 0.0
    stock_splits: float = 0.0


class TickerActions(BaseModel):
    """Model for Ticker Corporate Actions (dividends + splits)."""
    symbol: str
    actions: List[ActionEntry] = Field(default_factory=list)


class CapitalGainEntry(BaseModel):
    """Single capital gain entry."""
    date: datetime
    capital_gain: float


class TickerCapitalGains(BaseModel):
    """Model for Ticker Capital Gains."""
    symbol: str
    capital_gains: List[CapitalGainEntry] = Field(default_factory=list)


class SharesEntry(BaseModel):
    """Single shares outstanding entry."""
    date: datetime
    shares: int


class TickerShares(BaseModel):
    """Model for Ticker Shares Outstanding history."""
    symbol: str
    shares: List[SharesEntry] = Field(default_factory=list)


class TickerFastInfo(BaseModel):
    """Model for Ticker Fast Info (lightweight price data)."""
    symbol: str
    currency: Optional[str] = None
    day_high: Optional[float] = None
    day_low: Optional[float] = None
    exchange: Optional[str] = None
    fifty_day_average: Optional[float] = None
    last_price: Optional[float] = None
    last_volume: Optional[int] = None
    market_cap: Optional[float] = None
    open: Optional[float] = None
    previous_close: Optional[float] = None
    quote_type: Optional[str] = None
    regular_market_previous_close: Optional[float] = None
    shares: Optional[int] = None
    ten_day_average_volume: Optional[int] = None
    three_month_average_volume: Optional[int] = None
    timezone: Optional[str] = None
    two_hundred_day_average: Optional[float] = None
    year_change: Optional[float] = None
    year_high: Optional[float] = None
    year_low: Optional[float] = None


class TickerHistoryMetadata(BaseModel):
    """Model for Ticker History Metadata."""
    symbol: str
    metadata: Dict[str, Any] = Field(default_factory=dict)


class SECFiling(BaseModel):
    """Single SEC filing entry."""
    date: Optional[datetime] = None
    type: Optional[str] = None
    title: Optional[str] = None
    edgar_url: Optional[str] = None
    exhibits: List[Dict[str, Any]] = Field(default_factory=list)


class TickerSECFilings(BaseModel):
    """Model for Ticker SEC Filings."""
    symbol: str
    filings: List[SECFiling] = Field(default_factory=list)


class TickerISIN(BaseModel):
    """Model for Ticker ISIN."""
    symbol: str
    isin: Optional[str] = None


class FundsData(BaseModel):
    """Model for ETF/Mutual Fund data."""
    symbol: str
    description: Optional[str] = None
    fund_overview: Dict[str, Any] = Field(default_factory=dict)
    fund_operations: Dict[str, Any] = Field(default_factory=dict)
    asset_classes: Dict[str, Any] = Field(default_factory=dict)
    top_holdings: List[Dict[str, Any]] = Field(default_factory=list)
    equity_holdings: Dict[str, Any] = Field(default_factory=dict)
    bond_holdings: Dict[str, Any] = Field(default_factory=dict)
    bond_ratings: Dict[str, Any] = Field(default_factory=dict)
    sector_weightings: Dict[str, Any] = Field(default_factory=dict)
