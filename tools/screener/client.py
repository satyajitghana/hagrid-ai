"""Screener.in API Client."""

import logging
from typing import Any

from .core.http_client import ScreenerHTTPClient
from .core.exceptions import ScreenerValidationError, ScreenerNotFoundError
from .models.search import CompanySearchResult, CompanySearchResponse
from .models.chart import (
    ChartResponse,
    PriceChartQuery,
    ValuationChartQuery,
    MarginChartQuery,
)

logger = logging.getLogger(__name__)


class ScreenerClient:
    """
    Client for interacting with Screener.in.
    
    Provides access to:
    - Company search API
    - Historical chart data (prices, PE, margins, etc.)
    - Company fundamentals page (as markdown)
    
    Example:
        >>> client = ScreenerClient()
        >>> 
        >>> # Search for a company
        >>> results = client.search("reliance")
        >>> company = results.first
        >>> print(f"Found: {company.name} ({company.symbol})")
        >>> 
        >>> # Get price chart data
        >>> chart = client.get_price_chart(company.id, days=365)
        >>> print(f"Latest price: ₹{chart.price.latest_value}")
        >>> 
        >>> # Get company fundamentals as markdown
        >>> markdown = client.get_company_page("RELIANCE")
        >>> print(markdown)
    """

    def __init__(
        self,
        timeout: float = 30.0,
    ) -> None:
        """
        Initialize the Screener client.

        Args:
            timeout: Request timeout in seconds
        """
        self._http = ScreenerHTTPClient(timeout=timeout)

    # ==========================================================================
    # Search API
    # ==========================================================================

    def search(
        self,
        query: str,
        version: int = 3,
        full_text_search: bool = True,
    ) -> CompanySearchResponse:
        """
        Search for companies by name or symbol.

        Args:
            query: Search term (company name or symbol)
            version: API version (default: 3)
            full_text_search: Enable full-text search (default: True)

        Returns:
            CompanySearchResponse with matching companies

        Example:
            >>> results = client.search("reliance")
            >>> for company in results.companies:
            ...     print(f"{company.name}: {company.url}")
        """
        if not query:
            raise ScreenerValidationError("query cannot be empty")

        params = {
            "q": query,
            "v": version,
            "fts": 1 if full_text_search else 0,
        }

        data = self._http.get_json("/company/search/", params=params)
        return CompanySearchResponse.from_api_response(data)

    def search_first(self, query: str) -> CompanySearchResult | None:
        """
        Search and return the first matching company.

        Args:
            query: Search term

        Returns:
            First matching company or None

        Example:
            >>> company = client.search_first("reliance industries")
            >>> if company:
            ...     print(f"ID: {company.id}, Symbol: {company.symbol}")
        """
        response = self.search(query)
        return response.first

    # ==========================================================================
    # Chart API
    # ==========================================================================
    #
    # Chart API availability:
    #   ✅ WORKS WITHOUT AUTH:
    #      - Price charts (Price, DMA50, DMA200, Volume)
    #      - get_price_chart()
    #
    #   ⚠️ MAY REQUIRE AUTH (returns 404):
    #      - Valuation charts (PE, EPS, Market Cap/Sales)
    #      - Margin charts (GPM, OPM, NPM)
    #      - get_valuation_chart(), get_market_cap_chart(), get_margin_chart()
    #
    # Alternative: Use get_company_page() which contains all data in HTML.
    # ==========================================================================

    def get_chart(
        self,
        company_id: int,
        query: str,
        days: int = 365,
        consolidated: bool = True,
    ) -> ChartResponse:
        """
        Get chart data for a company.

        Note: Some chart queries work without authentication (Price charts),
        while others (Valuation, Margin) may require a logged-in session.

        Args:
            company_id: Company ID from search results
            query: Chart query string (metrics to fetch)
            days: Number of days of data (default: 365)
            consolidated: Use consolidated data (default: True)

        Returns:
            ChartResponse with datasets

        Raises:
            ScreenerNotFoundError: If chart type requires auth
            ScreenerValidationError: If company_id is missing
        """
        if not company_id:
            raise ScreenerValidationError("company_id is required")

        params = {
            "q": query,
            "days": days,
            "consolidated": "true" if consolidated else "false",
        }

        data = self._http.get_json(f"/company/{company_id}/chart/", params=params)
        return ChartResponse.from_api_response(data)

    def get_price_chart(
        self,
        company_id: int,
        days: int = 365,
        consolidated: bool = True,
    ) -> ChartResponse:
        """
        Get price chart with moving averages and volume.

        ✅ WORKS WITHOUT AUTHENTICATION

        Args:
            company_id: Company ID from search results
            days: Number of days (default: 365)
            consolidated: Use consolidated data

        Returns:
            ChartResponse with Price, DMA50, DMA200, Volume datasets

        Example:
            >>> results = client.search("reliance")
            >>> chart = client.get_price_chart(results.first.id)
            >>> print(f"Latest: ₹{chart.price.latest_value}")
        """
        return self.get_chart(
            company_id=company_id,
            query=PriceChartQuery.PRICE_WITH_MA.value,
            days=days,
            consolidated=consolidated,
        )

    def get_valuation_chart(
        self,
        company_id: int,
        days: int = 10000,
        consolidated: bool = True,
    ) -> ChartResponse:
        """
        Get PE ratio and EPS chart.

        ⚠️ MAY REQUIRE AUTHENTICATION - Returns 404 without login.
        Alternative: Use get_company_page() for full data.

        Args:
            company_id: Company ID
            days: Number of days (default: 10000 for max history)
            consolidated: Use consolidated data

        Returns:
            ChartResponse with PE, Median PE, EPS datasets
        """
        return self.get_chart(
            company_id=company_id,
            query=ValuationChartQuery.PE_EPS.value,
            days=days,
            consolidated=consolidated,
        )

    def get_margin_chart(
        self,
        company_id: int,
        days: int = 10000,
        consolidated: bool = True,
    ) -> ChartResponse:
        """
        Get profit margin chart (GPM, OPM, NPM).

        ⚠️ MAY REQUIRE AUTHENTICATION - Returns 404 without login.
        Alternative: Use get_company_page() for full data.

        Args:
            company_id: Company ID
            days: Number of days (default: 10000 for max history)
            consolidated: Use consolidated data

        Returns:
            ChartResponse with GPM, OPM, NPM, Quarter Sales datasets
        """
        return self.get_chart(
            company_id=company_id,
            query=MarginChartQuery.ALL_MARGINS.value,
            days=days,
            consolidated=consolidated,
        )

    def get_market_cap_chart(
        self,
        company_id: int,
        days: int = 10000,
        consolidated: bool = True,
    ) -> ChartResponse:
        """
        Get market cap to sales ratio chart.

        ⚠️ MAY REQUIRE AUTHENTICATION - Returns 404 without login.
        Alternative: Use get_company_page() for full data.

        Args:
            company_id: Company ID
            days: Number of days (default: 10000 for max history)
            consolidated: Use consolidated data

        Returns:
            ChartResponse with Market Cap/Sales, Median, Sales datasets
        """
        return self.get_chart(
            company_id=company_id,
            query=ValuationChartQuery.MARKET_CAP_SALES.value,
            days=days,
            consolidated=consolidated,
        )

    # ==========================================================================
    # Company Page (Web Scraping)
    # ==========================================================================

    def get_company_page(
        self,
        symbol: str,
        consolidated: bool = True,
    ) -> str:
        """
        Get company fundamentals page as markdown.

        Fetches the Screener.in company page and converts it to
        markdown format suitable for LLM consumption.

        Args:
            symbol: Stock symbol (e.g., "RELIANCE", "TCS", "INFY")
            consolidated: Use consolidated view (default: True)

        Returns:
            Markdown content of the company page

        Example:
            >>> markdown = client.get_company_page("RELIANCE")
            >>> print(markdown[:500])  # Print first 500 chars
        """
        if not symbol:
            raise ScreenerValidationError("symbol cannot be empty")

        # Build path
        path = f"/company/{symbol.upper()}/"
        if consolidated:
            path = f"/company/{symbol.upper()}/consolidated/"

        return self._http.get_markdown(path)

    def get_company_page_raw(
        self,
        symbol: str,
        consolidated: bool = True,
    ) -> str:
        """
        Get company page as raw HTML.

        Args:
            symbol: Stock symbol
            consolidated: Use consolidated view

        Returns:
            Raw HTML content
        """
        if not symbol:
            raise ScreenerValidationError("symbol cannot be empty")

        path = f"/company/{symbol.upper()}/"
        if consolidated:
            path = f"/company/{symbol.upper()}/consolidated/"

        return self._http.get_html(path)

    # ==========================================================================
    # Convenience Methods
    # ==========================================================================

    def get_company_fundamentals(
        self,
        query: str,
    ) -> str:
        """
        Search for a company and get its fundamentals page.

        Convenience method that combines search and page fetch.

        Args:
            query: Company name or symbol

        Returns:
            Markdown content of the company page

        Raises:
            ScreenerNotFoundError: If company not found

        Example:
            >>> fundamentals = client.get_company_fundamentals("reliance industries")
            >>> print(fundamentals)
        """
        company = self.search_first(query)
        if not company:
            raise ScreenerNotFoundError(f"Company not found: {query}")

        return self._http.get_markdown(company.url)

    def get_all_chart_data(
        self,
        company_id: int,
        days: int = 365,
        consolidated: bool = True,
    ) -> dict[str, ChartResponse | None]:
        """
        Get all chart data for a company.

        Fetches price, valuation, and margin charts in one call.
        Returns None for charts that fail to fetch.

        Args:
            company_id: Company ID
            days: Number of days for price data
            consolidated: Use consolidated data

        Returns:
            Dictionary with 'price', 'valuation', 'margin' chart responses

        Example:
            >>> charts = client.get_all_chart_data(2726)
            >>> if charts['price']:
            ...     print(f"Price: ₹{charts['price'].price.latest_value}")
        """
        charts = {}
        
        try:
            charts["price"] = self.get_price_chart(company_id, days, consolidated)
        except Exception as e:
            logger.warning(f"Failed to fetch price chart: {e}")
            charts["price"] = None
            
        try:
            charts["valuation"] = self.get_valuation_chart(company_id, 10000, consolidated)
        except Exception as e:
            logger.warning(f"Failed to fetch valuation chart: {e}")
            charts["valuation"] = None
            
        try:
            charts["margin"] = self.get_margin_chart(company_id, 10000, consolidated)
        except Exception as e:
            logger.warning(f"Failed to fetch margin chart: {e}")
            charts["margin"] = None
            
        try:
            charts["market_cap"] = self.get_market_cap_chart(company_id, 10000, consolidated)
        except Exception as e:
            logger.warning(f"Failed to fetch market cap chart: {e}")
            charts["market_cap"] = None
            
        return charts

    def get_company_summary(
        self,
        query: str,
        price_days: int = 365,
    ) -> dict[str, Any]:
        """
        Get a complete summary of a company.

        Combines search, charts, and fundamentals page.

        Args:
            query: Company name or symbol
            price_days: Days of price history

        Returns:
            Dictionary with company info, charts, and fundamentals

        Example:
            >>> summary = client.get_company_summary("reliance")
            >>> print(f"Company: {summary['company'].name}")
            >>> print(f"Latest Price: ₹{summary['charts']['price'].price.latest_value}")
        """
        company = self.search_first(query)
        if not company:
            raise ScreenerNotFoundError(f"Company not found: {query}")

        result = {
            "company": company,
            "charts": None,
            "fundamentals_markdown": None,
        }

        # Get charts if we have company ID
        if company.id:
            result["charts"] = self.get_all_chart_data(
                company.id, 
                days=price_days,
                consolidated=company.is_consolidated,
            )

        # Get fundamentals page
        result["fundamentals_markdown"] = self._http.get_markdown(company.url)

        return result

    def get_company_markdown(
        self,
        query: str,
        price_days: int = 365,
    ) -> str:
        """
        Get a comprehensive markdown report for a company by search query.

        Note: Chart API may require authentication and often fails.
        Use get_report_markdown() with a CompanySearchResult for reliability.

        Args:
            query: Company name or symbol
            price_days: Days of price history

        Returns:
            Markdown formatted string
        """
        summary = self.get_company_summary(query, price_days=price_days)
        company = summary['company']
        charts = summary['charts']
        fundamentals = summary['fundamentals_markdown']

        md = f"# Report for {company.name} ({company.symbol})\n\n"
        
        # 1. Company Info
        md += f"**Screener ID:** {company.id}\n"
        md += f"**URL:** https://www.screener.in{company.url}\n\n"

        # 2. Charts Summary (often fails due to auth)
        if charts:
            md += "## Market & Financial Data (Latest)\n\n"
            
            # Price
            price_chart = charts.get('price')
            if price_chart and price_chart.price and price_chart.price.latest_value:
                md += f"**Current Price:** ₹{price_chart.price.latest_value} ({price_chart.price.latest_date})\n"
                if price_chart.dma50 and price_chart.dma50.latest_value:
                    md += f"**50 DMA:** ₹{price_chart.dma50.latest_value}\n"
                if price_chart.dma200 and price_chart.dma200.latest_value:
                    md += f"**200 DMA:** ₹{price_chart.dma200.latest_value}\n"
            
            # Valuation
            val_chart = charts.get('valuation')
            if val_chart:
                if val_chart.pe_ratio and val_chart.pe_ratio.latest_value:
                    md += f"**PE Ratio:** {val_chart.pe_ratio.latest_value}\n"
                if val_chart.eps and val_chart.eps.latest_value:
                    md += f"**EPS (TTM):** ₹{val_chart.eps.latest_value}\n"
            
            # Margins
            margin_chart = charts.get('margin')
            if margin_chart:
                 if margin_chart.opm and margin_chart.opm.latest_value:
                     md += f"**OPM:** {margin_chart.opm.latest_value}%\n"
                 if margin_chart.npm and margin_chart.npm.latest_value:
                     md += f"**NPM:** {margin_chart.npm.latest_value}%\n"

            md += "\n"

        # 3. Fundamentals Page
        md += "## Fundamentals Analysis\n\n"
        md += fundamentals

        return md

    def get_report_markdown(
        self,
        company: CompanySearchResult,
    ) -> str:
        """
        Get markdown report for a company from search result.

        This is the recommended method as it:
        - Avoids extra search API call
        - Uses the URL directly from search result
        - Doesn't rely on chart API (which requires auth)

        Args:
            company: CompanySearchResult from search()

        Returns:
            Markdown formatted string with company fundamentals

        Example:
            >>> results = client.search("reliance")
            >>> company = results.first
            >>> markdown = client.get_report_markdown(company)
            >>> print(markdown[:500])
        """
        if not company:
            raise ScreenerValidationError("company cannot be None")

        # Fetch the fundamentals page
        fundamentals = self._http.get_markdown(company.url)

        md = f"# {company.name}\n\n"
        md += f"**Symbol:** {company.symbol}\n"
        md += f"**Screener ID:** {company.id}\n"
        md += f"**URL:** https://www.screener.in{company.url}\n"
        md += f"**Consolidated:** {'Yes' if company.is_consolidated else 'No'}\n\n"
        md += "---\n\n"
        md += fundamentals

        return md

    def get_report_by_symbol(
        self,
        symbol: str,
        consolidated: bool = True,
    ) -> str:
        """
        Get markdown report for a company by stock symbol.

        Directly fetches the company page without searching.

        Args:
            symbol: Stock symbol (e.g., "RELIANCE", "TCS", "INFY")
            consolidated: Use consolidated view (default: True)

        Returns:
            Markdown formatted string

        Example:
            >>> markdown = client.get_report_by_symbol("RELIANCE")
            >>> print(markdown[:500])
        """
        if not symbol:
            raise ScreenerValidationError("symbol cannot be empty")

        # Build path
        path = f"/company/{symbol.upper()}/"
        if consolidated:
            path = f"/company/{symbol.upper()}/consolidated/"

        fundamentals = self._http.get_markdown(path)

        md = f"# {symbol.upper()}\n\n"
        md += f"**URL:** https://www.screener.in{path}\n"
        md += f"**Consolidated:** {'Yes' if consolidated else 'No'}\n\n"
        md += "---\n\n"
        md += fundamentals

        return md

    # ==========================================================================
    # Resource Management
    # ==========================================================================

    def close(self) -> None:
        """Close the client and release resources."""
        self._http.close()

    def __enter__(self) -> "ScreenerClient":
        """Context manager entry."""
        return self

    def __exit__(self, *args: Any) -> None:
        """Context manager exit."""
        self.close()