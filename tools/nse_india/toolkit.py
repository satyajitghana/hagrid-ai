"""Agno Toolkit for NSE India corporate announcements - for agent integration."""

import csv
from datetime import date, datetime
from io import StringIO
from pathlib import Path
from typing import Any

from agno.tools import Toolkit

from .client import NSEIndiaClient
from .models.announcement import (
    Announcement,
    AnnualReport,
    DebtAnnouncement,
    EquityAnnouncement,
    ShareholdingPattern,
)
from .models.enums import AnnouncementIndex
from .models.financial_results import FinancialResultsComparison
from .models.most_active import (
    MostActiveResponse,
    MostActiveSMEResponse,
    MostActiveETFResponse,
    PriceVariationsResponse,
    VolumeGainersResponse,
)
from .models.oi_spurts import OISpurtData, OISpurtsResponse
from .models.shareholding import DetailedShareholdingPattern


class NSEIndiaToolkit(Toolkit):
    """Toolkit for NSE India corporate announcements.

    Provides tools for agents to fetch corporate announcements,
    annual reports, and related data from NSE India.
    """

    def __init__(
        self,
        db_path: str | Path = "nse_announcements.db",
        attachments_dir: str | Path = "./nse_attachments",
        **kwargs,
    ):
        """Initialize the NSE India toolkit.

        Args:
            db_path: Path to SQLite database for tracking
            attachments_dir: Directory for downloaded attachments
        """
        self.client = NSEIndiaClient(
            db_path=db_path,
            attachments_dir=attachments_dir,
        )

        tools = [
            self.get_equity_announcements,
            self.get_debt_announcements,
            self.get_symbol_announcements,
            self.get_new_announcements,
            self.get_annual_reports,
            self.get_shareholding_patterns,
            self.get_detailed_shareholding,
            self.get_financial_results_comparison,
            self.get_oi_spurts,
            self.get_most_active,
            self.get_market_movers,
            self.get_price_band_hitters,
            self.get_symbol_summary,
            self.get_gift_nifty,
            self.get_index_constituents,
            self.get_index_symbols,
            self.get_index_summary,
            # New enhanced tools
            self.scan_oi_spurts,
            self.fetch_sector_constituents,
        ]

        instructions = """Use these tools to fetch data from NSE India:
- Corporate announcements (equity, debt, symbol-specific)
- Annual reports and shareholding patterns
- Financial results comparison across quarters
- Open Interest (OI) spurts and market activity
- Most active stocks, market movers, price band hitters
- Comprehensive symbol summaries with derivatives data
- GIFT NIFTY prices
- Index constituents and symbols (NIFTY 50, NIFTY 100, NIFTY BANK, etc.)
- Index summaries with price, returns, top contributors

**New Enhanced Tools:**
- `scan_oi_spurts()` - Categorizes OI changes as bullish/bearish signals:
  * Long Buildup (bullish), Short Buildup (bearish)
  * Short Covering (bullish), Long Unwinding (bearish)
- `fetch_sector_constituents(sector)` - Get all stocks in a sector by name:
  * Examples: "banking", "it", "pharma", "auto", "metal", "fmcg"

Available indices: NIFTY 50, NIFTY NEXT 50, NIFTY 100, NIFTY 200, NIFTY 500,
NIFTY BANK, NIFTY IT, NIFTY PHARMA, NIFTY AUTO, NIFTY FMCG, NIFTY METAL,
NIFTY REALTY, NIFTY ENERGY, NIFTY INFRA, NIFTY PSE, NIFTY PSU BANK, etc.

Note: Symbol should be in uppercase (e.g., "RELIANCE", "TCS", "INFY")."""

        super().__init__(name="nse_india", tools=tools, instructions=instructions, **kwargs)

    def _format_announcements_as_csv(self, announcements: list[Announcement]) -> str:
        """Format announcements as CSV for LLM readability.

        Args:
            announcements: List of announcements to format

        Returns:
            CSV formatted string
        """
        if not announcements:
            return "No announcements found."

        output = StringIO()

        # Determine columns based on announcement type
        first = announcements[0]
        if isinstance(first, EquityAnnouncement):
            fieldnames = [
                "symbol",
                "company_name",
                "subject",
                "details",
                "broadcast_datetime",
                "attachment_url",
            ]
        else:
            fieldnames = [
                "company_name",
                "subject",
                "details",
                "broadcast_datetime",
                "attachment_url",
            ]

        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()

        for ann in announcements:
            row = {
                "company_name": ann.company_name,
                "subject": ann.subject,
                "details": ann.details[:200] + "..." if len(ann.details) > 200 else ann.details,
                "broadcast_datetime": (
                    ann.broadcast_datetime.strftime("%Y-%m-%d %H:%M:%S")
                    if ann.broadcast_datetime
                    else "-"
                ),
                "attachment_url": ann.attachment_url or "",
            }

            if isinstance(ann, EquityAnnouncement):
                row["symbol"] = ann.symbol

            writer.writerow(row)

        return output.getvalue()

    def _format_reports_as_csv(self, reports: list[AnnualReport], symbol: str) -> str:
        """Format annual reports as CSV for LLM readability.

        Args:
            reports: List of annual reports to format
            symbol: Stock symbol

        Returns:
            CSV formatted string
        """
        if not reports:
            return f"No annual reports found for {symbol}."

        output = StringIO()
        fieldnames = [
            "company_name",
            "financial_year",
            "broadcast_datetime",
            "file_url",
            "file_type",
        ]

        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()

        for report in reports:
            writer.writerow({
                "company_name": report.company_name,
                "financial_year": report.financial_year,
                "broadcast_datetime": (
                    report.broadcast_datetime.strftime("%Y-%m-%d %H:%M:%S")
                    if report.broadcast_datetime
                    else "-"
                ),
                "file_url": report.file_url,
                "file_type": "ZIP" if report.is_zip else "PDF",
            })

        return output.getvalue()

    def _parse_date(self, date_str: str | None) -> date | None:
        """Parse date string in DD-MM-YYYY format.

        Args:
            date_str: Date string or None

        Returns:
            Parsed date or None
        """
        if not date_str:
            return None

        try:
            return datetime.strptime(date_str, "%d-%m-%Y").date()
        except ValueError:
            try:
                return datetime.strptime(date_str, "%Y-%m-%d").date()
            except ValueError:
                return None

    def get_equity_announcements(self, limit: int = 50) -> str:
        """Get latest equity corporate announcements from NSE India.

        Use this tool to fetch recent corporate announcements for all
        equity securities listed on NSE.

        Args:
            limit: Maximum number of announcements to return (default 50)

        Returns:
            CSV formatted string of announcements with columns:
            symbol, company_name, subject, details, broadcast_datetime, attachment_url
        """
        announcements = self.client.get_announcements(AnnouncementIndex.EQUITIES)
        return self._format_announcements_as_csv(announcements[:limit])

    def get_debt_announcements(self, limit: int = 50) -> str:
        """Get latest debt securities corporate announcements from NSE India.

        Use this tool to fetch recent corporate announcements for debt
        securities (bonds, NCDs) listed on NSE.

        Args:
            limit: Maximum number of announcements to return (default 50)

        Returns:
            CSV formatted string of announcements with columns:
            company_name, subject, details, broadcast_datetime, attachment_url
        """
        announcements = self.client.get_announcements(AnnouncementIndex.DEBT)
        return self._format_announcements_as_csv(announcements[:limit])

    def get_symbol_announcements(
        self,
        symbol: str,
        from_date: str | None = None,
        to_date: str | None = None,
        limit: int = 50,
    ) -> str:
        """Get corporate announcements for a specific stock symbol.

        Use this tool to fetch announcements for a specific company
        identified by its NSE symbol.

        Args:
            symbol: Stock symbol (e.g., "RELIANCE", "IREDA", "TCS")
            from_date: Start date in DD-MM-YYYY format (optional)
            to_date: End date in DD-MM-YYYY format (optional)
            limit: Maximum number of announcements to return (default 50)

        Returns:
            CSV formatted string of announcements for the symbol
        """
        from_date_parsed = self._parse_date(from_date)
        to_date_parsed = self._parse_date(to_date)

        announcements = self.client.get_announcements(
            index=AnnouncementIndex.EQUITIES,
            symbol=symbol,
            from_date=from_date_parsed,
            to_date=to_date_parsed,
        )

        return self._format_announcements_as_csv(announcements[:limit])

    def get_new_announcements(self, index: str = "equities", limit: int = 50) -> str:
        """Get only new/unprocessed announcements (not seen before).

        Use this tool to fetch announcements that haven't been processed yet.
        This is useful for tracking only new corporate events.

        Args:
            index: Type of announcements - "equities", "debt", "sme", "mf", "slb"
            limit: Maximum number of announcements to return (default 50)

        Returns:
            CSV formatted string of new announcements only
        """
        try:
            idx = AnnouncementIndex(index.lower())
        except ValueError:
            return f"Invalid index type: {index}. Valid options: equities, debt, sme, mf, slb"

        new_announcements = self.client.get_new_announcements(idx)
        return self._format_announcements_as_csv(new_announcements[:limit])

    def get_annual_reports(self, symbol: str) -> str:
        """Get annual reports for a company.

        Use this tool to fetch all available annual reports for a company.
        Annual reports contain detailed financial information, management
        discussions, and company strategy.

        Args:
            symbol: Stock symbol (e.g., "RELIANCE", "TCS", "INFY")

        Returns:
            CSV formatted string of annual reports with columns:
            company_name, financial_year, broadcast_datetime, file_url, file_type
        """
        reports = self.client.get_annual_reports(symbol=symbol)
        return self._format_reports_as_csv(reports, symbol)

    def _format_shareholding_patterns(self, patterns: list[ShareholdingPattern], symbol: str) -> str:
        """Format shareholding patterns as a markdown table.

        Args:
            patterns: List of shareholding patterns
            symbol: Stock symbol

        Returns:
            Markdown formatted string
        """
        if not patterns:
            return f"No shareholding pattern data found for {symbol}."

        lines = []
        lines.append(f"# Shareholding Pattern History - {patterns[0].company_name} ({symbol})")
        lines.append("")
        lines.append("| Quarter | Date | Promoter % | Public % | Employee Trust % |")
        lines.append("|---------|------|------------|----------|------------------|")

        for pattern in patterns:
            quarter = pattern.quarter or "-"
            date_str = pattern.pattern_date.strftime("%d-%b-%Y") if pattern.pattern_date else "-"
            promoter = f"{pattern.promoter_percentage:.2f}" if pattern.promoter_percentage is not None else "-"
            public = f"{pattern.public_percentage:.2f}" if pattern.public_percentage is not None else "-"
            emp_trust = f"{pattern.employee_trusts:.2f}" if pattern.employee_trusts is not None else "-"

            lines.append(f"| {quarter} | {date_str} | {promoter}% | {public}% | {emp_trust}% |")

        lines.append("")

        # Add trend summary if we have enough data
        # Filter to only patterns with valid (non-zero) promoter percentage
        valid_patterns = [p for p in patterns if p.promoter_percentage and p.promoter_percentage > 0]

        if len(valid_patterns) >= 2:
            latest = valid_patterns[0]
            oldest = valid_patterns[-1]

            promoter_change = latest.promoter_percentage - oldest.promoter_percentage
            public_change = (latest.public_percentage or 0) - (oldest.public_percentage or 0)

            lines.append("## Trend Summary")
            lines.append("")
            oldest_date = oldest.pattern_date.strftime("%b %Y") if oldest.pattern_date else "earliest"
            latest_date = latest.pattern_date.strftime("%b %Y") if latest.pattern_date else "latest"
            lines.append(f"*From {oldest_date} to {latest_date}:*")

            promoter_direction = "↑" if promoter_change > 0 else "↓" if promoter_change < 0 else "→"
            public_direction = "↑" if public_change > 0 else "↓" if public_change < 0 else "→"

            lines.append(f"- Promoter holding: {promoter_direction} {abs(promoter_change):.2f}%")
            lines.append(f"- Public holding: {public_direction} {abs(public_change):.2f}%")
            lines.append("")

        return "\n".join(lines)

    def get_shareholding_patterns(self, symbol: str, limit: int = 20) -> str:
        """Get historical shareholding pattern data for a company.

        Use this tool to fetch quarterly shareholding pattern history showing
        how promoter and public ownership has changed over time.

        The data includes:
        - Quarter-wise promoter group holdings percentage
        - Public shareholding percentage
        - Employee trust holdings (if any)
        - Trend analysis showing ownership changes

        Args:
            symbol: Stock symbol (e.g., "RELIANCE", "TCS", "INFY")
            limit: Maximum number of quarters to return (default 20)

        Returns:
            Markdown formatted table showing shareholding pattern history
            with promoter %, public %, and trend analysis
        """
        try:
            patterns = self.client.get_shareholding_patterns_history(symbol=symbol)
            # Filter to only valid patterns (with non-zero promoter percentage)
            valid_patterns = [p for p in patterns if p.promoter_percentage and p.promoter_percentage > 0]
            return self._format_shareholding_patterns(valid_patterns[:limit], symbol.upper())
        except Exception as e:
            return f"Error fetching shareholding patterns for {symbol}: {str(e)}"

    def _format_detailed_shareholding(self, details: DetailedShareholdingPattern) -> str:
        """Format detailed shareholding pattern as markdown.

        Args:
            details: DetailedShareholdingPattern object

        Returns:
            Markdown formatted string
        """
        lines = []

        # Header
        period_str = details.period_ended.strftime("%d-%b-%Y") if details.period_ended else "N/A"
        lines.append(f"# Detailed Shareholding Pattern - {details.company_name} ({details.symbol})")
        lines.append(f"**Period Ended:** {period_str}")
        lines.append("")

        # Summary table
        lines.append("## Summary")
        lines.append("")
        lines.append("| Category | Shareholders | Shares | % Holding |")
        lines.append("|----------|--------------|--------|-----------|")

        for s in details.summary:
            if s.total_shares > 0 or "total" in s.category_name.lower():
                lines.append(
                    f"| {s.category_name} | {s.num_shareholders:,} | {s.total_shares:,} | {s.shareholding_percentage:.2f}% |"
                )

        lines.append("")

        # Top Promoters
        top_promoters = details.top_promoters
        if top_promoters:
            lines.append("## Top Promoter Shareholders")
            lines.append("")
            lines.append("| Name | Type | Shares | % Holding |")
            lines.append("|------|------|--------|-----------|")

            for p in top_promoters[:15]:
                # Skip subtotals
                if "total" in p.name.lower() or "sub-total" in p.name.lower():
                    continue
                name = p.name[:40] + "..." if len(p.name) > 40 else p.name
                entity_type = p.entity_type or "-"
                lines.append(
                    f"| {name} | {entity_type} | {p.total_shares:,} | {p.shareholding_percentage:.2f}% |"
                )

            lines.append("")

        # Beneficial Owners
        top_bos = details.top_beneficial_owners
        if top_bos:
            lines.append("## Significant Beneficial Owners")
            lines.append("")
            lines.append("| Beneficial Owner | Registered Holder | % Holding | Voting % |")
            lines.append("|------------------|-------------------|-----------|----------|")

            seen_combos = set()
            for bo in top_bos[:10]:
                combo = (bo.sbo_name, bo.registered_owner_name)
                if combo in seen_combos:
                    continue
                seen_combos.add(combo)

                sbo_name = bo.sbo_name[:35] + "..." if len(bo.sbo_name) > 35 else bo.sbo_name
                reg_name = bo.registered_owner_name[:25] + "..." if len(bo.registered_owner_name) > 25 else bo.registered_owner_name
                lines.append(
                    f"| {sbo_name} | {reg_name} | {bo.shareholding_percentage:.2f}% | {bo.voting_rights_percentage:.2f}% |"
                )

            lines.append("")

        # Public Institutions Summary
        if details.public_institutions:
            institutions_with_shares = [i for i in details.public_institutions if i.total_shares > 0 and "total" not in i.name.lower()]
            if institutions_with_shares:
                lines.append("## Major Institutional Holders")
                lines.append("")
                lines.append("| Institution Type | Shares | % Holding |")
                lines.append("|------------------|--------|-----------|")

                for inst in sorted(institutions_with_shares, key=lambda x: x.shareholding_percentage, reverse=True)[:10]:
                    name = inst.name[:35] + "..." if len(inst.name) > 35 else inst.name
                    lines.append(
                        f"| {name} | {inst.total_shares:,} | {inst.shareholding_percentage:.2f}% |"
                    )

                lines.append("")

        # Non-Public Shareholders
        if details.non_public_shareholders:
            non_public_with_shares = [n for n in details.non_public_shareholders if n.total_shares > 0]
            if non_public_with_shares:
                lines.append("## Non-Public Shareholders")
                lines.append("")
                for np in non_public_with_shares[:5]:
                    lines.append(f"- **{np.name}**: {np.total_shares:,} shares ({np.shareholding_percentage:.2f}%)")
                lines.append("")

        return "\n".join(lines)

    def get_detailed_shareholding(self, symbol: str) -> str:
        """Get detailed shareholding pattern with individual shareholder names.

        This tool fetches comprehensive shareholding data for the latest quarter including:
        - Summary by category (Promoter, Public, Non-Public)
        - Individual promoter shareholders with their exact holdings
        - Significant Beneficial Owners (SBOs) - the actual people/entities behind holdings
        - Institutional holders breakdown
        - Non-public shareholders

        Use this when you need to know WHO owns the company, not just the percentages.

        Args:
            symbol: Stock symbol (e.g., "RELIANCE", "TCS", "IREDA")

        Returns:
            Markdown formatted detailed shareholding pattern with shareholder names
        """
        try:
            details = self.client.get_latest_shareholding_details(symbol)
            if details is None:
                return f"No shareholding data found for {symbol}"
            return self._format_detailed_shareholding(details)
        except Exception as e:
            return f"Error fetching detailed shareholding for {symbol}: {str(e)}"

    def _format_financial_comparison(self, comparison: FinancialResultsComparison) -> str:
        """Format financial results comparison as markdown.

        Args:
            comparison: FinancialResultsComparison object

        Returns:
            Markdown formatted string
        """
        lines = []

        # Header
        lines.append(f"# Financial Results Comparison - {comparison.symbol}")
        if comparison.is_banking:
            lines.append("*(Banking/NBFC Company)*")
        lines.append("")

        if not comparison.periods:
            lines.append("No financial data available.")
            return "\n".join(lines)

        # Latest quarter summary
        latest = comparison.latest
        if latest:
            lines.append("## Latest Quarter Summary")
            lines.append(f"**Period:** {latest.quarter or 'N/A'} (ended {latest.period_label})")
            lines.append(f"**Audited:** {'Yes' if latest.is_audited else 'No'}")
            lines.append("")

            # Key metrics
            def fmt_lakhs(v: float | None) -> str:
                if v is None:
                    return "N/A"
                if abs(v) >= 100000:
                    return f"₹{v / 100:.0f} Cr"
                return f"₹{v:,.0f} L"

            def fmt_growth(v: float | None) -> str:
                if v is None:
                    return "N/A"
                sign = "+" if v >= 0 else ""
                return f"{sign}{v:.1f}%"

            lines.append("| Metric | Value | QoQ Growth | YoY Growth |")
            lines.append("|--------|-------|------------|------------|")

            # Revenue
            rev_qoq = comparison.revenue_growth_qoq
            rev_yoy = comparison.revenue_growth_yoy
            lines.append(f"| **Revenue** | {fmt_lakhs(latest.net_sales)} | {fmt_growth(rev_qoq)} | {fmt_growth(rev_yoy)} |")

            # Net Profit
            profit_qoq = comparison.profit_growth_qoq
            profit_yoy = comparison.profit_growth_yoy
            lines.append(f"| **Net Profit** | {fmt_lakhs(latest.net_profit)} | {fmt_growth(profit_qoq)} | {fmt_growth(profit_yoy)} |")

            # EPS
            eps = latest.basic_eps_continuing or latest.basic_eps
            if eps is not None:
                lines.append(f"| **EPS** | ₹{eps:.2f} | - | - |")

            # Margins
            if latest.net_profit_margin is not None:
                lines.append(f"| **Net Profit Margin** | {latest.net_profit_margin:.1f}% | - | - |")

            if latest.ebitda is not None:
                lines.append(f"| **EBITDA** | {fmt_lakhs(latest.ebitda)} | - | - |")

            lines.append("")

        # Quarterly trend table
        if len(comparison.periods) > 1:
            lines.append("## Quarterly Trend")
            lines.append("*(All values in ₹ Lakhs)*")
            lines.append("")

            # Table header
            header = "| Quarter | Revenue | Net Profit | EPS | NPM % |"
            separator = "|---------|---------|------------|-----|-------|"
            lines.append(header)
            lines.append(separator)

            for p in comparison.periods[:8]:
                quarter = p.quarter or p.period_label
                revenue = f"{p.net_sales:,.0f}" if p.net_sales else "-"
                profit = f"{p.net_profit:,.0f}" if p.net_profit else "-"
                eps = p.basic_eps_continuing or p.basic_eps
                eps_str = f"{eps:.2f}" if eps else "-"
                margin = f"{p.net_profit_margin:.1f}" if p.net_profit_margin else "-"
                audited = " ✓" if p.is_audited else ""

                lines.append(f"| {quarter}{audited} | {revenue} | {profit} | {eps_str} | {margin} |")

            lines.append("")
            lines.append("*✓ = Audited*")
            lines.append("")

        # Expense breakdown for latest quarter
        if latest and latest.total_expenses:
            lines.append("## Expense Breakdown (Latest Quarter)")
            lines.append("")
            lines.append("| Expense Item | Amount (₹ Lakhs) | % of Revenue |")
            lines.append("|--------------|------------------|--------------|")

            def pct_of_rev(v: float | None) -> str:
                if v is None or latest.net_sales is None or latest.net_sales == 0:
                    return "-"
                return f"{(v / latest.net_sales) * 100:.1f}%"

            if latest.raw_material_consumed:
                lines.append(f"| Raw Materials | {latest.raw_material_consumed:,.0f} | {pct_of_rev(latest.raw_material_consumed)} |")
            if latest.staff_cost:
                lines.append(f"| Employee Cost | {latest.staff_cost:,.0f} | {pct_of_rev(latest.staff_cost)} |")
            if latest.depreciation:
                lines.append(f"| Depreciation | {latest.depreciation:,.0f} | {pct_of_rev(latest.depreciation)} |")
            if latest.interest_expense:
                lines.append(f"| Interest | {latest.interest_expense:,.0f} | {pct_of_rev(latest.interest_expense)} |")
            if latest.other_expenses:
                lines.append(f"| Other Expenses | {latest.other_expenses:,.0f} | {pct_of_rev(latest.other_expenses)} |")
            if latest.total_expenses:
                lines.append(f"| **Total** | **{latest.total_expenses:,.0f}** | {pct_of_rev(latest.total_expenses)} |")

            lines.append("")

        # Financial ratios
        if latest:
            has_ratios = any([
                latest.debt_equity_ratio,
                latest.interest_service_coverage,
                latest.debt_service_coverage,
            ])
            if has_ratios:
                lines.append("## Financial Ratios")
                lines.append("")
                if latest.debt_equity_ratio is not None:
                    lines.append(f"- **Debt/Equity Ratio:** {latest.debt_equity_ratio:.2f}")
                if latest.interest_service_coverage is not None:
                    lines.append(f"- **Interest Service Coverage:** {latest.interest_service_coverage:.2f}")
                if latest.debt_service_coverage is not None:
                    lines.append(f"- **Debt Service Coverage:** {latest.debt_service_coverage:.2f}")
                lines.append("")

        return "\n".join(lines)

    def get_financial_results_comparison(self, symbol: str, num_quarters: int = 8) -> str:
        """Get quarterly financial results comparison for a company.

        This tool fetches detailed financial data across multiple quarters,
        making it easy to compare revenue, profit, expenses, EPS, and margins.

        The output includes:
        - Latest quarter summary with key metrics
        - Quarter-over-quarter (QoQ) and year-over-year (YoY) growth
        - Quarterly trend table (revenue, profit, EPS, margins)
        - Expense breakdown
        - Financial ratios (if available)

        Use this when you need to analyze financial performance trends.

        Args:
            symbol: Stock symbol (e.g., "RELIANCE", "TCS", "INFY")
            num_quarters: Number of quarters to show (default: 8)

        Returns:
            Markdown formatted financial results comparison
        """
        try:
            comparison = self.client.get_financial_results_comparison(symbol)
            if not comparison.periods:
                return f"No financial results data found for {symbol}"
            # Limit periods
            comparison.periods = comparison.periods[:num_quarters]
            return self._format_financial_comparison(comparison)
        except Exception as e:
            return f"Error fetching financial results for {symbol}: {str(e)}"

    def _format_oi_spurts(self, response: OISpurtsResponse, show_type: str = "all") -> str:
        """Format OI spurts data as markdown.

        Args:
            response: OISpurtsResponse object
            show_type: "all", "gainers", or "losers"

        Returns:
            Markdown formatted string
        """
        lines = []
        lines.append("# OI Spurts - Open Interest Changes")
        lines.append("")

        if not response.data:
            lines.append("No OI spurt data available.")
            return "\n".join(lines)

        def fmt_value(v: float) -> str:
            """Format value in lakhs/crores."""
            if abs(v) >= 10000000:
                return f"₹{v / 100:.0f} Cr"
            elif abs(v) >= 100000:
                return f"₹{v / 100:.0f} Cr"
            else:
                return f"₹{v:,.0f} L"

        def fmt_oi(v: int) -> str:
            """Format OI value."""
            if v >= 10000000:
                return f"{v / 10000000:.2f}Cr"
            elif v >= 100000:
                return f"{v / 100000:.2f}L"
            else:
                return f"{v:,}"

        # OI Gainers (Buildup)
        if show_type in ("all", "gainers"):
            gainers = response.oi_gainers[:15]
            if gainers:
                lines.append("## OI Buildup (Increasing OI)")
                lines.append("*Stocks with significant increase in open interest - may indicate new positions being created*")
                lines.append("")
                lines.append("| Symbol | LTP | OI Change | % Change | Volume | Total Value |")
                lines.append("|--------|-----|-----------|----------|--------|-------------|")

                for d in gainers:
                    change_sign = "+" if d.change_in_oi > 0 else ""
                    lines.append(
                        f"| **{d.symbol}** | ₹{d.underlying_value:,.0f} | {change_sign}{fmt_oi(d.change_in_oi)} | +{d.avg_in_oi:.1f}% | {fmt_oi(d.volume)} | {fmt_value(d.total)} |"
                    )

                lines.append("")

        # OI Losers (Unwinding)
        if show_type in ("all", "losers"):
            losers = response.oi_losers[:15]
            if losers:
                lines.append("## OI Unwinding (Decreasing OI)")
                lines.append("*Stocks with significant decrease in open interest - may indicate positions being closed*")
                lines.append("")
                lines.append("| Symbol | LTP | OI Change | % Change | Volume | Total Value |")
                lines.append("|--------|-----|-----------|----------|--------|-------------|")

                for d in losers:
                    lines.append(
                        f"| **{d.symbol}** | ₹{d.underlying_value:,.0f} | {fmt_oi(d.change_in_oi)} | {d.avg_in_oi:.1f}% | {fmt_oi(d.volume)} | {fmt_value(d.total)} |"
                    )

                lines.append("")

        # Summary stats
        if show_type == "all":
            total_buildup = len(response.oi_gainers)
            total_unwinding = len(response.oi_losers)
            lines.append("## Summary")
            lines.append("")
            lines.append(f"- **Stocks with OI Buildup:** {total_buildup}")
            lines.append(f"- **Stocks with OI Unwinding:** {total_unwinding}")
            lines.append("")

        return "\n".join(lines)

    def get_oi_spurts(self, show_type: str = "all", limit: int = 15) -> str:
        """Get stocks with unusual changes in open interest (OI spurts).

        This tool shows stocks with significant changes in open interest,
        which can indicate unusual derivative activity. OI spurts are useful for:

        - **OI Buildup**: Increasing OI suggests new positions being created.
          Combined with price rise = Long buildup (bullish)
          Combined with price fall = Short buildup (bearish)

        - **OI Unwinding**: Decreasing OI suggests positions being closed.
          Combined with price fall = Long unwinding
          Combined with price rise = Short covering

        Args:
            show_type: What to show - "all" (default), "gainers" (OI buildup), or "losers" (OI unwinding)
            limit: Maximum number of stocks to show per category (default: 15)

        Returns:
            Markdown formatted table of OI spurts with:
            - Symbol and last traded price
            - Change in OI (absolute and percentage)
            - Trading volume
            - Total derivative value
        """
        try:
            response = self.client.get_oi_spurts()
            if not response.data:
                return "No OI spurt data available. This data is only available during market hours."
            return self._format_oi_spurts(response, show_type)
        except Exception as e:
            return f"Error fetching OI spurts: {str(e)}"

    def _format_most_active(
        self,
        equities: MostActiveResponse | None = None,
        sme: MostActiveSMEResponse | None = None,
        etf: MostActiveETFResponse | None = None,
        segment: str = "equities",
    ) -> str:
        """Format most active securities as markdown."""
        lines = []

        def fmt_value(v: float) -> str:
            """Format value in crores."""
            if v >= 10000000:
                return f"₹{v / 10000000:,.0f} Cr"
            elif v >= 100000:
                return f"₹{v / 100000:,.0f} L"
            else:
                return f"₹{v:,.0f}"

        def fmt_volume(v: int) -> str:
            """Format volume."""
            if v >= 10000000:
                return f"{v / 10000000:.2f}Cr"
            elif v >= 100000:
                return f"{v / 100000:.2f}L"
            else:
                return f"{v:,}"

        if segment == "equities" and equities and equities.equities:
            lines.append("# Most Active Equities")
            lines.append("")
            lines.append("| Symbol | LTP | Change | Volume | Value |")
            lines.append("|--------|-----|--------|--------|-------|")

            for e in equities.equities[:20]:
                change_sign = "+" if e.percent_change >= 0 else ""
                lines.append(
                    f"| **{e.symbol}** | ₹{e.last_price:,.2f} | {change_sign}{e.percent_change:.2f}% | {fmt_volume(e.total_traded_volume)} | {fmt_value(e.total_traded_value)} |"
                )
            lines.append("")

            if equities.timestamp:
                lines.append(f"*Last updated: {equities.timestamp}*")
                lines.append("")

        elif segment == "sme" and sme and sme.data:
            lines.append("# Most Active SME Stocks")
            lines.append("")
            lines.append("| Symbol | LTP | Change | Volume | Value |")
            lines.append("|--------|-----|--------|--------|-------|")

            for s in sme.data[:20]:
                change_sign = "+" if s.percent_change >= 0 else ""
                lines.append(
                    f"| **{s.symbol}** | ₹{s.last_price:,.2f} | {change_sign}{s.percent_change:.2f}% | {fmt_volume(s.total_traded_volume)} | {fmt_value(s.total_traded_value)} |"
                )
            lines.append("")

            if sme.timestamp:
                lines.append(f"*Last updated: {sme.timestamp}*")
                lines.append("")

        elif segment == "etf" and etf and etf.data:
            lines.append("# Most Active ETFs")
            lines.append("")
            lines.append("| Symbol | LTP | Change | Volume | Value | NAV | Prem/Disc |")
            lines.append("|--------|-----|--------|--------|-------|-----|-----------|")

            for e in etf.data[:20]:
                change_sign = "+" if e.percent_change >= 0 else ""
                nav_str = f"₹{e.nav:.2f}" if e.nav else "-"
                prem_disc = e.premium_discount
                prem_disc_str = f"{prem_disc:+.2f}%" if prem_disc is not None else "-"
                lines.append(
                    f"| **{e.symbol}** | ₹{e.last_price:,.2f} | {change_sign}{e.percent_change:.2f}% | {fmt_volume(e.total_traded_volume)} | {fmt_value(e.total_traded_value)} | {nav_str} | {prem_disc_str} |"
                )
            lines.append("")

            if etf.timestamp:
                lines.append(f"*Last updated: {etf.timestamp}*")
                lines.append("")

        if not lines:
            return "No data available for this segment."

        return "\n".join(lines)

    def get_most_active(self, segment: str = "equities", sort_by: str = "value") -> str:
        """Get most active securities by trading activity.

        This tool shows the most actively traded securities on NSE,
        useful for identifying:
        - High liquidity stocks with significant trading volume
        - Stocks with institutional interest (high value trades)
        - Market momentum and participation

        Args:
            segment: Market segment - "equities" (default), "sme", or "etf"
            sort_by: Sort criteria - "value" (default) or "volume"

        Returns:
            Markdown formatted table of most active securities with:
            - Symbol and last traded price
            - Percentage change
            - Trading volume and value
            - NAV and premium/discount (for ETFs only)
        """
        try:
            if segment == "equities":
                response = self.client.get_most_active_equities(sort_by=sort_by)
                if not response.equities:
                    return "No most active equities data available."
                return self._format_most_active(equities=response, segment="equities")

            elif segment == "sme":
                response = self.client.get_most_active_sme(sort_by=sort_by)
                if not response.data:
                    return "No most active SME data available."
                return self._format_most_active(sme=response, segment="sme")

            elif segment == "etf":
                response = self.client.get_most_active_etf(sort_by=sort_by)
                if not response.data:
                    return "No most active ETF data available."
                return self._format_most_active(etf=response, segment="etf")

            else:
                return f"Invalid segment: {segment}. Valid options: equities, sme, etf"

        except Exception as e:
            return f"Error fetching most active {segment}: {str(e)}"

    def _format_market_movers(
        self,
        gainers: PriceVariationsResponse | None = None,
        losers: PriceVariationsResponse | None = None,
        volume_gainers: VolumeGainersResponse | None = None,
        mover_type: str = "all",
    ) -> str:
        """Format market movers (gainers/losers/volume) as markdown."""
        lines = []
        lines.append("# Market Movers")
        lines.append("")

        def fmt_value(v: float) -> str:
            """Format value in crores."""
            if v >= 10000000:
                return f"₹{v / 10000000:,.0f} Cr"
            elif v >= 100000:
                return f"₹{v / 100000:,.0f} L"
            else:
                return f"₹{v:,.0f}"

        # Price Gainers
        if mover_type in ("all", "gainers") and gainers and gainers.data:
            lines.append("## Top Gainers")
            lines.append("")
            lines.append("| Symbol | LTP | Change | Open | High | Low | Turnover |")
            lines.append("|--------|-----|--------|------|------|-----|----------|")

            for g in gainers.data[:15]:
                lines.append(
                    f"| **{g.symbol}** | ₹{g.ltp:,.2f} | +{g.percent_change:.2f}% | ₹{g.open_price:,.2f} | ₹{g.high_price:,.2f} | ₹{g.low_price:,.2f} | {fmt_value(g.turnover)} |"
                )
            lines.append("")

        # Price Losers
        if mover_type in ("all", "losers") and losers and losers.data:
            lines.append("## Top Losers")
            lines.append("")
            lines.append("| Symbol | LTP | Change | Open | High | Low | Turnover |")
            lines.append("|--------|-----|--------|------|------|-----|----------|")

            for l in losers.data[:15]:
                lines.append(
                    f"| **{l.symbol}** | ₹{l.ltp:,.2f} | {l.percent_change:.2f}% | ₹{l.open_price:,.2f} | ₹{l.high_price:,.2f} | ₹{l.low_price:,.2f} | {fmt_value(l.turnover)} |"
                )
            lines.append("")

        # Volume Gainers
        if mover_type in ("all", "volume") and volume_gainers and volume_gainers.data:
            lines.append("## Volume Spurts")
            lines.append("*Stocks with unusual volume compared to weekly average*")
            lines.append("")
            lines.append("| Symbol | LTP | Price Chg | Volume | 1W Avg | Vol Spike |")
            lines.append("|--------|-----|-----------|--------|--------|-----------|")

            for v in volume_gainers.data[:15]:
                change_sign = "+" if v.percent_change >= 0 else ""
                lines.append(
                    f"| **{v.symbol}** | ₹{v.ltp:,.2f} | {change_sign}{v.percent_change:.2f}% | {v.volume:,} | {v.week1_avg_volume:,} | {v.week1_vol_change:.1f}x |"
                )
            lines.append("")

        if len(lines) <= 2:
            return "No market mover data available."

        return "\n".join(lines)

    def get_market_movers(self, mover_type: str = "all", min_change: int = 5) -> str:
        """Get market movers - top gainers, losers, and volume spurts.

        This tool shows stocks with significant price or volume movements,
        useful for identifying:
        - Stocks making big moves (breakouts/breakdowns)
        - Momentum opportunities
        - Unusual activity that may signal news or events

        Args:
            mover_type: Type of movers - "all" (default), "gainers", "losers", or "volume"
            min_change: Minimum percentage change for gainers/losers (default: 5)
                Options: 2, 5, 10, 20

        Returns:
            Markdown formatted tables showing:
            - Top Gainers: Stocks with highest price increase
            - Top Losers: Stocks with highest price decrease
            - Volume Spurts: Stocks with unusual volume vs weekly average
        """
        try:
            gainers = None
            losers = None
            volume_gainers = None

            if mover_type in ("all", "gainers"):
                gainers = self.client.get_price_gainers(min_change=min_change)

            if mover_type in ("all", "losers"):
                losers = self.client.get_price_losers(min_change=min_change)

            if mover_type in ("all", "volume"):
                volume_gainers = self.client.get_volume_gainers()

            return self._format_market_movers(
                gainers=gainers,
                losers=losers,
                volume_gainers=volume_gainers,
                mover_type=mover_type,
            )

        except Exception as e:
            return f"Error fetching market movers: {str(e)}"

    def _format_number(self, value: float | int | str | None, decimals: int = 2) -> str:
        """Format a number with commas and optional decimal places."""
        if value is None:
            return "N/A"
        try:
            num = float(value)
            if num >= 1e12:
                return f"{num / 1e12:,.{decimals}f}T"
            elif num >= 1e9:
                return f"{num / 1e9:,.{decimals}f}B"
            elif num >= 1e7:
                return f"{num / 1e7:,.{decimals}f}Cr"
            elif num >= 1e5:
                return f"{num / 1e5:,.{decimals}f}L"
            else:
                return f"{num:,.{decimals}f}"
        except (ValueError, TypeError):
            return str(value) if value else "N/A"

    def _format_percent(self, value: float | int | str | None) -> str:
        """Format a percentage value."""
        if value is None:
            return "N/A"
        try:
            num = float(value)
            sign = "+" if num > 0 else ""
            return f"{sign}{num:.2f}%"
        except (ValueError, TypeError):
            return str(value) if value else "N/A"

    def _format_summary_markdown(self, data: dict[str, Any]) -> str:
        """Format symbol data as a markdown summary."""
        lines = []

        # Extract data
        symbol_name = data.get("symbol_name", {})
        metadata = data.get("metadata", {})
        symbol_data = data.get("symbol_data", {})
        shareholding = data.get("shareholding", {})
        financials = data.get("financials", [])
        integrated_filing = data.get("integrated_filing", [])
        yearwise = data.get("yearwise", [])
        announcements = data.get("announcements", [])
        corp_actions = data.get("corp_actions", [])
        board_meetings = data.get("board_meetings", [])
        annual_reports = data.get("annual_reports", [])
        brsr_reports = data.get("brsr_reports", [])
        index_list = data.get("index_list", [])
        upcoming_events = data.get("upcoming_events", [])

        # Derivatives data (only for F&O stocks)
        derivatives_filter = data.get("derivatives_filter", {})
        derivatives_data = data.get("derivatives_data", {})
        most_active_calls = data.get("most_active_calls", {})
        most_active_puts = data.get("most_active_puts", {})
        most_active_by_oi = data.get("most_active_by_oi", {})
        option_chain = data.get("option_chain", {})
        option_chain_dropdown = data.get("option_chain_dropdown", {})

        # Extract equity response
        equity = {}
        if symbol_data and "equityResponse" in symbol_data:
            equity_list = symbol_data.get("equityResponse", [])
            if equity_list:
                equity = equity_list[0]

        meta = equity.get("metaData", {})
        trade_info = equity.get("tradeInfo", {})
        price_info = equity.get("priceInfo", {})
        sec_info = equity.get("secInfo", {})

        # Header
        company = symbol_name.get("companyName", metadata.get("companyName", "Unknown"))
        symbol = symbol_name.get("symbol", metadata.get("symbol", ""))
        lines.append(f"# {company} ({symbol})")
        lines.append("")

        # Basic info
        isin = metadata.get("isin", "N/A")
        is_fno = "Yes" if metadata.get("isFNOSec") == "true" else "No"
        sector = sec_info.get("sector", "N/A")
        industry = sec_info.get("basicIndustry", "N/A")
        index = sec_info.get("index", "N/A")

        lines.append(f"**ISIN:** {isin} | **F&O:** {is_fno} | **Sector:** {sector}")
        lines.append(f"**Industry:** {industry} | **Index:** {index}")
        lines.append("")

        # Price section
        lines.append("## Price & Trading")
        lines.append("")

        last_price = meta.get("closePrice") or meta.get("lastPrice", 0)
        change = meta.get("change", 0)
        pchange = meta.get("pChange", 0)
        prev_close = meta.get("previousClose", 0)
        open_price = meta.get("open", 0)
        day_high = meta.get("dayHigh", 0)
        day_low = meta.get("dayLow", 0)

        change_emoji = "🟢" if float(change) >= 0 else "🔴"
        lines.append(
            f"**Last Price:** ₹{self._format_number(last_price)} {change_emoji} {self._format_percent(pchange)}"
        )
        lines.append(f"**Open:** ₹{self._format_number(open_price)} | **Prev Close:** ₹{self._format_number(prev_close)}")
        lines.append(f"**Day Range:** ₹{self._format_number(day_low)} - ₹{self._format_number(day_high)}")
        lines.append("")

        # 52 week high/low
        year_high = price_info.get("yearHigh", 0)
        year_low = price_info.get("yearLow", 0)
        year_high_dt = price_info.get("yearHightDt", "").split(" ")[0] if price_info.get("yearHightDt") else ""
        year_low_dt = price_info.get("yearLowDt", "").split(" ")[0] if price_info.get("yearLowDt") else ""

        lines.append(f"**52W High:** ₹{self._format_number(year_high)} ({year_high_dt})")
        lines.append(f"**52W Low:** ₹{self._format_number(year_low)} ({year_low_dt})")
        lines.append("")

        # Volume & Market Cap
        volume = trade_info.get("totalTradedVolume", 0)
        value = trade_info.get("totalTradedValue", 0)
        market_cap = trade_info.get("totalMarketCap", 0)
        ffmc = trade_info.get("ffmc", 0)
        delivery_pct = trade_info.get("deliveryToTradedQuantity", 0)

        lines.append(f"**Volume:** {self._format_number(volume, 0)} | **Value:** ₹{self._format_number(value)}")
        lines.append(f"**Market Cap:** ₹{self._format_number(market_cap)} | **FF Market Cap:** ₹{self._format_number(ffmc)}")
        lines.append(f"**Delivery %:** {self._format_percent(delivery_pct).replace('+', '')}")
        lines.append("")

        # PE ratio
        pe = sec_info.get("pdSymbolPe", "N/A")
        sector_pe = sec_info.get("pdSectorPe", "N/A")
        lines.append(f"**P/E Ratio:** {pe} | **Sector P/E:** {sector_pe}")
        lines.append("")

        # Performance section
        if yearwise:
            lines.append("## Performance")
            lines.append("")
            perf = yearwise[0] if isinstance(yearwise, list) else yearwise

            lines.append("| Period | Stock | Index |")
            lines.append("|--------|-------|-------|")

            periods = [
                ("1D", "yesterday_chng_per", "index_yesterday_chng_per"),
                ("1W", "one_week_chng_per", "index_one_week_chng_per"),
                ("1M", "one_month_chng_per", "index_one_month_chng_per"),
                ("3M", "three_month_chng_per", "index_three_month_chng_per"),
                ("6M", "six_month_chng_per", "index_six_month_chng_per"),
                ("1Y", "one_year_chng_per", "index_one_year_chng_per"),
                ("3Y", "three_year_chng_per", "index_three_year_chng_per"),
                ("5Y", "five_year_chng_per", "index_five_year_chng_per"),
            ]

            for label, stock_key, index_key in periods:
                stock_val = perf.get(stock_key)
                index_val = perf.get(index_key)
                if stock_val is not None:
                    lines.append(
                        f"| {label} | {self._format_percent(stock_val)} | {self._format_percent(index_val)} |"
                    )

            index_name = perf.get("index_name", "NIFTY 50")
            lines.append(f"\n*Compared with {index_name}*")
            lines.append("")

        # Shareholding section
        if shareholding:
            lines.append("## Shareholding Pattern")
            lines.append("")

            # Get the most recent shareholding
            dates = list(shareholding.keys())
            if dates:
                latest_date = dates[0]
                latest = shareholding[latest_date]
                promoter = latest.get("promoter_group", {}).get("value", "N/A")
                public = latest.get("public", {}).get("value", "N/A")

                lines.append(f"*As of {latest_date}*")
                lines.append(f"- **Promoter & Promoter Group:** {promoter}%")
                lines.append(f"- **Public:** {public}%")
                lines.append("")

        # Financial Status
        if financials:
            lines.append("## Recent Financials")
            lines.append("*(Values in ₹ Lakhs)*")
            lines.append("")

            lines.append("| Quarter | Total Income | Net Profit | EPS |")
            lines.append("|---------|--------------|------------|-----|")

            for fin in financials[:4]:
                quarter = fin.get("to_date_MonYr", "N/A")
                income = fin.get("totalIncome")
                profit = fin.get("netProLossAftTax")
                eps = fin.get("eps", "N/A")
                audited = "✓" if fin.get("audited") == "Audited" else ""

                # Format as plain numbers with commas for readability
                income_str = f"{int(income):,}" if income else "N/A"
                profit_str = f"{int(profit):,}" if profit else "N/A"

                lines.append(f"| {quarter} {audited} | {income_str} | {profit_str} | {eps} |")

            lines.append("")

        # Integrated Filing Data (Consolidated vs Standalone)
        if integrated_filing:
            lines.append("## Consolidated Financials")
            lines.append("*(Values in ₹ Lakhs)*")
            lines.append("")

            # Filter for consolidated results
            consolidated = [f for f in integrated_filing if f.get("gfrConsolidated") == "Consolidated"][:4]

            if consolidated:
                lines.append("| Quarter | Total Income | Net Profit | EPS |")
                lines.append("|---------|--------------|------------|-----|")

                for fin in consolidated:
                    quarter = fin.get("gfrQuaterEnded", "N/A")
                    income = fin.get("gfrTotalIncome")
                    profit = fin.get("gfrNetProLoss")
                    eps = fin.get("gfrErnPerShare", "N/A")
                    audited = "✓" if fin.get("gfrAuditedUnaudited") == "Audited" else ""

                    income_str = f"{int(income):,}" if income else "N/A"
                    profit_str = f"{int(profit):,}" if profit else "N/A"

                    lines.append(f"| {quarter} {audited} | {income_str} | {profit_str} | {eps} |")

                lines.append("")

        # Derivatives Section (only for F&O stocks)
        if derivatives_data and derivatives_data.get("data"):
            lines.append("## Derivatives")
            lines.append("")

            # Get expiry dates
            expiry_dates = derivatives_filter.get("expiryDate", [])
            if expiry_dates:
                lines.append(f"**Expiry Dates:** {', '.join(expiry_dates[:3])}")
                lines.append("")

            # Futures data
            futures = [d for d in derivatives_data.get("data", []) if d.get("instrumentType") == "FUTSTK"]
            if futures:
                fut = futures[0]  # Near month futures
                lines.append("### Futures (Near Month)")
                lines.append("")
                lines.append(f"**Last Price:** ₹{self._format_number(fut.get('lastPrice'))}")
                lines.append(f"**Change:** {self._format_percent(fut.get('pchange'))}")
                lines.append(f"**Open Interest:** {self._format_number(fut.get('openInterest'), 0)}")
                lines.append(f"**OI Change:** {self._format_percent(fut.get('pchangeinOpenInterest'))}")
                lines.append(f"**Volume:** {self._format_number(fut.get('totalTradedVolume'), 0)}")
                lines.append("")

            # Most Active by OI
            oi_data = most_active_by_oi.get("data", [])
            if oi_data:
                lines.append("### Most Active by Open Interest")
                lines.append("")
                lines.append("| Contract | LTP | Change |")
                lines.append("|----------|-----|--------|")
                for item in oi_data[:5]:
                    contract = item.get("contract", "N/A")
                    ltp = item.get("lastPrice", 0)
                    pchange = item.get("perChange", 0)
                    lines.append(f"| {contract} | ₹{ltp:.2f} | {self._format_percent(pchange)} |")
                lines.append("")

            # Most Active Calls
            calls_data = most_active_calls.get("data", [])
            if calls_data:
                lines.append("### Most Active Calls")
                lines.append("")
                lines.append("| Contract | LTP | Change |")
                lines.append("|----------|-----|--------|")
                for opt in calls_data[:5]:
                    contract = opt.get("contract", "N/A")
                    ltp = opt.get("lastPrice", 0)
                    pchange = opt.get("perChange", 0)
                    lines.append(f"| {contract} | ₹{ltp:.2f} | {self._format_percent(pchange)} |")
                lines.append("")

            # Most Active Puts
            puts_data = most_active_puts.get("data", [])
            if puts_data:
                lines.append("### Most Active Puts")
                lines.append("")
                lines.append("| Contract | LTP | Change |")
                lines.append("|----------|-----|--------|")
                for opt in puts_data[:5]:
                    contract = opt.get("contract", "N/A")
                    ltp = opt.get("lastPrice", 0)
                    pchange = opt.get("perChange", 0)
                    lines.append(f"| {contract} | ₹{ltp:.2f} | {self._format_percent(pchange)} |")
                lines.append("")

            # Option Chain Summary
            if option_chain and option_chain.get("data"):
                chain_data = option_chain.get("data", [])
                underlying_value = option_chain.get("underlyingValue", 0)

                # Calculate PCR (Put-Call Ratio) and find max OI strikes
                total_call_oi = 0
                total_put_oi = 0
                max_call_oi = 0
                max_call_oi_strike = 0
                max_put_oi = 0
                max_put_oi_strike = 0
                atm_strike = None
                atm_data = None

                for item in chain_data:
                    strike = item.get("strikePrice", 0)
                    ce = item.get("CE", {})
                    pe = item.get("PE", {})

                    ce_oi = ce.get("openInterest", 0) or 0
                    pe_oi = pe.get("openInterest", 0) or 0

                    total_call_oi += ce_oi
                    total_put_oi += pe_oi

                    if ce_oi > max_call_oi:
                        max_call_oi = ce_oi
                        max_call_oi_strike = strike

                    if pe_oi > max_put_oi:
                        max_put_oi = pe_oi
                        max_put_oi_strike = strike

                    # Find ATM strike (closest to underlying)
                    if atm_strike is None or abs(strike - underlying_value) < abs(atm_strike - underlying_value):
                        atm_strike = strike
                        atm_data = item

                pcr = total_put_oi / total_call_oi if total_call_oi > 0 else 0

                lines.append("### Option Chain Summary")
                lines.append("")
                lines.append(f"**Underlying:** ₹{underlying_value}")
                lines.append(f"**PCR (OI):** {pcr:.2f}")
                lines.append(f"**Max Call OI:** {self._format_number(max_call_oi, 0)} @ ₹{max_call_oi_strike}")
                lines.append(f"**Max Put OI:** {self._format_number(max_put_oi, 0)} @ ₹{max_put_oi_strike}")
                lines.append("")

                # ATM Options
                if atm_data:
                    atm_ce = atm_data.get("CE", {})
                    atm_pe = atm_data.get("PE", {})
                    lines.append(f"**ATM Strike:** ₹{atm_strike}")
                    lines.append(f"- CE: ₹{atm_ce.get('lastPrice', 0):.2f} | OI: {self._format_number(atm_ce.get('openInterest', 0), 0)} | IV: {atm_ce.get('impliedVolatility', 0):.1f}%")
                    lines.append(f"- PE: ₹{atm_pe.get('lastPrice', 0):.2f} | OI: {self._format_number(atm_pe.get('openInterest', 0), 0)} | IV: {atm_pe.get('impliedVolatility', 0):.1f}%")
                    lines.append("")

                timestamp = most_active_calls.get("timestamp", "")
                if timestamp:
                    lines.append(f"*Options data as of {timestamp}*")
                lines.append("")

        # Corporate Actions
        if corp_actions:
            lines.append("## Recent Corporate Actions")
            lines.append("")

            for action in corp_actions[:3]:
                subject = action.get("subject", "N/A")
                ex_date = action.get("exDate", "N/A")
                lines.append(f"- **{subject}** (Ex-Date: {ex_date})")

            lines.append("")

        # Recent Announcements
        if announcements:
            lines.append("## Recent Announcements")
            lines.append("")

            for ann in announcements[:3]:
                desc = ann.get("desc", "N/A")
                date_str = ann.get("an_dt", "").split(" ")[0] if ann.get("an_dt") else "N/A"
                lines.append(f"- **{desc}** ({date_str})")

            lines.append("")

        # Board Meetings
        if board_meetings:
            lines.append("## Board Meetings")
            lines.append("")

            for meeting in board_meetings[:2]:
                date_str = meeting.get("bm_date", "N/A")
                purpose = meeting.get("bm_purpose", "N/A")
                lines.append(f"- **{date_str}:** {purpose}")

            lines.append("")

        # Upcoming Events
        if upcoming_events:
            lines.append("## Upcoming Events")
            lines.append("")

            for event in upcoming_events[:5]:
                event_date = event.event_date.strftime("%d-%b-%Y")
                purpose = event.purpose
                lines.append(f"- **{event_date}:** {purpose}")

            lines.append("")

        # Annual Reports
        if annual_reports:
            lines.append("## Annual Reports")
            lines.append("")

            for report in annual_reports[:3]:
                fy = f"FY {report.get('fromYr', '')}-{report.get('toYr', '')}"
                url = report.get("fileName", "")
                date_str = report.get("broadcast_dttm", "").split(" ")[0] if report.get("broadcast_dttm") else ""
                if url and url != "-":
                    lines.append(f"- [{fy}]({url}) ({date_str})")
                else:
                    lines.append(f"- {fy} ({date_str})")

            lines.append("")

        # BRSR Reports
        if brsr_reports:
            lines.append("## BRSR Reports")
            lines.append("")

            for report in brsr_reports[:3]:
                fy = f"FY {report.get('fyFrom', '')}-{report.get('fyTo', '')}"
                url = report.get("attachmentFile", "")
                date_str = report.get("submissionDate", "").split(" ")[0] if report.get("submissionDate") else ""
                if url:
                    lines.append(f"- [{fy}]({url}) ({date_str})")
                else:
                    lines.append(f"- {fy} ({date_str})")

            lines.append("")

        # Index membership
        if index_list:
            display_indices = index_list[:10]
            if display_indices:
                lines.append("## Index Membership")
                lines.append("")
                lines.append(", ".join(display_indices))
                if len(index_list) > 10:
                    lines.append(f"*...and {len(index_list) - 10} more*")
                lines.append("")

        # Last update time
        last_update = equity.get("lastUpdateTime", "")
        if last_update:
            lines.append(f"---\n*Last updated: {last_update}*")

        return "\n".join(lines)

    def _format_price_band_hitters(
        self,
        response: Any,
        band_type: str = "both",
        limit: int = 20,
    ) -> str:
        """Format price band hitters as markdown.

        Args:
            response: PriceBandResponse from client
            band_type: 'upper', 'lower', or 'both'
            limit: Maximum stocks to show per band

        Returns:
            Markdown formatted string
        """
        from .models.price_band import PriceBandHitter, PriceBandResponse

        if not isinstance(response, PriceBandResponse):
            return "Error: Invalid response format"

        lines = ["# Price Band Hitters", ""]
        lines.append("*Stocks at circuit limits (upper/lower price bands)*")
        lines.append("")

        # Summary counts
        if response.count:
            lines.append("## Summary")
            lines.append(f"- **Upper Circuit:** {response.count.upper}")
            lines.append(f"- **Lower Circuit:** {response.count.lower}")
            lines.append(f"- **Total:** {response.count.total}")
            lines.append("")

        def format_band_table(hitters: list[PriceBandHitter], band_name: str) -> list[str]:
            """Format a band's data as table."""
            table_lines = [f"## {band_name} Circuit", ""]

            if not hitters:
                table_lines.append(f"*No stocks at {band_name.lower()} circuit*")
                table_lines.append("")
                return table_lines

            table_lines.append(f"| Symbol | LTP | Change% | Band | Volume | Turnover(Cr) |")
            table_lines.append("|--------|-----|---------|------|--------|--------------|")

            for h in hitters[:limit]:
                change_emoji = "🔺" if h.percent_change > 0 else "🔻"
                turnover_cr = h.turnover / 100  # lakhs to crores
                table_lines.append(
                    f"| {h.symbol} | {h.ltp:,.2f} | {change_emoji}{h.percent_change:+.2f}% | {h.price_band} | {h.total_traded_volume:,} | {turnover_cr:,.2f} |"
                )

            if len(hitters) > limit:
                table_lines.append(f"| *...and {len(hitters) - limit} more* | | | | | |")

            table_lines.append("")
            return table_lines

        # Upper band
        if band_type in ["upper", "both"]:
            lines.extend(format_band_table(response.upper.all_securities, "Upper"))

        # Lower band
        if band_type in ["lower", "both"]:
            lines.extend(format_band_table(response.lower.all_securities, "Lower"))

        # High turnover section
        upper_large = response.upper.securities_gt_20cr
        lower_large = response.lower.securities_gt_20cr

        if upper_large or lower_large:
            lines.append("## High Turnover (>20 Cr)")
            lines.append("")

            if upper_large:
                lines.append("**Upper Circuit (High Turnover):**")
                for h in upper_large[:5]:
                    turnover_cr = h.turnover / 100
                    lines.append(f"- {h.symbol}: ₹{h.ltp:,.2f} ({h.percent_change:+.2f}%) - Turnover: ₹{turnover_cr:,.2f}Cr")
                lines.append("")

            if lower_large:
                lines.append("**Lower Circuit (High Turnover):**")
                for h in lower_large[:5]:
                    turnover_cr = h.turnover / 100
                    lines.append(f"- {h.symbol}: ₹{h.ltp:,.2f} ({h.percent_change:+.2f}%) - Turnover: ₹{turnover_cr:,.2f}Cr")
                lines.append("")

        if response.timestamp:
            lines.append(f"---\n*Last updated: {response.timestamp}*")

        return "\n".join(lines)

    def get_price_band_hitters(
        self,
        band_type: str = "both",
        min_turnover: int = 0,
        limit: int = 20,
    ) -> str:
        """Get stocks hitting upper or lower price bands (circuit limits).

        This tool returns stocks that have hit their circuit limits during
        the trading session. Useful for identifying:
        - Stocks with extreme momentum (upper circuit = maximum allowed gain)
        - Stocks under heavy selling pressure (lower circuit = maximum allowed loss)
        - Potential breakout or breakdown candidates

        Args:
            band_type: Which band to show
                - "both": Show both upper and lower circuit stocks (default)
                - "upper": Show only upper circuit stocks
                - "lower": Show only lower circuit stocks
            min_turnover: Minimum turnover filter in crores
                - 0: All securities (default)
                - 10: Securities with turnover > 10 crores
                - 20: Securities with turnover > 20 crores
            limit: Maximum stocks to show per band (default 20)

        Returns:
            Markdown formatted table of stocks at circuit limits
        """
        try:
            response = self.client.get_price_band_hitters()
            return self._format_price_band_hitters(response, band_type, limit)
        except Exception as e:
            return f"Error fetching price band hitters: {str(e)}"

    def get_symbol_summary(self, symbol: str) -> str:
        """Get a comprehensive summary for a stock symbol.

        This tool fetches data from multiple NSE APIs and generates a nicely
        formatted markdown summary including:
        - Company info and metadata (ISIN, F&O status, sector, industry)
        - Current price and trading data (LTP, open, close, day range)
        - 52-week high/low with dates
        - Volume, market cap, delivery percentage
        - P/E ratio comparison with sector
        - Performance comparison with index (1D to 5Y returns)
        - Shareholding pattern (promoter vs public)
        - Recent financials (standalone quarterly results)
        - Consolidated financials (from integrated filings)
        - Derivatives data (futures, most active options) - for F&O stocks
        - Option chain summary (PCR, max OI strikes, ATM options) - for F&O stocks
        - Corporate actions (dividends, bonus, splits)
        - Recent announcements
        - Board meetings
        - Upcoming events (results, dividends, AGM, etc.)
        - Annual report links
        - BRSR (sustainability) report links
        - Index membership

        Args:
            symbol: Stock symbol (e.g., "RELIANCE", "TCS", "INFY", "BSE")

        Returns:
            Markdown formatted summary of the stock
        """
        try:
            data = self.client.get_symbol_summary_data(symbol)
            return self._format_summary_markdown(data)
        except Exception as e:
            return f"Error fetching summary for {symbol}: {str(e)}"

    def get_gift_nifty(self, show_history: bool = True, history_days: int = 10) -> str:
        """Get GIFT NIFTY (SGX NIFTY) current price and recent history.

        GIFT NIFTY trades on SGX (Singapore Exchange) for ~21 hours a day.
        It's a derivative of NIFTY 50 and provides price discovery for
        Indian markets before they open.

        Useful for:
        - Pre-market price indication for NIFTY 50
        - Gap up/down prediction for Indian markets
        - Global sentiment during off-market hours

        Args:
            show_history: If True, include recent daily OHLCV history
            history_days: Number of historical days to show (default: 10)

        Returns:
            Markdown formatted GIFT NIFTY summary with:
            - Current price and change
            - Day's high/low
            - Recent daily OHLCV history (if show_history=True)
        """
        try:
            lines = ["# GIFT NIFTY (SGX NIFTY)", ""]

            # Get current price
            current = self.client.get_gift_nifty_current()

            price = current.get("current")
            change = current.get("change")
            change_pct = current.get("change_percent")
            prev_close = current.get("prev_close")
            day_open = current.get("open")
            day_high = current.get("high")
            day_low = current.get("low")

            if price:
                change_emoji = "🟢" if (change and change >= 0) else "🔴"
                change_sign = "+" if (change and change >= 0) else ""

                lines.append("## Current Price")
                lines.append("")
                lines.append(f"**{price:,.2f}** {change_emoji} {change_sign}{change:,.2f} ({change_sign}{change_pct:.2f}%)")
                lines.append("")

                lines.append("## Today's Range")
                lines.append("")
                lines.append(f"| Open | High | Low | Prev Close |")
                lines.append("|------|------|-----|------------|")
                lines.append(
                    f"| {day_open:,.2f} | {day_high:,.2f} | {day_low:,.2f} | {prev_close:,.2f} |"
                )
                lines.append("")
            else:
                lines.append("*Unable to fetch current GIFT NIFTY price*")
                lines.append("")

            # Add history if requested
            if show_history:
                try:
                    df = self.client.get_gift_nifty_history(
                        resolution="1D", countback=history_days + 1, as_df=True
                    )

                    if not df.empty:
                        lines.append(f"## Recent History (Last {history_days} Days)")
                        lines.append("")
                        lines.append("| Date | Open | High | Low | Close | Change |")
                        lines.append("|------|------|------|-----|-------|--------|")

                        # Get last N+1 rows and calculate change
                        recent = df.tail(history_days + 1).copy()
                        recent["change"] = recent["close"].diff()
                        recent["change_pct"] = recent["close"].pct_change() * 100

                        # Skip first row (no change data) and iterate
                        for idx in recent.index[1:]:
                            row = recent.loc[idx]
                            date_str = idx.strftime("%Y-%m-%d")
                            chg = row["change"]
                            chg_pct = row["change_pct"]
                            chg_sign = "+" if chg >= 0 else ""
                            lines.append(
                                f"| {date_str} | {row['open']:,.0f} | {row['high']:,.0f} | "
                                f"{row['low']:,.0f} | {row['close']:,.0f} | {chg_sign}{chg_pct:.2f}% |"
                            )

                        lines.append("")
                except Exception:
                    pass  # Skip history on error

            lines.append("---")
            lines.append("*Data from MoneyControl / SGX*")

            return "\n".join(lines)

        except Exception as e:
            return f"Error fetching GIFT NIFTY data: {str(e)}"

    def get_index_constituents(self, index_name: str, limit: int = 50) -> str:
        """Get all constituents of an NSE index with their price data.

        This tool returns all stocks that are part of a given NSE index, including:
        - Stock symbol and company name
        - Current price and change percentage
        - Day's open, high, low
        - Volume and turnover
        - 52-week high/low proximity
        - Year-to-date and 30-day performance

        Use this to:
        - Get the list of stocks in NIFTY 50, NIFTY 100, NIFTY BANK, etc.
        - Screen index constituents by performance
        - Identify stocks near 52-week highs or lows

        Args:
            index_name: Index name (e.g., "NIFTY 50", "NIFTY BANK", "NIFTY 100", "NIFTY IT")
            limit: Maximum number of constituents to return (default 50)

        Returns:
            Markdown formatted table of index constituents with price data
        """
        try:
            response = self.client.get_index_constituents(index_name)

            if not response.data:
                return f"No constituents found for index: {index_name}"

            lines = [f"# {response.name} Constituents", ""]

            # Index summary
            if response.advance:
                adv = response.advance
                lines.append(f"**Advances:** {adv.advances} | **Declines:** {adv.declines} | **Unchanged:** {adv.unchanged}")
                lines.append("")

            # Constituents table
            lines.append("| Symbol | Company | LTP | Change% | Volume | 52W High% | 52W Low% | 1Y Ret% |")
            lines.append("|--------|---------|-----|---------|--------|-----------|----------|---------|")

            for c in response.data[:limit]:
                # Skip the index row itself
                if c.symbol == response.name or c.priority == 1:
                    continue

                symbol = c.symbol or "-"
                company = c.meta.company_name[:25] + "..." if c.meta and len(c.meta.company_name) > 25 else (c.meta.company_name if c.meta else "-")
                ltp = f"₹{c.last_price:,.2f}" if c.last_price else "-"
                pchange = f"{c.pchange:+.2f}%" if c.pchange is not None else "-"
                volume = self._format_volume(c.total_traded_volume) if c.total_traded_volume else "-"
                near_high = f"{c.near_wkh:.1f}%" if c.near_wkh is not None else "-"
                near_low = f"{c.near_wkl:.1f}%" if c.near_wkl is not None else "-"
                yearly_ret = f"{c.per_change_365d:+.1f}%" if c.per_change_365d is not None else "-"

                lines.append(f"| {symbol} | {company} | {ltp} | {pchange} | {volume} | {near_high} | {near_low} | {yearly_ret} |")

            lines.append("")
            lines.append(f"*Total constituents: {len(response.data) - 1}*")  # -1 for index row
            if response.timestamp:
                lines.append(f"*Last updated: {response.timestamp}*")

            return "\n".join(lines)

        except Exception as e:
            return f"Error fetching index constituents for {index_name}: {str(e)}"

    def _format_volume(self, volume: int | None) -> str:
        """Format volume in lakhs/crores."""
        if volume is None:
            return "-"
        if volume >= 10000000:
            return f"{volume / 10000000:.1f}Cr"
        elif volume >= 100000:
            return f"{volume / 100000:.1f}L"
        else:
            return f"{volume:,}"

    def get_index_symbols(self, index_name: str) -> str:
        """Get list of all stock symbols in an NSE index.

        This is a lightweight tool that returns just the symbols without price data.
        Useful for:
        - Getting a quick list of index members
        - Using as input for other tools (correlation, screening)
        - Checking if a stock belongs to an index

        Args:
            index_name: Index name (e.g., "NIFTY 50", "NIFTY BANK", "NIFTY 100")

        Returns:
            Comma-separated list of symbols in the index
        """
        try:
            symbols = self.client.get_index_symbols(index_name)

            if not symbols:
                return f"No symbols found for index: {index_name}"

            lines = [f"# {index_name} - Stock Symbols", ""]
            lines.append(f"**Total stocks:** {len(symbols)}")
            lines.append("")
            lines.append(", ".join(symbols))

            return "\n".join(lines)

        except Exception as e:
            return f"Error fetching index symbols for {index_name}: {str(e)}"

    def get_index_summary(self, index_name: str) -> str:
        """Get comprehensive summary for an NSE index.

        This tool provides a detailed overview of an index including:
        - Current price, change, and day's range
        - Valuation metrics (P/E, P/B, dividend yield)
        - Returns across multiple timeframes (1W to 5Y)
        - Top contributors (positive and negative)
        - Top gainers and losers in the index
        - Recent corporate announcements

        Useful for:
        - Getting market/sector overview
        - Understanding what's driving index movement
        - Identifying sector leaders and laggards

        Args:
            index_name: Index name (e.g., "NIFTY 50", "NIFTY BANK", "NIFTY IT")

        Returns:
            Markdown formatted comprehensive index summary
        """
        try:
            return self.client.get_index_summary_markdown(index_name)
        except Exception as e:
            return f"Error fetching index summary for {index_name}: {str(e)}"

    # Sector to Index mapping for fetch_sector_constituents
    SECTOR_INDEX_MAP = {
        # Banking & Finance
        "banking": "NIFTY BANK",
        "bank": "NIFTY BANK",
        "banks": "NIFTY BANK",
        "private bank": "NIFTY PRIVATE BANK",
        "psu bank": "NIFTY PSU BANK",
        "financial": "NIFTY FINANCIAL SERVICES",
        "financial services": "NIFTY FINANCIAL SERVICES",
        "nbfc": "NIFTY FINANCIAL SERVICES",
        # Technology
        "it": "NIFTY IT",
        "technology": "NIFTY IT",
        "tech": "NIFTY IT",
        "software": "NIFTY IT",
        # Healthcare
        "pharma": "NIFTY PHARMA",
        "pharmaceutical": "NIFTY PHARMA",
        "healthcare": "NIFTY HEALTHCARE INDEX",
        "hospital": "NIFTY HEALTHCARE INDEX",
        # Consumer
        "fmcg": "NIFTY FMCG",
        "consumer": "NIFTY FMCG",
        "consumer durables": "NIFTY CONSUMER DURABLES",
        # Industrial
        "auto": "NIFTY AUTO",
        "automobile": "NIFTY AUTO",
        "automotive": "NIFTY AUTO",
        "metal": "NIFTY METAL",
        "metals": "NIFTY METAL",
        "steel": "NIFTY METAL",
        "realty": "NIFTY REALTY",
        "real estate": "NIFTY REALTY",
        "energy": "NIFTY ENERGY",
        "power": "NIFTY ENERGY",
        "oil gas": "NIFTY OIL & GAS",
        "oil & gas": "NIFTY OIL & GAS",
        "infra": "NIFTY INFRASTRUCTURE",
        "infrastructure": "NIFTY INFRASTRUCTURE",
        "commodities": "NIFTY COMMODITIES",
        "commodity": "NIFTY COMMODITIES",
        # Public Sector
        "pse": "NIFTY PSE",
        "psu": "NIFTY PSE",
        "cpse": "NIFTY CPSE",
        # Media
        "media": "NIFTY MEDIA",
        # Broad Market
        "nifty50": "NIFTY 50",
        "nifty 50": "NIFTY 50",
        "nifty100": "NIFTY 100",
        "nifty 100": "NIFTY 100",
        "midcap": "NIFTY MIDCAP 100",
        "smallcap": "NIFTY SMALLCAP 100",
    }

    def scan_oi_spurts(self) -> str:
        """Scan OI spurts and categorize as bullish/bearish signals.

        This tool fetches OI spurt data and cross-references with price movements
        to categorize signals:

        **Signal Categories:**
        - **LONG BUILDUP** (Bullish): OI ↑ + Price ↑ = New longs being created
        - **SHORT BUILDUP** (Bearish): OI ↑ + Price ↓ = New shorts being created
        - **LONG UNWINDING** (Bearish): OI ↓ + Price ↓ = Longs closing positions
        - **SHORT COVERING** (Bullish): OI ↓ + Price ↑ = Shorts closing positions

        This is more actionable than raw OI data because it tells you
        the likely direction of smart money.

        Returns:
            Markdown formatted analysis with:
            - Categorized signals (bullish/bearish)
            - Top stocks in each category
            - Trading implications
        """
        try:
            # Fetch OI spurts
            oi_response = self.client.get_oi_spurts()
            if not oi_response.data:
                return "No OI spurt data available. This data is only available during market hours."

            # Fetch price changes from index constituents (covers F&O stocks)
            # NIFTY 500 provides the broadest coverage for F&O underlyings
            price_changes: dict[str, float] = {}

            # Helper to extract price changes from index response
            def add_price_data(response):
                for c in response.data:
                    if c.symbol and 'NIFTY' not in c.symbol.upper():
                        price_changes[c.symbol.upper()] = c.pchange

            # Get NIFTY 500 constituents (covers ~97% of F&O stocks)
            try:
                resp = self.client.get_nifty500_constituents()
                add_price_data(resp)
            except Exception:
                # Fallback to smaller indices if NIFTY 500 fails
                try:
                    add_price_data(self.client.get_nifty50_constituents())
                    add_price_data(self.client.get_nifty_next50_constituents())
                    add_price_data(self.client.get_nifty100_constituents())
                    add_price_data(self.client.get_nifty_bank_constituents())
                except Exception:
                    pass

            # Categorize OI spurts
            long_buildup = []      # OI ↑ + Price ↑ = Bullish
            short_buildup = []     # OI ↑ + Price ↓ = Bearish
            long_unwinding = []    # OI ↓ + Price ↓ = Bearish
            short_covering = []    # OI ↓ + Price ↑ = Bullish
            uncategorized = []     # No price data available

            for item in oi_response.data:
                symbol = item.symbol.upper()
                oi_change = item.change_in_oi
                price_change = price_changes.get(symbol)

                if price_change is None:
                    uncategorized.append((item, 0))
                    continue

                if oi_change > 0:  # OI increasing
                    if price_change > 0:
                        long_buildup.append((item, price_change))
                    else:
                        short_buildup.append((item, price_change))
                else:  # OI decreasing
                    if price_change > 0:
                        short_covering.append((item, price_change))
                    else:
                        long_unwinding.append((item, price_change))

            # Sort by OI change magnitude
            long_buildup.sort(key=lambda x: x[0].avg_in_oi, reverse=True)
            short_buildup.sort(key=lambda x: x[0].avg_in_oi, reverse=True)
            long_unwinding.sort(key=lambda x: abs(x[0].avg_in_oi), reverse=True)
            short_covering.sort(key=lambda x: abs(x[0].avg_in_oi), reverse=True)

            # Format output
            lines = ["# OI Spurts - Signal Analysis", ""]
            lines.append("*Combining OI changes with price movements to identify smart money direction*")
            lines.append("")

            # Summary
            bullish_count = len(long_buildup) + len(short_covering)
            bearish_count = len(short_buildup) + len(long_unwinding)

            lines.append("## Summary")
            lines.append(f"- **Bullish Signals:** {bullish_count} (Long Buildup: {len(long_buildup)}, Short Covering: {len(short_covering)})")
            lines.append(f"- **Bearish Signals:** {bearish_count} (Short Buildup: {len(short_buildup)}, Long Unwinding: {len(long_unwinding)})")
            lines.append(f"- **Market Bias:** {'BULLISH' if bullish_count > bearish_count else 'BEARISH' if bearish_count > bullish_count else 'NEUTRAL'}")
            lines.append("")

            def fmt_oi(v: int) -> str:
                if abs(v) >= 10000000:
                    return f"{v / 10000000:.1f}Cr"
                elif abs(v) >= 100000:
                    return f"{v / 100000:.1f}L"
                return f"{v:,}"

            # Long Buildup (Bullish)
            if long_buildup:
                lines.append("## 🟢 LONG BUILDUP (Bullish)")
                lines.append("*OI increasing + Price rising = New long positions being created*")
                lines.append("")
                lines.append("| Symbol | Price | Price Chg | OI Change | OI Chg% | Value (Cr) |")
                lines.append("|--------|-------|-----------|-----------|---------|------------|")
                for item, price_chg in long_buildup[:10]:
                    value_cr = item.total / 100
                    lines.append(
                        f"| **{item.symbol}** | ₹{item.underlying_value:,.0f} | +{price_chg:.2f}% | +{fmt_oi(item.change_in_oi)} | +{item.avg_in_oi:.1f}% | {value_cr:,.0f} |"
                    )
                lines.append("")

            # Short Covering (Bullish)
            if short_covering:
                lines.append("## 🟢 SHORT COVERING (Bullish)")
                lines.append("*OI decreasing + Price rising = Shorts closing positions*")
                lines.append("")
                lines.append("| Symbol | Price | Price Chg | OI Change | OI Chg% | Value (Cr) |")
                lines.append("|--------|-------|-----------|-----------|---------|------------|")
                for item, price_chg in short_covering[:10]:
                    value_cr = item.total / 100
                    lines.append(
                        f"| **{item.symbol}** | ₹{item.underlying_value:,.0f} | +{price_chg:.2f}% | {fmt_oi(item.change_in_oi)} | {item.avg_in_oi:.1f}% | {value_cr:,.0f} |"
                    )
                lines.append("")

            # Short Buildup (Bearish)
            if short_buildup:
                lines.append("## 🔴 SHORT BUILDUP (Bearish)")
                lines.append("*OI increasing + Price falling = New short positions being created*")
                lines.append("")
                lines.append("| Symbol | Price | Price Chg | OI Change | OI Chg% | Value (Cr) |")
                lines.append("|--------|-------|-----------|-----------|---------|------------|")
                for item, price_chg in short_buildup[:10]:
                    value_cr = item.total / 100
                    lines.append(
                        f"| **{item.symbol}** | ₹{item.underlying_value:,.0f} | {price_chg:.2f}% | +{fmt_oi(item.change_in_oi)} | +{item.avg_in_oi:.1f}% | {value_cr:,.0f} |"
                    )
                lines.append("")

            # Long Unwinding (Bearish)
            if long_unwinding:
                lines.append("## 🔴 LONG UNWINDING (Bearish)")
                lines.append("*OI decreasing + Price falling = Longs closing positions*")
                lines.append("")
                lines.append("| Symbol | Price | Price Chg | OI Change | OI Chg% | Value (Cr) |")
                lines.append("|--------|-------|-----------|-----------|---------|------------|")
                for item, price_chg in long_unwinding[:10]:
                    value_cr = item.total / 100
                    lines.append(
                        f"| **{item.symbol}** | ₹{item.underlying_value:,.0f} | {price_chg:.2f}% | {fmt_oi(item.change_in_oi)} | {item.avg_in_oi:.1f}% | {value_cr:,.0f} |"
                    )
                lines.append("")

            # Trading implications
            lines.append("## Trading Implications")
            lines.append("")
            if long_buildup:
                top_lb = [item.symbol for item, _ in long_buildup[:3]]
                lines.append(f"- **Strong Longs:** {', '.join(top_lb)} - Consider buying on dips")
            if short_covering:
                top_sc = [item.symbol for item, _ in short_covering[:3]]
                lines.append(f"- **Short Squeeze Candidates:** {', '.join(top_sc)} - Momentum may continue")
            if short_buildup:
                top_sb = [item.symbol for item, _ in short_buildup[:3]]
                lines.append(f"- **Weak Stocks:** {', '.join(top_sb)} - Avoid longs, consider shorts")
            if long_unwinding:
                top_lu = [item.symbol for item, _ in long_unwinding[:3]]
                lines.append(f"- **Exiting Longs:** {', '.join(top_lu)} - Possible further downside")
            lines.append("")

            return "\n".join(lines)

        except Exception as e:
            return f"Error scanning OI spurts: {str(e)}"

    def fetch_sector_constituents(self, sector: str) -> str:
        """Fetch all stocks in a sector dynamically.

        This tool maps common sector names to NSE indices and returns all
        constituent stocks with their current prices and performance data.

        Use this to:
        - Get all stocks in a specific sector for analysis
        - Screen sector stocks by performance
        - Identify sector leaders and laggards

        Args:
            sector: Sector name (case-insensitive). Examples:
                - Banking: "banking", "bank", "private bank", "psu bank"
                - Technology: "it", "tech", "software"
                - Healthcare: "pharma", "healthcare"
                - Consumer: "fmcg", "consumer durables"
                - Industrial: "auto", "metal", "realty", "energy", "infra"
                - Others: "media", "pse", "psu", "oil gas"

        Returns:
            Markdown formatted list of sector stocks with:
            - Symbol, company name, LTP
            - Day's change percentage
            - 52W high/low proximity
            - 1Y returns
        """
        try:
            # Normalize sector name
            sector_lower = sector.lower().strip()

            # Look up index name
            index_name = self.SECTOR_INDEX_MAP.get(sector_lower)

            if not index_name:
                # Try partial match
                for key, value in self.SECTOR_INDEX_MAP.items():
                    if sector_lower in key or key in sector_lower:
                        index_name = value
                        break

            if not index_name:
                available = sorted(set(self.SECTOR_INDEX_MAP.values()))
                return (
                    f"Unknown sector: '{sector}'\n\n"
                    f"**Available sectors:**\n"
                    + "\n".join(f"- {s}" for s in available)
                )

            # Fetch index constituents
            response = self.client.get_index_constituents(index_name)

            if not response.data:
                return f"No constituents found for {index_name}"

            lines = [f"# {index_name} - Sector Constituents", ""]

            # Summary
            if response.advance:
                adv = response.advance
                lines.append(f"**Advances:** {adv.advances} | **Declines:** {adv.declines} | **Unchanged:** {adv.unchanged}")
                lines.append("")

            # Table
            lines.append("| Symbol | Company | LTP | Change% | 52W High% | 52W Low% | 1Y Ret% |")
            lines.append("|--------|---------|-----|---------|-----------|----------|---------|")

            # Sort by day's change (best performers first)
            sorted_data = sorted(
                [d for d in response.data if d.symbol != response.name and d.priority != 1],
                key=lambda x: x.pchange or 0,
                reverse=True
            )

            for c in sorted_data:
                symbol = c.symbol or "-"
                company = "-"
                if c.meta and c.meta.company_name:
                    company = c.meta.company_name[:30] + "..." if len(c.meta.company_name) > 30 else c.meta.company_name

                ltp = f"₹{c.last_price:,.2f}" if c.last_price else "-"
                pchange = f"{c.pchange:+.2f}%" if c.pchange is not None else "-"
                near_high = f"{c.near_wkh:.1f}%" if c.near_wkh is not None else "-"
                near_low = f"{c.near_wkl:.1f}%" if c.near_wkl is not None else "-"
                yearly_ret = f"{c.per_change_365d:+.1f}%" if c.per_change_365d is not None else "-"

                lines.append(f"| **{symbol}** | {company} | {ltp} | {pchange} | {near_high} | {near_low} | {yearly_ret} |")

            lines.append("")
            lines.append(f"*Total: {len(sorted_data)} stocks*")

            # Quick stats
            gainers = len([d for d in sorted_data if d.pchange and d.pchange > 0])
            losers = len([d for d in sorted_data if d.pchange and d.pchange < 0])
            near_high_count = len([d for d in sorted_data if d.near_wkh and d.near_wkh >= 95])
            near_low_count = len([d for d in sorted_data if d.near_wkl and d.near_wkl <= 5])

            lines.append("")
            lines.append("## Quick Stats")
            lines.append(f"- **Gainers:** {gainers} | **Losers:** {losers}")
            lines.append(f"- **Near 52W High (≥95%):** {near_high_count}")
            lines.append(f"- **Near 52W Low (≤5%):** {near_low_count}")

            return "\n".join(lines)

        except Exception as e:
            return f"Error fetching sector constituents for '{sector}': {str(e)}"
