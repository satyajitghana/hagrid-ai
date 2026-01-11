"""News API response models."""

from datetime import datetime
from pydantic import BaseModel, Field
from typing import Any


class NewsProvider(BaseModel):
    """News provider information."""
    
    id: str = Field(description="Provider ID (e.g., 'reuters', 'tradingview')")
    name: str = Field(description="Provider display name")
    logo_id: str | None = Field(default=None, description="Logo ID for provider")
    url: str | None = Field(default=None, description="Provider website URL")


class RelatedSymbol(BaseModel):
    """Symbol related to a news story."""
    
    symbol: str = Field(description="Full symbol (e.g., 'NSE:RELIANCE')")
    logoid: str | None = Field(default=None, description="Symbol logo ID")
    currency_logoid: str | None = Field(default=None, alias="currency-logoid")
    base_currency_logoid: str | None = Field(default=None, alias="base-currency-logoid")
    
    @property
    def exchange(self) -> str | None:
        """Extract exchange from symbol."""
        if ":" in self.symbol:
            return self.symbol.split(":")[0]
        return None
    
    @property
    def ticker(self) -> str:
        """Extract ticker from symbol."""
        if ":" in self.symbol:
            return self.symbol.split(":")[1]
        return self.symbol
    
    def get_logo_url(self, base_url: str = "https://s3-symbol-logo.tradingview.com") -> str | None:
        """Get URL for the symbol's logo."""
        if self.logoid:
            return f"{base_url}/{self.logoid}.svg"
        return None

    class Config:
        populate_by_name = True


class NewsItem(BaseModel):
    """Individual news item."""
    
    id: str = Field(description="Unique news item ID")
    title: str = Field(description="News headline")
    published: int = Field(description="Publication timestamp (Unix)")
    urgency: int = Field(default=2, description="Urgency level (1=high, 2=normal)")
    
    # Links
    link: str | None = Field(default=None, description="External link to full article")
    story_path: str | None = Field(default=None, alias="storyPath", description="TradingView story path")
    
    # Related content
    related_symbols: list[RelatedSymbol] = Field(
        default_factory=list, 
        alias="relatedSymbols",
        description="Symbols mentioned in the story"
    )
    
    # Provider
    provider: NewsProvider | None = Field(default=None, description="News source provider")
    
    # Access and flags
    permission: str | None = Field(default=None, description="Access permission (e.g., 'headline', 'provider')")
    is_exclusive: bool = Field(default=False, alias="isExclusive", description="Is exclusive content")
    
    @property
    def published_datetime(self) -> datetime:
        """Convert Unix timestamp to datetime."""
        return datetime.fromtimestamp(self.published)
    
    @property
    def published_date(self) -> str:
        """Get formatted date string."""
        return self.published_datetime.strftime("%Y-%m-%d")
    
    @property
    def published_time(self) -> str:
        """Get formatted time string."""
        return self.published_datetime.strftime("%H:%M:%S")
    
    @property
    def is_headline_only(self) -> bool:
        """Check if only headline is accessible."""
        return self.permission == "headline"
    
    @property
    def is_provider_content(self) -> bool:
        """Check if content requires provider access."""
        return self.permission == "provider"
    
    @property
    def has_external_link(self) -> bool:
        """Check if there's an external link."""
        return self.link is not None
    
    @property
    def provider_name(self) -> str:
        """Get provider name or 'Unknown'."""
        return self.provider.name if self.provider else "Unknown"
    
    def get_tradingview_url(self, base: str = "https://www.tradingview.com") -> str | None:
        """Get full TradingView URL for the story."""
        if self.story_path:
            return f"{base}{self.story_path}"
        return None
    
    def get_symbol_tickers(self) -> list[str]:
        """Get list of ticker symbols mentioned."""
        return [s.ticker for s in self.related_symbols]

    class Config:
        populate_by_name = True


class NewsSection(BaseModel):
    """News category/section."""
    
    id: str = Field(description="Section ID (e.g., 'ipo', 'earnings')")
    title: str = Field(description="Section display title")


class NewsResponse(BaseModel):
    """Response from news API."""
    
    items: list[NewsItem] = Field(
        default_factory=list,
        description="List of news items"
    )
    sections: list[NewsSection] = Field(
        default_factory=list,
        description="Available news sections/categories"
    )
    
    @classmethod
    def from_api_response(cls, data: dict[str, Any]) -> "NewsResponse":
        """Create response from raw API data."""
        return cls.model_validate(data)
    
    @property
    def count(self) -> int:
        """Get number of news items."""
        return len(self.items)
    
    @property
    def latest(self) -> NewsItem | None:
        """Get the most recent news item."""
        if not self.items:
            return None
        return max(self.items, key=lambda x: x.published)
    
    @property
    def headlines(self) -> list[str]:
        """Get list of all headlines."""
        return [item.title for item in self.items]
    
    def filter_by_provider(self, provider_id: str) -> list[NewsItem]:
        """Filter news by provider ID."""
        return [
            item for item in self.items 
            if item.provider and item.provider.id == provider_id
        ]
    
    def filter_by_urgency(self, urgency: int) -> list[NewsItem]:
        """Filter news by urgency level."""
        return [item for item in self.items if item.urgency == urgency]
    
    def filter_exclusive(self) -> list[NewsItem]:
        """Get only exclusive news items."""
        return [item for item in self.items if item.is_exclusive]
    
    def filter_by_symbol(self, symbol: str) -> list[NewsItem]:
        """Filter news mentioning a specific symbol."""
        symbol_upper = symbol.upper()
        return [
            item for item in self.items 
            if any(s.symbol.upper() == symbol_upper or s.ticker.upper() == symbol_upper 
                   for s in item.related_symbols)
        ]
    
    def get_all_symbols(self) -> set[str]:
        """Get all unique symbols mentioned across all news."""
        symbols = set()
        for item in self.items:
            for s in item.related_symbols:
                symbols.add(s.symbol)
        return symbols
    
    def get_section_ids(self) -> list[str]:
        """Get list of section IDs."""
        return [s.id for s in self.sections]