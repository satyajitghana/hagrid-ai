from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from datetime import datetime


class GlobalIndex(BaseModel):
    """
    Model for Global Index data.
    """
    symbol: str
    name: str
    country: Optional[str] = None
    last_price: Optional[float] = None
    change: Optional[float] = None
    change_percent: Optional[float] = None
    market_state: Optional[str] = None


class MarketStatus(BaseModel):
    """Model for Market Status from yf.Market."""
    market: str
    status: Dict[str, Any] = Field(default_factory=dict)
    summary: Dict[str, Any] = Field(default_factory=dict)


class EarningsEvent(BaseModel):
    """Single earnings calendar event."""
    symbol: Optional[str] = None
    company_name: Optional[str] = None
    earnings_date: Optional[datetime] = None
    eps_estimate: Optional[float] = None
    reported_eps: Optional[float] = None
    surprise_percent: Optional[float] = None


class IPOEvent(BaseModel):
    """Single IPO calendar event."""
    symbol: Optional[str] = None
    company_name: Optional[str] = None
    exchange: Optional[str] = None
    price_range: Optional[str] = None
    shares: Optional[int] = None
    date: Optional[datetime] = None


class SplitEvent(BaseModel):
    """Single stock split calendar event."""
    symbol: Optional[str] = None
    company_name: Optional[str] = None
    date: Optional[datetime] = None
    split_ratio: Optional[str] = None


class EconomicEvent(BaseModel):
    """Single economic calendar event."""
    event_name: Optional[str] = None
    country: Optional[str] = None
    date: Optional[datetime] = None
    actual: Optional[str] = None
    estimate: Optional[str] = None
    prior: Optional[str] = None


class CalendarsData(BaseModel):
    """Model for Calendars data from yf.Calendars."""
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    earnings: List[Dict[str, Any]] = Field(default_factory=list)
    ipo_info: List[Dict[str, Any]] = Field(default_factory=list)
    splits: List[Dict[str, Any]] = Field(default_factory=list)
    economic_events: List[Dict[str, Any]] = Field(default_factory=list)


class SearchQuote(BaseModel):
    """Single search quote result."""
    symbol: Optional[str] = None
    short_name: Optional[str] = None
    long_name: Optional[str] = None
    quote_type: Optional[str] = None
    exchange: Optional[str] = None
    sector: Optional[str] = None
    industry: Optional[str] = None
    score: Optional[float] = None


class SearchNews(BaseModel):
    """Single search news result."""
    title: Optional[str] = None
    publisher: Optional[str] = None
    link: Optional[str] = None
    publish_time: Optional[datetime] = None
    type: Optional[str] = None


class SearchResults(BaseModel):
    """Model for Search results from yf.Search."""
    query: str
    quotes: List[Dict[str, Any]] = Field(default_factory=list)
    news: List[Dict[str, Any]] = Field(default_factory=list)
    research: List[Dict[str, Any]] = Field(default_factory=list)


class LookupResults(BaseModel):
    """Model for Lookup results from yf.Lookup."""
    query: str
    all: List[Dict[str, Any]] = Field(default_factory=list)
    stocks: List[Dict[str, Any]] = Field(default_factory=list)
    mutual_funds: List[Dict[str, Any]] = Field(default_factory=list)
    etfs: List[Dict[str, Any]] = Field(default_factory=list)
    indices: List[Dict[str, Any]] = Field(default_factory=list)
    futures: List[Dict[str, Any]] = Field(default_factory=list)
    currencies: List[Dict[str, Any]] = Field(default_factory=list)
    cryptocurrencies: List[Dict[str, Any]] = Field(default_factory=list)


class SectorData(BaseModel):
    """Model for Sector data from yf.Sector."""
    key: str
    name: Optional[str] = None
    symbol: Optional[str] = None
    overview: Dict[str, Any] = Field(default_factory=dict)
    top_companies: List[Dict[str, Any]] = Field(default_factory=list)
    top_etfs: List[Dict[str, Any]] = Field(default_factory=list)
    top_mutual_funds: List[Dict[str, Any]] = Field(default_factory=list)
    industries: List[Dict[str, Any]] = Field(default_factory=list)
    research_reports: List[Dict[str, Any]] = Field(default_factory=list)


class IndustryData(BaseModel):
    """Model for Industry data from yf.Industry."""
    key: str
    name: Optional[str] = None
    symbol: Optional[str] = None
    sector_key: Optional[str] = None
    sector_name: Optional[str] = None
    overview: Dict[str, Any] = Field(default_factory=dict)
    top_companies: List[Dict[str, Any]] = Field(default_factory=list)
    top_performing_companies: List[Dict[str, Any]] = Field(default_factory=list)
    top_growth_companies: List[Dict[str, Any]] = Field(default_factory=list)
    research_reports: List[Dict[str, Any]] = Field(default_factory=list)


class ScreenerResult(BaseModel):
    """Model for Screener results from yf.screen."""
    query_name: Optional[str] = None
    total: int = 0
    results: List[Dict[str, Any]] = Field(default_factory=list)


class BulkDownloadResult(BaseModel):
    """Model for bulk download results."""
    symbols: List[str] = Field(default_factory=list)
    period: Optional[str] = None
    interval: Optional[str] = None
    start: Optional[str] = None
    end: Optional[str] = None
    data: List[Dict[str, Any]] = Field(default_factory=list)
