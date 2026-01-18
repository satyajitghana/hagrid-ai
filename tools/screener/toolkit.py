"""Agno Toolkit for Screener.in - for agent integration."""

from agno.tools import Toolkit

from .client import ScreenerClient
from .core.exceptions import ScreenerNotFoundError


class ScreenerToolkit(Toolkit):
    """Toolkit for Screener.in company fundamentals.

    Provides tools for agents to fetch company fundamentals,
    financial data, and analysis from Screener.in.
    """

    def __init__(self, timeout: float = 30.0, **kwargs):
        """Initialize the Screener toolkit.

        Args:
            timeout: Request timeout in seconds
        """
        self.client = ScreenerClient(timeout=timeout)

        tools = [
            self.search_company,
            self.get_company_fundamentals,
            self.get_price_chart,
        ]

        instructions = """Use these tools to fetch company fundamentals from Screener.in:
- Search for Indian companies by name or symbol
- Get detailed company fundamentals (financials, ratios, shareholding)
- Get price charts with moving averages

Symbols should be uppercase (e.g., "RELIANCE", "TCS", "INFY").
Best for fundamental analysis of Indian stocks."""

        super().__init__(name="screener", tools=tools, instructions=instructions, **kwargs)

    def search_company(self, query: str) -> str:
        """Search for companies by name or symbol on Screener.in.

        Use this tool to find companies before fetching their fundamentals.
        Returns matching companies with their IDs and URLs.

        Args:
            query: Search term (company name or symbol like "reliance", "tcs", "infosys")

        Returns:
            Markdown list of matching companies with:
            - Company name and symbol
            - Screener ID (for chart APIs)
            - URL to Screener page
        """
        try:
            response = self.client.search(query)

            if not response.companies:
                return f"No companies found matching '{query}'"

            lines = [f"# Search Results for '{query}'", ""]
            lines.append("| Company | Symbol | ID | URL |")
            lines.append("|---------|--------|----|----|")

            for company in response.companies[:15]:
                name = company.name[:40] + "..." if len(company.name) > 40 else company.name
                symbol = company.symbol or "-"
                cid = company.id or "-"
                url = f"https://www.screener.in{company.url}" if company.url else "-"
                lines.append(f"| {name} | {symbol} | {cid} | {url} |")

            lines.append("")
            lines.append(f"*Total matches: {len(response.companies)}*")

            return "\n".join(lines)

        except Exception as e:
            return f"Error searching for '{query}': {str(e)}"

    def get_company_fundamentals(self, symbol: str, consolidated: bool = True) -> str:
        """Get detailed company fundamentals from Screener.in.

        Returns comprehensive fundamental data including:
        - Company overview and key metrics
        - Quarterly and annual financial results
        - Balance sheet and cash flow highlights
        - Shareholding pattern
        - Peer comparison
        - Pros and cons analysis

        Args:
            symbol: Stock symbol (e.g., "RELIANCE", "TCS", "INFY", "HDFCBANK")
            consolidated: Use consolidated financials (default True).
                         Set to False for standalone results.

        Returns:
            Markdown formatted company fundamentals page
        """
        try:
            return self.client.get_report_by_symbol(symbol, consolidated=consolidated)

        except ScreenerNotFoundError:
            return f"Company not found: {symbol}. Please check the symbol and try again."
        except Exception as e:
            return f"Error fetching fundamentals for {symbol}: {str(e)}"

    def get_price_chart(self, symbol: str, days: int = 365) -> str:
        """Get price chart data with moving averages for a company.

        Fetches historical price data including:
        - Current price
        - 50-day moving average (DMA)
        - 200-day moving average (DMA)
        - Volume data

        Note: This requires the company ID which is fetched via search.

        Args:
            symbol: Stock symbol (e.g., "RELIANCE", "TCS")
            days: Number of days of history (default 365)

        Returns:
            Markdown with price chart summary including current price and moving averages
        """
        try:
            # First search for the company to get the ID
            company = self.client.search_first(symbol)

            if not company:
                return f"Company not found: {symbol}"

            if not company.id:
                return f"No company ID available for {symbol}. Cannot fetch chart data."

            # Get price chart
            chart = self.client.get_price_chart(
                company_id=company.id,
                days=days,
                consolidated=company.is_consolidated,
            )

            lines = [f"# Price Chart - {company.name} ({symbol})", ""]

            # Current price
            if chart.price and chart.price.latest_value:
                lines.append(f"**Current Price:** ₹{chart.price.latest_value:,.2f}")
                if chart.price.latest_date:
                    lines.append(f"**As of:** {chart.price.latest_date}")
                lines.append("")

            # Moving averages
            lines.append("## Moving Averages")
            lines.append("")

            if chart.dma50 and chart.dma50.latest_value:
                lines.append(f"**50 DMA:** ₹{chart.dma50.latest_value:,.2f}")

            if chart.dma200 and chart.dma200.latest_value:
                lines.append(f"**200 DMA:** ₹{chart.dma200.latest_value:,.2f}")

            # Price vs MA analysis
            if chart.price and chart.price.latest_value:
                price = chart.price.latest_value

                if chart.dma50 and chart.dma50.latest_value:
                    dma50 = chart.dma50.latest_value
                    diff_50 = ((price - dma50) / dma50) * 100
                    direction_50 = "above" if price > dma50 else "below"
                    lines.append(f"  - Price is {abs(diff_50):.1f}% {direction_50} 50 DMA")

                if chart.dma200 and chart.dma200.latest_value:
                    dma200 = chart.dma200.latest_value
                    diff_200 = ((price - dma200) / dma200) * 100
                    direction_200 = "above" if price > dma200 else "below"
                    lines.append(f"  - Price is {abs(diff_200):.1f}% {direction_200} 200 DMA")

            lines.append("")

            # Volume if available
            if chart.volume and chart.volume.latest_value:
                vol = chart.volume.latest_value
                if vol >= 10000000:
                    vol_str = f"{vol / 10000000:.2f} Cr"
                elif vol >= 100000:
                    vol_str = f"{vol / 100000:.2f} L"
                else:
                    vol_str = f"{vol:,.0f}"
                lines.append(f"**Volume:** {vol_str}")

            lines.append("")
            lines.append(f"*Data from Screener.in | [View on Screener](https://www.screener.in{company.url})*")

            return "\n".join(lines)

        except ScreenerNotFoundError:
            return f"Company not found: {symbol}"
        except Exception as e:
            return f"Error fetching price chart for {symbol}: {str(e)}"
