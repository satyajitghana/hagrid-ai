"""Symbol search API response models."""

from enum import Enum
from pydantic import BaseModel, Field
from typing import Any


class SymbolType(str, Enum):
    """Types of symbols available on TradingView."""
    STOCK = "stock"
    FUTURES = "futures"
    WARRANT = "warrant"
    BOND = "bond"
    FUND = "fund"
    DR = "dr"  # Depositary Receipt
    INDEX = "index"
    CRYPTO = "crypto"
    FOREX = "forex"
    CFD = "cfd"


class FuturesContract(BaseModel):
    """Futures contract information."""
    
    symbol: str = Field(description="Contract symbol")
    source_logoid: str | None = Field(default=None, alias="source_logoid")
    description: str | None = Field(default=None, description="Contract description (e.g., 'Jan 2026')")
    typespecs: list[str] = Field(default_factory=list, description="Type specifications")
    
    @property
    def is_continuous(self) -> bool:
        """Check if this is a continuous contract."""
        return "continuous" in self.typespecs
    
    @property
    def is_synthetic(self) -> bool:
        """Check if this is a synthetic contract."""
        return "synthetic" in self.typespecs

    class Config:
        populate_by_name = True


class SourceInfo(BaseModel):
    """Exchange/source information."""
    
    id: str = Field(description="Source ID (e.g., 'NSE')")
    name: str = Field(description="Source name")
    description: str = Field(description="Source description")


class Symbol(BaseModel):
    """Individual symbol from search results."""
    
    symbol: str = Field(description="Trading symbol")
    description: str = Field(description="Symbol description/company name")
    type: str = Field(description="Symbol type (stock, futures, bond, etc.)")
    exchange: str = Field(description="Exchange code")
    
    # Identifiers
    isin: str | None = Field(default=None, description="ISIN code")
    cusip: str | None = Field(default=None, description="CUSIP code")
    cik_code: str | None = Field(default=None, description="SEC CIK code")
    
    # Currency and country
    currency_code: str | None = Field(default=None, description="Trading currency")
    country: str | None = Field(default=None, description="Country code")
    
    # Logo IDs for fetching images
    logoid: str | None = Field(default=None, description="Symbol logo ID")
    currency_logoid: str | None = Field(default=None, alias="currency-logoid")
    source_logoid: str | None = Field(default=None, description="Exchange logo ID")
    
    # Source information
    source_id: str | None = Field(default=None, description="Source ID")
    source2: SourceInfo | None = Field(default=None, description="Extended source info")
    provider_id: str | None = Field(default=None, description="Data provider ID")
    
    # Type specifications
    typespecs: list[str] = Field(default_factory=list, description="Type specs (common, etf, etc.)")
    
    # Listing info
    is_primary_listing: bool = Field(default=False, description="Is primary listing")
    
    # IPO info
    ipo_offer_time: int | None = Field(default=None, description="IPO timestamp")
    
    # Search metadata
    found_by_isin: bool = Field(default=False)
    found_by_cusip: bool = Field(default=False)
    
    # Futures contracts (only for futures type)
    contracts: list[FuturesContract] = Field(default_factory=list)
    
    @property
    def full_symbol(self) -> str:
        """Get full symbol with exchange (e.g., 'NSE:RELIANCE')."""
        return f"{self.exchange}:{self.symbol}"
    
    @property
    def clean_description(self) -> str:
        """Get description without HTML tags."""
        import re
        return re.sub(r'<[^>]+>', '', self.description)
    
    @property
    def is_stock(self) -> bool:
        """Check if this is a stock."""
        return self.type == SymbolType.STOCK.value
    
    @property
    def is_futures(self) -> bool:
        """Check if this is a futures contract."""
        return self.type == SymbolType.FUTURES.value
    
    @property
    def is_etf(self) -> bool:
        """Check if this is an ETF."""
        return "etf" in self.typespecs
    
    @property
    def is_common_stock(self) -> bool:
        """Check if this is common stock."""
        return "common" in self.typespecs
    
    def get_logo_url(self, base_url: str = "https://s3-symbol-logo.tradingview.com") -> str | None:
        """Get URL for the symbol's logo."""
        if self.logoid:
            return f"{base_url}/{self.logoid}.svg"
        return None

    class Config:
        populate_by_name = True


class SymbolSearchResponse(BaseModel):
    """Response from symbol search API."""
    
    symbols_remaining: int = Field(
        description="Number of additional symbols matching the query"
    )
    symbols: list[Symbol] = Field(
        default_factory=list,
        description="List of matching symbols"
    )
    
    @classmethod
    def from_api_response(cls, data: dict[str, Any]) -> "SymbolSearchResponse":
        """Create response from raw API data."""
        return cls.model_validate(data)
    
    @property
    def stocks(self) -> list[Symbol]:
        """Get only stock symbols."""
        return [s for s in self.symbols if s.is_stock]
    
    @property
    def futures(self) -> list[Symbol]:
        """Get only futures symbols."""
        return [s for s in self.symbols if s.is_futures]
    
    @property
    def primary_listings(self) -> list[Symbol]:
        """Get only primary listings."""
        return [s for s in self.symbols if s.is_primary_listing]
    
    @property
    def first(self) -> Symbol | None:
        """Get the first symbol result."""
        return self.symbols[0] if self.symbols else None
    
    @property
    def first_stock(self) -> Symbol | None:
        """Get the first stock result."""
        stocks = self.stocks
        return stocks[0] if stocks else None
    
    def filter_by_exchange(self, exchange: str) -> list[Symbol]:
        """Filter symbols by exchange."""
        return [s for s in self.symbols if s.exchange.upper() == exchange.upper()]
    
    def filter_by_country(self, country: str) -> list[Symbol]:
        """Filter symbols by country."""
        return [s for s in self.symbols if s.country and s.country.upper() == country.upper()]