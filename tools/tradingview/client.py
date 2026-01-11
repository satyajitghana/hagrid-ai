"""TradingView API Client."""

import logging
from typing import Any

from .core.http_client import TradingViewHTTPClient
from .core.exceptions import TradingViewValidationError, TradingViewNotFoundError
from .models.symbol import Symbol, SymbolSearchResponse
from .models.news import NewsResponse, NewsItem
from .models.scanner import TechnicalIndicators, TECHNICALS_FIELDS

logger = logging.getLogger(__name__)


class TradingViewClient:
    """
    Client for interacting with TradingView's public APIs.
    
    Provides access to:
    - Symbol search (search for stocks, futures, bonds, etc.)
    - News for symbols
    - Technical indicators and scanner data
    
    Example:
        >>> client = TradingViewClient()
        >>> 
        >>> # Search for a symbol
        >>> results = client.search_symbol("RELIANCE")
        >>> symbol = results.first_stock
        >>> print(f"Found: {symbol.full_symbol}")
        >>> 
        >>> # Get news for a symbol
        >>> news = client.get_news("NSE:RELIANCE")
        >>> for item in news.items[:5]:
        ...     print(f"{item.published_date}: {item.title}")
        >>> 
        >>> # Get technical indicators
        >>> technicals = client.get_technicals("NSE:RELIANCE")
        >>> print(f"RSI: {technicals.rsi}")
        >>> print(f"Recommendation: {technicals.overall_recommendation}")
    """

    def __init__(
        self,
        timeout: float = 30.0,
    ) -> None:
        """
        Initialize the TradingView client.

        Args:
            timeout: Request timeout in seconds
        """
        self._http = TradingViewHTTPClient(timeout=timeout)

    # ==========================================================================
    # Symbol Search API
    # ==========================================================================

    def search_symbol(
        self,
        text: str,
        exchange: str | None = None,
        lang: str = "en",
        search_type: str | None = None,
        sort_by_country: str = "US",
        highlight: bool = True,
    ) -> SymbolSearchResponse:
        """
        Search for symbols by name, ticker, or ISIN.

        Args:
            text: Search text (symbol, company name, or ISIN)
            exchange: Filter by exchange (e.g., "NSE", "NYSE")
            lang: Language code (default: "en")
            search_type: Type filter (e.g., "stock", "futures")
            sort_by_country: Sort results by country (default: "US")
            highlight: Enable result highlighting (default: True)

        Returns:
            SymbolSearchResponse with matching symbols

        Example:
            >>> results = client.search_symbol("RELIANCE", exchange="NSE")
            >>> for symbol in results.stocks:
            ...     print(f"{symbol.full_symbol}: {symbol.clean_description}")
        """
        if not text:
            raise TradingViewValidationError("text cannot be empty")

        params = {
            "text": text,
            "hl": 1 if highlight else 0,
            "exchange": exchange or "",
            "lang": lang,
            "search_type": search_type or "undefined",
            "domain": "production",
            "sort_by_country": sort_by_country,
            "promo": "true",
        }

        data = self._http.symbol_search("/symbol_search/v3/", params=params)
        return SymbolSearchResponse.from_api_response(data)

    def search_first(self, text: str, exchange: str | None = None) -> Symbol | None:
        """
        Search and return the first matching symbol.

        Args:
            text: Search text
            exchange: Optional exchange filter

        Returns:
            First matching symbol or None

        Example:
            >>> symbol = client.search_first("RELIANCE", exchange="NSE")
            >>> if symbol:
            ...     print(f"Found: {symbol.full_symbol}")
        """
        response = self.search_symbol(text, exchange=exchange)
        return response.first

    def search_stock(self, text: str, exchange: str | None = None) -> Symbol | None:
        """
        Search and return the first matching stock.

        Args:
            text: Search text
            exchange: Optional exchange filter

        Returns:
            First matching stock or None

        Example:
            >>> stock = client.search_stock("INFY", exchange="NSE")
            >>> print(f"ISIN: {stock.isin}")
        """
        response = self.search_symbol(text, exchange=exchange)
        return response.first_stock

    # ==========================================================================
    # News API
    # ==========================================================================

    def get_news(
        self,
        symbol: str,
        lang: str = "en",
        client_type: str = "overview",
        user_prostatus: str = "non_pro",
    ) -> NewsResponse:
        """
        Get news for a symbol.

        Args:
            symbol: Full symbol with exchange (e.g., "NSE:RELIANCE")
            lang: Language code (default: "en")
            client_type: Client type (default: "overview")
            user_prostatus: User status (default: "non_pro")

        Returns:
            NewsResponse with news items

        Example:
            >>> news = client.get_news("NSE:RELIANCE")
            >>> for item in news.items[:5]:
            ...     print(f"{item.title}")
            ...     print(f"  Source: {item.provider_name}")
        """
        if not symbol:
            raise TradingViewValidationError("symbol cannot be empty")

        # Normalize symbol format
        if ":" not in symbol:
            raise TradingViewValidationError(
                "symbol must include exchange (e.g., 'NSE:RELIANCE')"
            )

        params = {
            "filter": [f"lang:{lang}", f"symbol:{symbol}"],
            "client": client_type,
            "user_prostatus": user_prostatus,
        }

        # Build query string manually for filter array
        query_parts = [
            f"filter=lang%3A{lang}",
            f"filter=symbol%3A{symbol}",
            f"client={client_type}",
            f"user_prostatus={user_prostatus}",
        ]
        endpoint = f"/public/view/v1/symbol?{'&'.join(query_parts)}"

        data = self._http.get(self._http.NEWS_URL, endpoint)
        return NewsResponse.from_api_response(data)

    def get_latest_news(
        self,
        symbol: str,
        count: int = 10,
    ) -> list[NewsItem]:
        """
        Get latest news items for a symbol.

        Args:
            symbol: Full symbol with exchange
            count: Number of items to return

        Returns:
            List of news items

        Example:
            >>> news = client.get_latest_news("NSE:RELIANCE", count=5)
            >>> for item in news:
            ...     print(f"{item.published_datetime}: {item.title}")
        """
        response = self.get_news(symbol)
        return response.items[:count]

    # ==========================================================================
    # Scanner/Technicals API
    # ==========================================================================

    def get_technicals(
        self,
        symbol: str,
        fields: list[str] | None = None,
    ) -> TechnicalIndicators:
        """
        Get technical indicators for a symbol.

        Args:
            symbol: Full symbol with exchange (e.g., "NSE:RELIANCE")
            fields: List of fields to fetch (default: all standard fields)

        Returns:
            TechnicalIndicators with all requested data

        Example:
            >>> technicals = client.get_technicals("NSE:RELIANCE")
            >>> print(f"RSI: {technicals.rsi}")
            >>> print(f"MACD: {technicals.macd_macd}")
            >>> print(f"Recommendation: {technicals.overall_recommendation}")
        """
        if not symbol:
            raise TradingViewValidationError("symbol cannot be empty")

        if ":" not in symbol:
            raise TradingViewValidationError(
                "symbol must include exchange (e.g., 'NSE:RELIANCE')"
            )

        if fields is None:
            fields = TECHNICALS_FIELDS

        params = {
            "symbol": symbol,
            "fields": ",".join(fields),
            "no_404": "true",
            "label-product": "popup-technicals",
        }

        data = self._http.scanner("/symbol", params=params)
        return TechnicalIndicators.from_api_response(data)

    def get_recommendation(self, symbol: str) -> str:
        """
        Get overall technical recommendation for a symbol.

        Args:
            symbol: Full symbol with exchange

        Returns:
            Recommendation string (STRONG_BUY, BUY, NEUTRAL, SELL, STRONG_SELL)

        Example:
            >>> rec = client.get_recommendation("NSE:RELIANCE")
            >>> print(f"Recommendation: {rec}")
        """
        technicals = self.get_technicals(symbol)
        return technicals.overall_recommendation.value

    def get_moving_averages(self, symbol: str) -> dict[str, float | None]:
        """
        Get all moving averages for a symbol.

        Args:
            symbol: Full symbol with exchange

        Returns:
            Dictionary of moving average values

        Example:
            >>> mas = client.get_moving_averages("NSE:RELIANCE")
            >>> print(f"SMA200: {mas['SMA200']}")
        """
        technicals = self.get_technicals(symbol)
        return technicals.get_all_moving_averages()

    def get_pivot_levels(self, symbol: str) -> dict[str, float | None]:
        """
        Get classic pivot levels for a symbol.

        Args:
            symbol: Full symbol with exchange

        Returns:
            Dictionary with R3, R2, R1, Pivot, S1, S2, S3

        Example:
            >>> pivots = client.get_pivot_levels("NSE:RELIANCE")
            >>> print(f"Pivot: {pivots['Pivot']}")
            >>> print(f"R1: {pivots['R1']}, S1: {pivots['S1']}")
        """
        technicals = self.get_technicals(symbol)
        return technicals.get_classic_pivot_levels()

    # ==========================================================================
    # Convenience Methods
    # ==========================================================================

    def get_symbol_overview(
        self,
        text: str,
        exchange: str | None = None,
    ) -> dict[str, Any]:
        """
        Get a complete overview for a symbol.

        Combines search, news, and technicals.

        Args:
            text: Symbol or company name to search
            exchange: Optional exchange filter

        Returns:
            Dictionary with symbol, news, and technicals

        Example:
            >>> overview = client.get_symbol_overview("RELIANCE", exchange="NSE")
            >>> print(f"Symbol: {overview['symbol'].full_symbol}")
            >>> print(f"Price: {overview['technicals'].close}")
            >>> print(f"Recommendation: {overview['technicals'].overall_recommendation}")
        """
        # Search for symbol
        symbol = self.search_stock(text, exchange=exchange)
        if not symbol:
            raise TradingViewNotFoundError(f"Symbol not found: {text}")

        full_symbol = symbol.full_symbol

        # Get news and technicals
        try:
            news = self.get_news(full_symbol)
        except Exception as e:
            logger.warning(f"Failed to fetch news for {full_symbol}: {e}")
            news = None

        try:
            technicals = self.get_technicals(full_symbol)
        except Exception as e:
            logger.warning(f"Failed to fetch technicals for {full_symbol}: {e}")
            technicals = None

        return {
            "symbol": symbol,
            "news": news,
            "technicals": technicals,
            "full_symbol": full_symbol,
            "logo_url": symbol.get_logo_url(),
        }

    def get_symbol_with_technicals(
        self,
        text: str,
        exchange: str | None = None,
    ) -> tuple[Symbol, TechnicalIndicators] | None:
        """
        Search for a symbol and get its technical indicators.

        Args:
            text: Symbol or company name
            exchange: Optional exchange filter

        Returns:
            Tuple of (Symbol, TechnicalIndicators) or None if not found

        Example:
            >>> result = client.get_symbol_with_technicals("TCS", exchange="NSE")
            >>> if result:
            ...     symbol, technicals = result
            ...     print(f"{symbol.clean_description}: RSI={technicals.rsi}")
        """
        symbol = self.search_stock(text, exchange=exchange)
        if not symbol:
            return None

        technicals = self.get_technicals(symbol.full_symbol)
        return (symbol, technicals)

    def get_logo_url(self, logoid: str, extension: str = "svg") -> str:
        """
        Get URL for a symbol's logo.

        Args:
            logoid: Logo ID from symbol data
            extension: File extension (svg, png)

        Returns:
            Full URL to logo image
        """
        return self._http.get_logo_url(logoid, extension)

    # ==========================================================================
    # Resource Management
    # ==========================================================================

    def close(self) -> None:
        """Close the client and release resources."""
        self._http.close()

    def __enter__(self) -> "TradingViewClient":
        """Context manager entry."""
        return self

    def __exit__(self, *args: Any) -> None:
        """Context manager exit."""
        self.close()