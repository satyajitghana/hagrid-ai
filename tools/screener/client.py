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

    def get_chart(
        self,
        company_id: int,
        query: str,
        days: int = 365,
        consolidated: bool = True,
    ) -> ChartResponse:
        """
        Get chart data for a company.

        Args:
            company_id: Company ID from search results
            query: Chart query string (metrics to fetch)
            days: Number of days of data (default: 365)
            consolidated: Use consolidated data (default: True)

        Returns:
            ChartResponse with datasets

        Example:
            >>> chart = client.get_chart(
            ...     company_id=2726,
            ...     query="Price-DMA50-DMA200-Volume",
            ...     days=365
            ... )
            >>> print(f"Latest price: {chart.price.latest_value}")
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

        Args:
            company_id: Company ID
            days: Number of days (default: 365)
            consolidated: Use consolidated data

        Returns:
            ChartResponse with Price, DMA50, DMA200, Volume datasets

        Example:
            >>> chart = client.get_price_chart(2726, days=365)
            >>> price = chart.price
            >>> print(f"Latest: ₹{price.latest_value} on {price.latest_date}")
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

        Args:
            company_id: Company ID
            days: Number of days (default: 10000 for max history)
            consolidated: Use consolidated data

        Returns:
            ChartResponse with PE, Median PE, EPS datasets

        Example:
            >>> chart = client.get_valuation_chart(2726)
            >>> pe = chart.pe_ratio
            >>> print(f"Current PE: {pe.latest_value}")
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

        Args:
            company_id: Company ID
            days: Number of days (default: 10000 for max history)
            consolidated: Use consolidated data

        Returns:
            ChartResponse with GPM, OPM, NPM, Quarter Sales datasets

        Example:
            >>> chart = client.get_margin_chart(2726)
            >>> opm = chart.opm
            >>> print(f"Latest OPM: {opm.latest_value}%")
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
        Get a comprehensive markdown report for a company.

        Includes name, description, charts (Price, PE, Margins), and fundamentals.

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

        # 2. Charts Summary
        if charts:
            md += "## Market & Financial Data (Latest)\n\n"
            
            # Price
            price_chart = charts.get('price')
            if price_chart and price_chart.price.latest_value:
                md += f"**Current Price:** ₹{price_chart.price.latest_value} ({price_chart.price.latest_date})\n"
                if price_chart.dma50.latest_value:
                    md += f"**50 DMA:** ₹{price_chart.dma50.latest_value}\n"
                if price_chart.dma200.latest_value:
                    md += f"**200 DMA:** ₹{price_chart.dma200.latest_value}\n"
            
            # Valuation
            val_chart = charts.get('valuation')
            if val_chart:
                if val_chart.pe_ratio.latest_value:
                    md += f"**PE Ratio:** {val_chart.pe_ratio.latest_value}\n"
                if val_chart.eps.latest_value:
                    md += f"**EPS (TTM):** ₹{val_chart.eps.latest_value}\n"
            
            # Margins
            margin_chart = charts.get('margin')
            if margin_chart:
                 if margin_chart.opm.latest_value:
                     md += f"**OPM:** {margin_chart.opm.latest_value}%\n"
                 if margin_chart.npm.latest_value:
                     md += f"**NPM:** {margin_chart.npm.latest_value}%\n"

            md += "\n"

        # 3. Fundamentals Page
        md += "## Fundamentals Analysis\n\n"
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