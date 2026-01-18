"""Agno Toolkit for Public Market Data - for agent integration."""

from agno.tools import Toolkit

from .client import PublicMarketDataClient


class PublicMarketDataToolkit(Toolkit):
    """Toolkit for fetching public market data from various sources.

    Provides tools for agents to fetch:
    - FII/FPI investment data from CDSL (monthly and fortnightly reports)
    - Global indices live prices (Groww)
    - Indian indices data (Groww)
    """

    def __init__(self, timeout: float = 30.0, **kwargs):
        """Initialize the Public Market Data toolkit.

        Args:
            timeout: Request timeout in seconds
        """
        self.client = PublicMarketDataClient(timeout=timeout)

        tools = [
            self.get_fii_monthly_data,
            self.get_fii_fortnightly_data,
            self.list_fii_fortnightly_dates,
            self.get_global_indices,
            self.get_indian_indices,
        ]

        instructions = """Use these tools for public market data:
- FII/FPI monthly and fortnightly investment data from CDSL
- Sector-wise FPI allocation changes
- Global indices (SGX Nifty, Dow Jones, Hang Seng, etc.)
- Indian indices list with 52-week ranges

For FII data, use list_fii_fortnightly_dates first to see available report dates."""

        super().__init__(name="public_market_data", tools=tools, instructions=instructions, **kwargs)

    def get_fii_monthly_data(self) -> str:
        """Get daily FII/FPI investment and derivative trading data from CDSL.

        Use this tool to fetch current month's Foreign Institutional Investor (FII)
        and Foreign Portfolio Investor (FPI) activity data including:

        **Investment Data:**
        - Daily investments by asset class: Equity, Debt (General Limit, VRR, FAR),
          Hybrid, Mutual Funds, and Alternative Investment Funds (AIFs)
        - Investment routes: Stock Exchange and Primary Market
        - Gross Purchases, Gross Sales, and Net Investment in both INR and USD

        **Derivative Trading Data:**
        - Daily derivative positions by product type
        - Index Futures/Options, Stock Futures/Options
        - Interest Rate, Currency, and Commodity derivatives
        - Buy/Sell volumes and Open Interest

        This data is useful for understanding:
        - FII/FPI sentiment and flow direction
        - Sector allocation changes
        - Derivative market positioning

        Returns:
            Markdown formatted content with daily FII/FPI investment data
        """
        try:
            return self.client.get_fii_monthly_data()
        except Exception as e:
            return f"Error fetching FII monthly data: {str(e)}"

    def get_fii_fortnightly_data(self, report_date: str | None = None) -> str:
        """Get FII/FPI fortnightly sector-wise investment data from CDSL.

        Use this tool to fetch detailed sector-wise Foreign Portfolio Investor (FPI)
        investment data for a specific fortnightly period including:

        **Investment Data:**
        - Assets Under Custody (AUC) at start and end of fortnight
        - Net investment by sector for the 15-day period
        - Data broken down by: Equity, Debt, Hybrid, Mutual Funds, AIFs
        - 22+ sectors tracked (Financial Services, IT, Auto, Healthcare, etc.)

        **Additional Data:**
        - Top 10 companies in debt holdings
        - Exchange rates used for conversion (INR/USD)

        This data is useful for:
        - Understanding which sectors FPIs are buying/selling
        - Tracking sector rotation by foreign investors
        - Analyzing long-term FPI positioning changes

        Args:
            report_date: Report date string (e.g., "December 31, 2025", "November 15, 2025").
                        If not specified, fetches the most recent available report.
                        Use `list_fii_fortnightly_dates` tool to see available dates.

        Returns:
            Markdown formatted content with sector-wise FPI investment data
        """
        try:
            return self.client.get_fii_fortnightly_data(report_date)
        except Exception as e:
            return f"Error fetching FII fortnightly data for {report_date or 'latest'}: {str(e)}"

    def list_fii_fortnightly_dates(self) -> str:
        """List all available FII/FPI fortnightly report dates.

        Use this tool to see which fortnightly reports are available before
        fetching a specific report with `get_fii_fortnightly_data`.

        Reports are released twice a month (around 15th and end of month)
        and cover the previous 15-day period.

        Returns:
            List of available report dates in reverse chronological order
            (most recent first)
        """
        dates = self.client.list_available_fortnightly_dates()
        lines = [
            "# Available FII Fortnightly Report Dates",
            "",
            "Reports are released twice monthly (mid-month and month-end).",
            "Use any of these dates with `get_fii_fortnightly_data` tool.",
            "",
        ]

        # Group by year
        current_year = None
        for d in dates:
            year = d.split(",")[-1].strip()
            if year != current_year:
                lines.append(f"## {year}")
                current_year = year
            lines.append(f"- {d}")

        return "\n".join(lines)

    # ==================== Groww APIs ====================

    def get_global_indices(self) -> str:
        """Get live prices for major global indices.

        Use this tool to fetch real-time data for global market indices including:

        **Asia:**
        - SGX Nifty / GIFT Nifty (Singapore)
        - NIKKEI 225 (Japan)
        - Hang Seng (Hong Kong)
        - KOSPI (South Korea)

        **US:**
        - Dow Jones Industrial Average
        - Dow Futures
        - S&P 500

        **Europe:**
        - DAX (Germany)
        - CAC 40 (France)
        - FTSE 100 (UK)

        This data is useful for:
        - Pre-market analysis (SGX Nifty indicates opening direction)
        - Global market sentiment
        - Inter-market correlations
        - Understanding global risk-on/risk-off sentiment

        Returns:
            Markdown formatted table with live prices, change, and OHLC data
        """
        try:
            indices = self.client.get_global_indices()

            if not indices:
                return "No global indices data available."

            lines = [
                "# Global Indices - Live Prices",
                "",
                "| Index | Country | Price | Change | Open | High | Low |",
                "|-------|---------|-------|--------|------|------|-----|",
            ]

            for idx in indices:
                change = idx.get("day_change", 0) or 0
                change_perc = idx.get("day_change_perc", 0) or 0
                emoji = "🟢" if change >= 0 else "🔴"
                sign = "+" if change >= 0 else ""

                price = idx.get("value")
                price_str = f"{price:,.2f}" if price else "-"
                open_str = f"{idx.get('open'):,.2f}" if idx.get("open") else "-"
                high_str = f"{idx.get('high'):,.2f}" if idx.get("high") else "-"
                low_str = f"{idx.get('low'):,.2f}" if idx.get("low") else "-"

                lines.append(
                    f"| **{idx.get('name', '')}** ({idx.get('symbol', '')}) | {idx.get('country', '')} | "
                    f"{price_str} | {emoji} {sign}{change_perc:.2f}% | {open_str} | {high_str} | {low_str} |"
                )

            lines.append("")
            lines.append("*Data from Groww*")

            return "\n".join(lines)

        except Exception as e:
            return f"Error fetching global indices: {str(e)}"

    def get_indian_indices(self) -> str:
        """Get list of Indian market indices with 52-week high/low data.

        Use this tool to fetch data for Indian market indices including:

        **Major Indices:**
        - NIFTY 50, NIFTY Bank, NIFTY Financial Services
        - BSE Sensex, BSE Bankex
        - India VIX (volatility index)

        **Broad Market:**
        - NIFTY Next 50, NIFTY 100, NIFTY 500
        - NIFTY Total Market

        **Cap-based:**
        - NIFTY Midcap 100/150, NIFTY Midcap Select
        - NIFTY Smallcap 100/250

        **Sectoral:**
        - NIFTY IT, NIFTY Pharma, NIFTY Auto
        - NIFTY FMCG, NIFTY Metal, NIFTY PSU Bank
        - NIFTY Commodities

        Returns:
            Markdown formatted table with index names, F&O status, and 52-week range
        """
        try:
            indices = self.client.get_indian_indices()

            if not indices:
                return "No Indian indices data available."

            lines = [
                "# Indian Market Indices",
                "",
                "| Index | Symbol | F&O | 52W Low | 52W High |",
                "|-------|--------|-----|---------|----------|",
            ]

            for idx in indices:
                fno = "✓" if idx.get("is_fno_enabled") else "-"
                year_low = idx.get("year_low")
                year_high = idx.get("year_high")
                low_str = f"{year_low:,.2f}" if year_low else "-"
                high_str = f"{year_high:,.2f}" if year_high else "-"

                lines.append(
                    f"| **{idx.get('display_name', '')}** | {idx.get('symbol', '')} | "
                    f"{fno} | {low_str} | {high_str} |"
                )

            lines.append("")
            lines.append("*F&O = Futures & Options available | Data from Groww*")

            return "\n".join(lines)

        except Exception as e:
            return f"Error fetching Indian indices: {str(e)}"
