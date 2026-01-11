"""
TradingView SDK - Access TradingView's public APIs for stock data.

This SDK provides access to:
- Symbol search (stocks, futures, bonds, funds, etc.)
- News for symbols
- Technical indicators and scanner data

Example:
    >>> from tools.tradingview import TradingViewClient
    >>> 
    >>> client = TradingViewClient()
    >>> 
    >>> # Search for a symbol
    >>> results = client.search_symbol("RELIANCE")
    >>> symbol = results.first_stock
    >>> print(f"Found: {symbol.full_symbol}")
    >>> 
    >>> # Get technical indicators
    >>> technicals = client.get_technicals("NSE:RELIANCE")
    >>> print(f"RSI: {technicals.rsi}")
    >>> print(f"Recommendation: {technicals.overall_recommendation}")
    >>> 
    >>> # Get news
    >>> news = client.get_news("NSE:RELIANCE")
    >>> for item in news.items[:5]:
    ...     print(f"{item.title}")
"""

from .client import TradingViewClient
from .core.exceptions import (
    TradingViewError,
    TradingViewAPIError,
    TradingViewConnectionError,
    TradingViewRateLimitError,
    TradingViewValidationError,
    TradingViewNotFoundError,
)
from .models.symbol import (
    SymbolType,
    Symbol,
    SymbolSearchResponse,
)
from .models.news import (
    NewsProvider,
    NewsItem,
    NewsResponse,
)
from .models.scanner import (
    Recommendation,
    TechnicalIndicators,
    TECHNICALS_FIELDS,
)

__all__ = [
    # Client
    "TradingViewClient",
    # Exceptions
    "TradingViewError",
    "TradingViewAPIError",
    "TradingViewConnectionError",
    "TradingViewRateLimitError",
    "TradingViewValidationError",
    "TradingViewNotFoundError",
    # Symbol models
    "SymbolType",
    "Symbol",
    "SymbolSearchResponse",
    # News models
    "NewsProvider",
    "NewsItem",
    "NewsResponse",
    # Scanner models
    "Recommendation",
    "TechnicalIndicators",
    "TECHNICALS_FIELDS",
]

__version__ = "0.1.0"