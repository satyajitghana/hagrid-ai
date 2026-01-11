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

class TickerHolders(BaseModel):
    """
    Model for Ticker Holders (Major, Institutional, Mutual Fund).
    """
    symbol: str
    major_holders: List[Dict[str, Any]] = Field(default_factory=list)
    institutional_holders: List[Dict[str, Any]] = Field(default_factory=list)
    mutualfund_holders: List[Dict[str, Any]] = Field(default_factory=list)
    insider_roster_holders: List[Dict[str, Any]] = Field(default_factory=list)

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