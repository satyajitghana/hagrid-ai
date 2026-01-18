"""NSE India API client for fetching corporate announcements and annual reports."""

import csv
import datetime
from datetime import date
from io import StringIO
from pathlib import Path
from typing import Any

from .core.cache import CacheConfig, CacheTTL
from .core.exceptions import NSEIndiaParseError
from .core.http_client import NSEIndiaHTTPClient
from .models.announcement import (
    Announcement,
    AnnualReport,
    DebtAnnouncement,
    EquityAnnouncement,
    ShareholdingPattern,
)
from .models.enums import AnnouncementIndex, FinancialResultPeriod
from .models.event_calendar import CorporateEvent
from .models.financial_results import (
    FinancialResult,
    FinancialResultPeriodData,
    FinancialResultsComparison,
)
from .models.indices import AllIndicesResponse, IndexCategory, IndexData
from .models.deals import (
    BlockDeal,
    BulkDeal,
    DealType,
    LargeDealsSnapshot,
    ShortSelling,
)
from .models.insider_trading import (
    InsiderTradingPlan,
    InsiderTransaction,
    InsiderTransactionResponse,
)
from .models.oi_spurts import OISpurtData, OISpurtsResponse
from .models.most_active import (
    MostActiveEquity,
    MostActiveETF,
    MostActiveETFResponse,
    MostActiveResponse,
    MostActiveSME,
    MostActiveSMEResponse,
    PriceVariation,
    PriceVariationsResponse,
    VolumeGainer,
    VolumeGainersResponse,
)
from .models.option_chain import (
    OptionChainAnalysis,
    OptionChainResponse,
    OptionChainStrike,
    OptionContractInfo,
    OptionData,
)
from .models.shareholding import (
    BeneficialOwner,
    DetailedShareholdingPattern,
    ShareholderDetail,
    ShareholdingDeclaration,
    ShareholdingSummary,
)
from .models.advances_declines import (
    AdvancesResponse,
    DeclinesResponse,
    MarketBreadthCount,
    MarketBreadthSnapshot,
    MarketMover,
    AdvancesDeclinesSectionData,
)
from .models.stocks_traded import (
    StockTraded,
    StocksTradedCount,
    StocksTradedResponse,
)
from .models.price_band import (
    PriceBandCategory,
    PriceBandCount,
    PriceBandHitter,
    PriceBandResponse,
)
from .models.pre_open import (
    PreOpenMarketDetail,
    PreOpenMarketSnapshot,
    PreOpenOrder,
    PreOpenResponse,
    PreOpenStock,
    PreOpenStockMetadata,
)
from .models.securities import (
    SecuritiesResponse,
    Security,
    TradingSeries,
)
from .models.index_constituents import (
    IndexAdvanceDecline,
    IndexConstituent,
    IndexConstituentsResponse,
    IndexMaster,
    StockMeta,
)
from .models.index_summary import (
    IndexAdvanceDeclineData,
    IndexAnnouncement,
    IndexBoardMeeting,
    IndexChartData,
    IndexChartPoint,
    IndexContributor,
    IndexFacts,
    IndexHeatmapStock,
    IndexPriceData,
    IndexReturns,
    IndexSummaryData,
    IndexTopMover,
)
from .models.chart import (
    ChartCandle,
    ChartDataResponse,
    ChartSymbol,
    ChartType,
    SymbolSearchResponse,
    SymbolType,
)
from .storage.tracker import AnnouncementTracker, ProcessedAnnouncement


class NSEIndiaClient:
    """Client for NSE India API.

    Provides methods to fetch corporate announcements, annual reports,
    and download PDF attachments.

    Features:
    - Automatic caching with intelligent TTLs per endpoint type
    - Real-time data (prices, OI) cached briefly (30s-2min)
    - Semi-static data (financials, shareholding) cached longer (days/weeks)
    - Static data (metadata, annual reports) cached for 30 days
    """

    def __init__(
        self,
        timeout: float = 30.0,
        db_path: str | Path = "nse_announcements.db",
        attachments_dir: str | Path = "nse_attachments",
        cache_enabled: bool = True,
    ):
        """Initialize the NSE India client.

        Args:
            timeout: HTTP request timeout in seconds
            db_path: Path to SQLite database for tracking processed announcements
            attachments_dir: Directory to store downloaded attachments
            cache_enabled: Whether to enable response caching (default: True)
        """
        cache_config = CacheConfig(enabled=cache_enabled)
        self._http = NSEIndiaHTTPClient(timeout=timeout, cache_config=cache_config)
        self._tracker = AnnouncementTracker(db_path=db_path)
        self._attachments_dir = Path(attachments_dir)

    @property
    def tracker(self) -> AnnouncementTracker:
        """Get the announcement tracker."""
        return self._tracker

    # === Cache Control Methods ===

    @property
    def cache_enabled(self) -> bool:
        """Check if caching is enabled."""
        return self._http.cache_enabled

    @property
    def cache_stats(self) -> dict[str, Any]:
        """Get cache statistics.

        Returns:
            Dict with:
            - entries: Number of cached entries
            - hits: Number of cache hits
            - misses: Number of cache misses
            - hit_rate_percent: Cache hit rate percentage
        """
        return self._http.cache_stats

    def enable_cache(self) -> None:
        """Enable response caching."""
        self._http.enable_cache()

    def disable_cache(self) -> None:
        """Disable response caching."""
        self._http.disable_cache()

    def clear_cache(self) -> None:
        """Clear all cached responses."""
        self._http.clear_cache()

    def _parse_csv(
        self,
        csv_content: str,
        index: AnnouncementIndex,
    ) -> list[Announcement]:
        """Parse CSV content into announcement models.

        Args:
            csv_content: Raw CSV content from NSE API
            index: Type of announcement index

        Returns:
            List of parsed announcement models
        """
        try:
            # Remove BOM if present (common in NSE CSV files)
            if csv_content.startswith("\ufeff"):
                csv_content = csv_content[1:]

            reader = csv.DictReader(StringIO(csv_content))
            announcements: list[Announcement] = []

            for row in reader:
                # Skip empty rows
                if not any(row.values()):
                    continue

                if index == AnnouncementIndex.DEBT:
                    # Debt announcements don't have SYMBOL column
                    announcement = DebtAnnouncement.model_validate(row)
                else:
                    # Equities, SME, MF, SLB have SYMBOL column
                    announcement = EquityAnnouncement.model_validate(row)

                announcements.append(announcement)

            return announcements

        except Exception as e:
            raise NSEIndiaParseError(
                message=f"Failed to parse CSV: {e}",
                raw_data=csv_content[:500],
            ) from e

    def get_announcements(
        self,
        index: AnnouncementIndex,
        from_date: date | None = None,
        to_date: date | None = None,
        symbol: str | None = None,
    ) -> list[Announcement]:
        """Fetch corporate announcements from NSE India.

        Args:
            index: Type of announcements (equities, debt, sme, mf, slb)
            from_date: Start date for filtering (optional)
            to_date: End date for filtering (optional)
            symbol: Stock symbol to filter by (optional)

        Returns:
            List of announcement models
        """
        params: dict = {
            "index": index.value,
            "csv": "true",
        }

        if from_date:
            params["from_date"] = from_date.strftime("%d-%m-%Y")

        if to_date:
            params["to_date"] = to_date.strftime("%d-%m-%Y")

        if symbol:
            params["symbol"] = symbol.upper()

        csv_content = self._http.get_csv("/api/corporate-announcements", params=params)
        return self._parse_csv(csv_content, index)

    def get_new_announcements(
        self,
        index: AnnouncementIndex,
        from_date: date | None = None,
        to_date: date | None = None,
        symbol: str | None = None,
    ) -> list[Announcement]:
        """Fetch only unprocessed announcements.

        Args:
            index: Type of announcements
            from_date: Start date for filtering (optional)
            to_date: End date for filtering (optional)
            symbol: Stock symbol to filter by (optional)

        Returns:
            List of announcements that haven't been processed yet
        """
        all_announcements = self.get_announcements(
            index=index,
            from_date=from_date,
            to_date=to_date,
            symbol=symbol,
        )
        return self._tracker.get_unprocessed(all_announcements)

    def get_annual_reports(
        self,
        symbol: str,
        index: AnnouncementIndex = AnnouncementIndex.EQUITIES,
    ) -> list[AnnualReport]:
        """Fetch annual reports for a company.

        Args:
            symbol: Stock symbol (e.g., "RELIANCE")
            index: Index type (default: equities)

        Returns:
            List of annual report data
        """
        params = {
            "index": index.value,
            "symbol": symbol.upper(),
        }

        response = self._http.get_json("/api/annual-reports", params=params)

        if "data" not in response:
            return []

        reports = []
        for item in response["data"]:
            try:
                report = AnnualReport.model_validate(item)
                reports.append(report)
            except Exception:
                # Skip invalid entries
                continue

        return reports

    def get_shareholding_patterns_history(
        self,
        symbol: str,
        issuer: str | None = None,
        index: AnnouncementIndex = AnnouncementIndex.EQUITIES,
    ) -> list[ShareholdingPattern]:
        """Fetch historical shareholding patterns for a company.

        This API provides quarterly shareholding pattern history showing
        promoter vs public holdings over time.

        Args:
            symbol: Stock symbol (e.g., "RELIANCE")
            issuer: Company name for filtering (optional, URL encoded automatically)
            index: Index type (default: equities)

        Returns:
            List of ShareholdingPattern objects sorted by date (newest first)
        """
        params: dict[str, str] = {
            "index": index.value,
            "symbol": symbol.upper(),
        }

        if issuer:
            params["issuer"] = issuer

        response = self._http.get_json("/api/corporate-share-holdings-master", params=params)

        # Response is a list directly
        if not isinstance(response, list):
            return []

        patterns = []
        for item in response:
            try:
                pattern = ShareholdingPattern.model_validate(item)
                patterns.append(pattern)
            except Exception:
                # Skip invalid entries
                continue

        return patterns

    def get_shareholding_details(
        self,
        nds_id: str,
        symbol: str | None = None,
        company_name: str | None = None,
        period_ended: str | None = None,
    ) -> DetailedShareholdingPattern:
        """Fetch detailed shareholding pattern for a specific quarter.

        This method fetches comprehensive shareholding data including:
        - Summary by category (promoter, public, non-public)
        - Individual promoter shareholders with their holdings
        - Public shareholders breakdown
        - Beneficial owners (significant shareholders)
        - Declarations

        Args:
            nds_id: The record ID from shareholding pattern history
            symbol: Stock symbol (optional, for metadata)
            company_name: Company name (optional, for metadata)
            period_ended: Period ended date string (optional, for metadata)

        Returns:
            DetailedShareholdingPattern object with all shareholding details
        """
        from .models.announcement import parse_nse_date

        # Fetch all relevant data
        summary_data = self._http.get_json(
            "/api/corporate-share-holdings-equities",
            params={"ndsId": nds_id, "index": "summary"}
        )
        promoter_data = self._http.get_json(
            "/api/corporate-share-holdings-equities",
            params={"ndsId": nds_id, "index": "promoter"}
        )
        public_data = self._http.get_json(
            "/api/corporate-share-holdings-equities",
            params={"ndsId": nds_id, "index": "public-shareholder"}
        )
        non_public_data = self._http.get_json(
            "/api/corporate-share-holdings-equities",
            params={"ndsId": nds_id, "index": "non-public-shareholder"}
        )
        beneficial_data = self._http.get_json(
            "/api/corporate-share-holdings-equities",
            params={"ndsId": nds_id, "index": "beneficial-owners"}
        )
        declaration_data = self._http.get_json(
            "/api/corporate-share-holdings-equities",
            params={"ndsId": nds_id, "index": "declaration"}
        )

        # Parse summary
        summary = []
        if isinstance(summary_data, list):
            for item in summary_data:
                try:
                    summary.append(ShareholdingSummary.model_validate(item))
                except Exception:
                    pass

        # Parse promoters - separate Indian and Foreign
        promoter_indian = []
        promoter_foreign = []
        current_section = "indian"

        if isinstance(promoter_data, list):
            for item in promoter_data:
                try:
                    col_i = item.get("COL_I", "")
                    # Track section changes
                    if col_i and "foreign" in col_i.lower():
                        current_section = "foreign"
                    elif col_i and "indian" in col_i.lower():
                        current_section = "indian"

                    detail = ShareholderDetail.model_validate(item)
                    if detail.is_individual:
                        if current_section == "foreign":
                            promoter_foreign.append(detail)
                        else:
                            promoter_indian.append(detail)
                except Exception:
                    pass

        # Parse public shareholders - separate institutions and non-institutions
        public_institutions = []
        public_non_institutions = []
        current_section = "institutions"

        if isinstance(public_data, list):
            for item in public_data:
                try:
                    col_i = item.get("COL_I", "")
                    # Track section changes
                    if col_i and "non-institution" in col_i.lower():
                        current_section = "non-institutions"
                    elif col_i and "institution" in col_i.lower():
                        current_section = "institutions"

                    detail = ShareholderDetail.model_validate(item)
                    if detail.total_shares > 0:
                        if current_section == "non-institutions":
                            public_non_institutions.append(detail)
                        else:
                            public_institutions.append(detail)
                except Exception:
                    pass

        # Parse non-public shareholders
        non_public = []
        if isinstance(non_public_data, list):
            for item in non_public_data:
                try:
                    detail = ShareholderDetail.model_validate(item)
                    if detail.total_shares > 0:
                        non_public.append(detail)
                except Exception:
                    pass

        # Parse beneficial owners
        beneficial_owners = []
        if isinstance(beneficial_data, list):
            for item in beneficial_data:
                try:
                    bo = BeneficialOwner.model_validate(item)
                    beneficial_owners.append(bo)
                except Exception:
                    pass

        # Parse declarations
        declarations = []
        if isinstance(declaration_data, list):
            for item in declaration_data:
                try:
                    decl = ShareholdingDeclaration.model_validate(item)
                    declarations.append(decl)
                except Exception:
                    pass

        # Parse period ended date
        period_dt = None
        if period_ended:
            period_dt = parse_nse_date(period_ended)

        return DetailedShareholdingPattern(
            symbol=symbol or "",
            company_name=company_name or "",
            nds_id=nds_id,
            period_ended=period_dt,
            summary=summary,
            promoter_indian=promoter_indian,
            promoter_foreign=promoter_foreign,
            public_institutions=public_institutions,
            public_non_institutions=public_non_institutions,
            non_public_shareholders=non_public,
            beneficial_owners=beneficial_owners,
            declarations=declarations,
        )

    def get_latest_shareholding_details(self, symbol: str) -> DetailedShareholdingPattern | None:
        """Fetch detailed shareholding pattern for the latest quarter.

        Convenience method that first fetches the shareholding history
        to get the latest nds_id, then fetches detailed data.

        Args:
            symbol: Stock symbol (e.g., "RELIANCE")

        Returns:
            DetailedShareholdingPattern object or None if no data
        """
        patterns = self.get_shareholding_patterns_history(symbol)
        if not patterns:
            return None

        # Get the first (latest) pattern
        latest = patterns[0]
        return self.get_shareholding_details(
            nds_id=latest.record_id,
            symbol=latest.symbol,
            company_name=latest.company_name,
            period_ended=latest.pattern_date.strftime("%d-%b-%Y") if latest.pattern_date else None,
        )

    def download_attachment(
        self,
        announcement: Announcement,
        subdir: str | None = None,
    ) -> Path | None:
        """Download PDF attachment for an announcement.

        Args:
            announcement: Announcement with attachment URL
            subdir: Optional subdirectory within attachments_dir

        Returns:
            Path to downloaded file, or None if no attachment
        """
        if not announcement.has_attachment:
            return None

        # Determine save directory
        save_dir = self._attachments_dir
        if subdir:
            save_dir = save_dir / subdir

        # Extract filename from URL
        filename = announcement.attachment_url.split("/")[-1]

        # Add symbol prefix for equity announcements
        if isinstance(announcement, EquityAnnouncement):
            filename = f"{announcement.symbol}_{filename}"

        save_path = save_dir / filename
        return self._http.download_file(announcement.attachment_url, save_path)

    def download_annual_report(
        self,
        report: AnnualReport,
        symbol: str,
        subdir: str | None = None,
    ) -> Path:
        """Download an annual report file.

        Args:
            report: Annual report to download
            symbol: Stock symbol
            subdir: Optional subdirectory within attachments_dir

        Returns:
            Path to downloaded file
        """
        save_dir = self._attachments_dir / "annual_reports"
        if subdir:
            save_dir = save_dir / subdir

        # Extract filename from URL
        filename = report.file_url.split("/")[-1]
        filename = f"{symbol.upper()}_{filename}"

        save_path = save_dir / filename
        return self._http.download_file(report.file_url, save_path)

    def process_announcements(
        self,
        index: AnnouncementIndex,
        download_attachments: bool = True,
        from_date: date | None = None,
        to_date: date | None = None,
        symbol: str | None = None,
    ) -> list[ProcessedAnnouncement]:
        """Fetch new announcements, optionally download PDFs, and mark as processed.

        This is the main method for processing announcements. It:
        1. Fetches all announcements matching the criteria
        2. Filters out already-processed ones
        3. Optionally downloads PDF attachments
        4. Marks each announcement as processed in the database

        Args:
            index: Type of announcements
            download_attachments: Whether to download PDF attachments
            from_date: Start date for filtering (optional)
            to_date: End date for filtering (optional)
            symbol: Stock symbol to filter by (optional)

        Returns:
            List of ProcessedAnnouncement records
        """
        # Get new announcements
        new_announcements = self.get_new_announcements(
            index=index,
            from_date=from_date,
            to_date=to_date,
            symbol=symbol,
        )

        processed: list[ProcessedAnnouncement] = []

        for announcement in new_announcements:
            attachment_path: str | None = None

            # Download attachment if requested
            if download_attachments and announcement.has_attachment:
                try:
                    path = self.download_attachment(
                        announcement,
                        subdir=index.value,
                    )
                    if path:
                        attachment_path = str(path)
                except Exception:
                    # Continue processing even if download fails
                    pass

            # Mark as processed
            record = self._tracker.mark_processed(
                announcement=announcement,
                index_type=index,
                attachment_path=attachment_path,
            )
            processed.append(record)

        return processed

    # Financial Results API methods
    def get_financial_results(
        self,
        symbol: str,
        issuer: str | None = None,
        period: FinancialResultPeriod = FinancialResultPeriod.QUARTERLY,
        index: AnnouncementIndex = AnnouncementIndex.EQUITIES,
    ) -> list[FinancialResult]:
        """Fetch corporate financial results for a company.

        This API provides historical financial results including quarterly
        and annual reports with both consolidated and non-consolidated data.

        Args:
            symbol: Stock symbol (e.g., "RELIANCE")
            issuer: Company name (optional, URL encoded automatically)
            period: Result period type (Quarterly or Annual)
            index: Index type (default: equities)

        Returns:
            List of FinancialResult objects sorted by filing date (newest first)
        """
        params: dict[str, str] = {
            "index": index.value,
            "symbol": symbol.upper(),
            "period": period.value,
        }

        if issuer:
            params["issuer"] = issuer

        response = self._http.get_json("/api/corporates-financial-results", params=params)

        if not isinstance(response, list):
            return []

        results = []
        for item in response:
            try:
                result = FinancialResult.model_validate(item)
                results.append(result)
            except Exception:
                # Skip invalid entries
                continue

        return results

    def get_quarterly_results(
        self,
        symbol: str,
        issuer: str | None = None,
        consolidated_only: bool = False,
        index: AnnouncementIndex = AnnouncementIndex.EQUITIES,
    ) -> list[FinancialResult]:
        """Fetch quarterly financial results for a company.

        Convenience method for getting only quarterly results.

        Args:
            symbol: Stock symbol (e.g., "RELIANCE")
            issuer: Company name (optional)
            consolidated_only: If True, return only consolidated results
            index: Index type (default: equities)

        Returns:
            List of quarterly FinancialResult objects
        """
        results = self.get_financial_results(
            symbol=symbol,
            issuer=issuer,
            period=FinancialResultPeriod.QUARTERLY,
            index=index,
        )

        if consolidated_only:
            results = [r for r in results if r.is_consolidated]

        return results

    def get_annual_results(
        self,
        symbol: str,
        issuer: str | None = None,
        consolidated_only: bool = False,
        index: AnnouncementIndex = AnnouncementIndex.EQUITIES,
    ) -> list[FinancialResult]:
        """Fetch annual financial results for a company.

        Convenience method for getting only annual results.

        Args:
            symbol: Stock symbol (e.g., "RELIANCE")
            issuer: Company name (optional)
            consolidated_only: If True, return only consolidated results
            index: Index type (default: equities)

        Returns:
            List of annual FinancialResult objects
        """
        results = self.get_financial_results(
            symbol=symbol,
            issuer=issuer,
            period=FinancialResultPeriod.ANNUAL,
            index=index,
        )

        if consolidated_only:
            results = [r for r in results if r.is_consolidated]

        return results

    def get_latest_financial_result(
        self,
        symbol: str,
        consolidated: bool = True,
        period: FinancialResultPeriod = FinancialResultPeriod.QUARTERLY,
        index: AnnouncementIndex = AnnouncementIndex.EQUITIES,
    ) -> FinancialResult | None:
        """Get the most recent financial result for a company.

        Args:
            symbol: Stock symbol (e.g., "RELIANCE")
            consolidated: If True, return consolidated result; otherwise non-consolidated
            period: Result period type (Quarterly or Annual)
            index: Index type (default: equities)

        Returns:
            Most recent FinancialResult or None if not found
        """
        results = self.get_financial_results(
            symbol=symbol,
            period=period,
            index=index,
        )

        # Filter by consolidation type
        filtered = [r for r in results if r.is_consolidated == consolidated]

        # Results should be sorted by filing date (newest first)
        if filtered:
            return filtered[0]
        return None

    def get_financial_results_by_fy(
        self,
        symbol: str,
        fy_start_year: int,
        period: FinancialResultPeriod = FinancialResultPeriod.QUARTERLY,
        index: AnnouncementIndex = AnnouncementIndex.EQUITIES,
    ) -> list[FinancialResult]:
        """Get financial results for a specific financial year.

        Args:
            symbol: Stock symbol (e.g., "RELIANCE")
            fy_start_year: Starting year of financial year (e.g., 2024 for FY 2024-25)
            period: Result period type (Quarterly or Annual)
            index: Index type (default: equities)

        Returns:
            List of FinancialResult objects for the specified FY
        """
        results = self.get_financial_results(
            symbol=symbol,
            period=period,
            index=index,
        )

        return [r for r in results if r.fy_start_year == fy_start_year]

    # Financial Results Comparison API methods
    def get_financial_results_comparison(
        self,
        symbol: str,
        issuer: str | None = None,
        index: AnnouncementIndex = AnnouncementIndex.EQUITIES,
    ) -> FinancialResultsComparison:
        """Fetch financial results comparison data for quarterly comparison.

        This API returns detailed financial data across multiple quarters,
        making it easy to compare revenue, profit, expenses, and ratios
        over time.

        Args:
            symbol: Stock symbol (e.g., "RELIANCE")
            issuer: Company name (optional, URL encoded automatically)
            index: Index type (default: equities)

        Returns:
            FinancialResultsComparison object with period-wise data
        """
        params: dict[str, str] = {
            "index": index.value,
            "symbol": symbol.upper(),
        }

        if issuer:
            params["issuer"] = issuer

        response = self._http.get_json("/api/results-comparision", params=params)

        # Parse the response
        periods = []
        is_banking = response.get("bankNonBnking", "N") == "Y"

        if "resCmpData" in response and isinstance(response["resCmpData"], list):
            for item in response["resCmpData"]:
                try:
                    period_data = FinancialResultPeriodData.model_validate(item)
                    periods.append(period_data)
                except Exception:
                    # Skip invalid entries
                    continue

        return FinancialResultsComparison(
            symbol=symbol.upper(),
            is_banking=is_banking,
            periods=periods,
        )

    def get_results_comparison_trend(
        self,
        symbol: str,
        num_quarters: int = 8,
        index: AnnouncementIndex = AnnouncementIndex.EQUITIES,
    ) -> dict[str, list[tuple[str, float | None]]]:
        """Get trend data for key financial metrics.

        Convenience method that returns trends for revenue, profit, EPS,
        and margins across multiple quarters.

        Args:
            symbol: Stock symbol (e.g., "RELIANCE")
            num_quarters: Number of quarters to include (default: 8)
            index: Index type (default: equities)

        Returns:
            Dictionary with trends for each metric:
            - revenue: [(period, value), ...]
            - profit: [(period, value), ...]
            - eps: [(period, value), ...]
            - margin: [(period, value), ...]
        """
        comparison = self.get_financial_results_comparison(symbol=symbol, index=index)

        # Limit to requested number of quarters
        periods = comparison.periods[:num_quarters]

        return {
            "revenue": [(p.period_label, p.net_sales) for p in periods],
            "profit": [(p.period_label, p.net_profit) for p in periods],
            "eps": [(p.period_label, p.basic_eps_continuing or p.basic_eps) for p in periods],
            "margin": [(p.period_label, p.net_profit_margin) for p in periods],
            "ebitda": [(p.period_label, p.ebitda) for p in periods],
        }

    def get_latest_quarter_comparison(
        self,
        symbol: str,
        index: AnnouncementIndex = AnnouncementIndex.EQUITIES,
    ) -> dict[str, Any]:
        """Get comparison of latest quarter vs previous quarter and same quarter last year.

        Args:
            symbol: Stock symbol (e.g., "RELIANCE")
            index: Index type (default: equities)

        Returns:
            Dictionary with latest quarter data and growth comparisons
        """
        comparison = self.get_financial_results_comparison(symbol=symbol, index=index)

        if not comparison.latest:
            return {"error": f"No financial data found for {symbol}"}

        latest = comparison.latest
        result: dict[str, Any] = {
            "symbol": symbol.upper(),
            "quarter": latest.quarter,
            "period_ended": latest.to_date.strftime("%d-%b-%Y") if latest.to_date else None,
            "is_audited": latest.is_audited,
            "revenue_lakhs": latest.net_sales,
            "net_profit_lakhs": latest.net_profit,
            "eps": latest.basic_eps_continuing or latest.basic_eps,
            "net_profit_margin": latest.net_profit_margin,
            "ebitda_lakhs": latest.ebitda,
        }

        # QoQ growth
        if comparison.revenue_growth_qoq is not None:
            result["revenue_growth_qoq"] = comparison.revenue_growth_qoq
        if comparison.profit_growth_qoq is not None:
            result["profit_growth_qoq"] = comparison.profit_growth_qoq

        # YoY growth
        if comparison.revenue_growth_yoy is not None:
            result["revenue_growth_yoy"] = comparison.revenue_growth_yoy
        if comparison.profit_growth_yoy is not None:
            result["profit_growth_yoy"] = comparison.profit_growth_yoy

        return result

    # Market Indices API methods
    def get_all_indices(self) -> AllIndicesResponse:
        """Fetch data for all NSE market indices.

        Returns real-time data for all indices including:
        - Price data (OHLC, last, variation)
        - Valuation metrics (PE, PB, Dividend Yield)
        - Market breadth (advances, declines, unchanged)
        - Performance metrics (1Y, 30D, 1W changes)
        - Chart URLs

        Returns:
            AllIndicesResponse containing list of all indices
        """
        from datetime import datetime

        response = self._http.get_json("/api/allIndices")

        if not isinstance(response, dict) or "data" not in response:
            return AllIndicesResponse(indices=[])

        indices = []
        for item in response["data"]:
            try:
                index = IndexData.model_validate(item)
                indices.append(index)
            except Exception:
                # Skip invalid entries
                continue

        return AllIndicesResponse(
            indices=indices,
            timestamp=datetime.now(),
        )

    def get_index(self, symbol: str) -> IndexData | None:
        """Get data for a specific index by symbol.

        Args:
            symbol: Index symbol (e.g., "NIFTY 50", "NIFTY BANK", "NIFTY IT")

        Returns:
            IndexData or None if not found
        """
        all_indices = self.get_all_indices()
        return all_indices.get_by_symbol(symbol)

    def get_indices_by_category(
        self, category: str | IndexCategory
    ) -> list[IndexData]:
        """Get indices filtered by category.

        Args:
            category: Index category (use IndexCategory enum or string)

        Returns:
            List of IndexData for the specified category
        """
        all_indices = self.get_all_indices()
        return all_indices.get_by_category(category)

    def get_derivatives_eligible_indices(self) -> list[IndexData]:
        """Get indices eligible for derivatives trading.

        Returns:
            List of IndexData for F&O eligible indices
        """
        all_indices = self.get_all_indices()
        return all_indices.derivatives_eligible

    def get_sectoral_indices(self) -> list[IndexData]:
        """Get all sectoral indices.

        Returns:
            List of sectoral IndexData
        """
        all_indices = self.get_all_indices()
        return all_indices.sectoral

    def get_broad_market_indices(self) -> list[IndexData]:
        """Get broad market indices (NIFTY 50, 100, 200, 500, etc.).

        Returns:
            List of broad market IndexData
        """
        all_indices = self.get_all_indices()
        return all_indices.broad_market

    def get_index_gainers(self, limit: int = 10) -> list[IndexData]:
        """Get top gaining indices.

        Args:
            limit: Maximum number of indices to return

        Returns:
            List of IndexData sorted by percent change (descending)
        """
        all_indices = self.get_all_indices()
        return all_indices.gainers[:limit]

    def get_index_losers(self, limit: int = 10) -> list[IndexData]:
        """Get top losing indices.

        Args:
            limit: Maximum number of indices to return

        Returns:
            List of IndexData sorted by percent change (ascending)
        """
        all_indices = self.get_all_indices()
        return all_indices.losers[:limit]

    def get_market_breadth(self) -> dict[str, Any]:
        """Get overall market breadth from NIFTY 500.

        Returns:
            Dict with advances, declines, unchanged, and ratio
        """
        nifty_500 = self.get_index("NIFTY 500")
        if nifty_500:
            return {
                "advances": nifty_500.advances,
                "declines": nifty_500.declines,
                "unchanged": nifty_500.unchanged,
                "ratio": nifty_500.market_breadth_ratio,
                "index_value": nifty_500.last,
                "percent_change": nifty_500.percent_change,
            }
        return {}

    # Large Deals (Bulk, Block, Short Selling) API methods
    def get_large_deals_snapshot(self) -> LargeDealsSnapshot:
        """Get snapshot of large deals from NSE capital markets.

        This API returns bulk deals, block deals, and short selling data:
        - Bulk Deals: Transactions where quantity > 0.5% of company shares
        - Block Deals: Single transactions >= 5 lakh shares or Rs. 10 crore value
        - Short Selling: Positions where investors sell borrowed securities

        Returns:
            LargeDealsSnapshot containing all deal types with helper methods
        """
        response = self._http.get_json("/api/snapshot-capital-market-largedeal")

        if not isinstance(response, dict):
            return LargeDealsSnapshot()

        # Parse bulk deals
        bulk_data = response.get("BULK_DEALS_DATA", [])
        bulk_deals = []
        for item in bulk_data:
            try:
                deal = BulkDeal.model_validate(item)
                bulk_deals.append(deal)
            except Exception:
                continue

        # Parse block deals
        block_data = response.get("BLOCK_DEALS_DATA", [])
        block_deals = []
        for item in block_data:
            try:
                deal = BlockDeal.model_validate(item)
                block_deals.append(deal)
            except Exception:
                continue

        # Parse short selling data
        short_data = response.get("SHORT_DEALS_DATA", [])
        short_selling = []
        for item in short_data:
            try:
                deal = ShortSelling.model_validate(item)
                short_selling.append(deal)
            except Exception:
                continue

        return LargeDealsSnapshot(
            as_on_date=response.get("date"),
            bulk_deals=bulk_deals,
            block_deals=block_deals,
            short_selling=short_selling,
            bulk_deals_count=len(bulk_deals),
            block_deals_count=len(block_deals),
            short_deals_count=len(short_selling),
        )

    def get_bulk_deals(self, symbol: str | None = None) -> list[BulkDeal]:
        """Get bulk deals, optionally filtered by symbol.

        Bulk deals are transactions where the total quantity traded is more than
        0.5% of the number of equity shares of the company.

        Args:
            symbol: Optional stock symbol to filter by

        Returns:
            List of BulkDeal objects
        """
        snapshot = self.get_large_deals_snapshot()
        if symbol:
            return snapshot.get_bulk_deals_by_symbol(symbol)
        return snapshot.bulk_deals

    def get_block_deals(self, symbol: str | None = None) -> list[BlockDeal]:
        """Get block deals, optionally filtered by symbol.

        Block deals are single transactions with a minimum quantity of 5 lakh shares
        or minimum value of Rs. 10 crore, executed through a separate trading window.

        Args:
            symbol: Optional stock symbol to filter by

        Returns:
            List of BlockDeal objects
        """
        snapshot = self.get_large_deals_snapshot()
        if symbol:
            return snapshot.get_block_deals_by_symbol(symbol)
        return snapshot.block_deals

    def get_short_selling(self, symbol: str | None = None) -> list[ShortSelling]:
        """Get short selling data, optionally filtered by symbol.

        Short selling occurs when an investor borrows a security and sells it
        on the open market, planning to buy it back later for less money.

        Args:
            symbol: Optional stock symbol to filter by

        Returns:
            List of ShortSelling objects
        """
        snapshot = self.get_large_deals_snapshot()
        if symbol:
            return snapshot.get_short_selling_by_symbol(symbol)
        return snapshot.short_selling

    def get_bulk_buys(self, limit: int = 20) -> list[BulkDeal]:
        """Get bulk buy deals sorted by value.

        Args:
            limit: Maximum number of deals to return

        Returns:
            List of BulkDeal objects (buy side only)
        """
        snapshot = self.get_large_deals_snapshot()
        buys = snapshot.bulk_buys
        return sorted(buys, key=lambda d: d.trade_value, reverse=True)[:limit]

    def get_bulk_sells(self, limit: int = 20) -> list[BulkDeal]:
        """Get bulk sell deals sorted by value.

        Args:
            limit: Maximum number of deals to return

        Returns:
            List of BulkDeal objects (sell side only)
        """
        snapshot = self.get_large_deals_snapshot()
        sells = snapshot.bulk_sells
        return sorted(sells, key=lambda d: d.trade_value, reverse=True)[:limit]

    def get_block_buys(self, limit: int = 20) -> list[BlockDeal]:
        """Get block buy deals sorted by value.

        Args:
            limit: Maximum number of deals to return

        Returns:
            List of BlockDeal objects (buy side only)
        """
        snapshot = self.get_large_deals_snapshot()
        buys = snapshot.block_buys
        return sorted(buys, key=lambda d: d.trade_value, reverse=True)[:limit]

    def get_block_sells(self, limit: int = 20) -> list[BlockDeal]:
        """Get block sell deals sorted by value.

        Args:
            limit: Maximum number of deals to return

        Returns:
            List of BlockDeal objects (sell side only)
        """
        snapshot = self.get_large_deals_snapshot()
        sells = snapshot.block_sells
        return sorted(sells, key=lambda d: d.trade_value, reverse=True)[:limit]

    def get_top_shorted_stocks(self, limit: int = 20) -> list[ShortSelling]:
        """Get top shorted stocks by quantity.

        Args:
            limit: Maximum number of stocks to return

        Returns:
            List of ShortSelling objects sorted by quantity
        """
        snapshot = self.get_large_deals_snapshot()
        return snapshot.get_top_shorted_stocks(limit)

    def get_deals_by_client(self, client_name: str) -> dict[str, list]:
        """Get all deals by a specific client (partial match).

        Useful for tracking activity of major institutional investors.

        Args:
            client_name: Client name to search for (case-insensitive partial match)

        Returns:
            Dictionary with bulk_deals and block_deals lists
        """
        snapshot = self.get_large_deals_snapshot()
        client_lower = client_name.lower()

        bulk_matches = [d for d in snapshot.bulk_deals if client_lower in d.client_name.lower()]
        block_matches = [d for d in snapshot.block_deals if client_lower in d.client_name.lower()]

        return {
            "bulk_deals": bulk_matches,
            "block_deals": block_matches,
        }

    # Stocks Traded (Live Analysis) API methods
    def get_stocks_traded(self) -> StocksTradedResponse:
        """Get live analysis of all stocks traded on NSE.

        Returns real-time data including:
        - Market breadth (advances, declines, unchanged)
        - Individual stock metrics (price, volume, market cap)
        - Trading activity across all listed securities

        Returns:
            StocksTradedResponse with count statistics and stock data
        """
        response = self._http.get_json("/api/live-analysis-stocksTraded")

        if not isinstance(response, dict):
            return StocksTradedResponse(
                count=StocksTradedCount(Advances=0, Unchange=0, Declines=0, Total=0),
                data=[],
            )

        total_data = response.get("total", {})
        count_data = total_data.get("count", {})
        stocks_data = total_data.get("data", [])

        # Parse count
        count = StocksTradedCount.model_validate(count_data)

        # Parse individual stocks
        stocks = []
        for item in stocks_data:
            try:
                stock = StockTraded.model_validate(item)
                stocks.append(stock)
            except Exception:
                continue

        return StocksTradedResponse(count=count, data=stocks)

    def get_top_traded_by_value(self, limit: int = 20) -> list[StockTraded]:
        """Get top traded stocks by value.

        Args:
            limit: Maximum number of stocks to return

        Returns:
            List of StockTraded sorted by traded value (descending)
        """
        response = self.get_stocks_traded()
        return response.get_most_traded_by_value(limit)

    def get_top_traded_by_volume(self, limit: int = 20) -> list[StockTraded]:
        """Get top traded stocks by volume.

        Args:
            limit: Maximum number of stocks to return

        Returns:
            List of StockTraded sorted by volume (descending)
        """
        response = self.get_stocks_traded()
        return response.get_most_traded_by_volume(limit)

    def get_stock_traded_data(self, symbol: str) -> StockTraded | None:
        """Get trading data for a specific symbol.

        Args:
            symbol: Stock symbol (e.g., "RELIANCE", "TCS")

        Returns:
            StockTraded or None if symbol not found
        """
        response = self.get_stocks_traded()
        return response.get_by_symbol(symbol)

    def get_market_turnover(self) -> dict[str, Any]:
        """Get overall market turnover statistics.

        Returns:
            Dictionary with market statistics:
            - advances, declines, unchanged counts
            - advance_decline_ratio
            - total_traded_value_cr
            - total_stocks_traded
        """
        response = self.get_stocks_traded()
        return {
            "advances": response.count.advances,
            "declines": response.count.declines,
            "unchanged": response.count.unchanged,
            "total_stocks": response.count.total,
            "advance_decline_ratio": response.count.advance_decline_ratio,
            "breadth_percentage": response.count.breadth_percentage,
            "total_traded_value_cr": response.total_traded_value_cr,
            "total_market_cap_cr": response.total_market_cap_cr,
        }

    def get_large_cap_activity(self, limit: int = 20) -> list[StockTraded]:
        """Get trading activity for large cap stocks.

        Large caps are defined as market cap > Rs. 50,000 crores.

        Args:
            limit: Maximum number of stocks to return

        Returns:
            List of StockTraded for large cap stocks sorted by traded value
        """
        response = self.get_stocks_traded()
        large_caps = response.get_large_caps(min_mcap_cr=50000)
        return sorted(large_caps, key=lambda s: s.total_traded_value, reverse=True)[:limit]

    def get_mid_cap_activity(self, limit: int = 20) -> list[StockTraded]:
        """Get trading activity for mid cap stocks.

        Mid caps are defined as market cap between Rs. 10,000-50,000 crores.

        Args:
            limit: Maximum number of stocks to return

        Returns:
            List of StockTraded for mid cap stocks sorted by traded value
        """
        response = self.get_stocks_traded()
        mid_caps = response.get_mid_caps(min_mcap_cr=10000, max_mcap_cr=50000)
        return sorted(mid_caps, key=lambda s: s.total_traded_value, reverse=True)[:limit]

    def get_small_cap_activity(self, limit: int = 20) -> list[StockTraded]:
        """Get trading activity for small cap stocks.

        Small caps are defined as market cap < Rs. 10,000 crores.

        Args:
            limit: Maximum number of stocks to return

        Returns:
            List of StockTraded for small cap stocks sorted by traded value
        """
        response = self.get_stocks_traded()
        small_caps = response.get_small_caps(max_mcap_cr=10000)
        return sorted(small_caps, key=lambda s: s.total_traded_value, reverse=True)[:limit]

    # Securities (Listed Stocks) API methods
    def get_listed_securities(self) -> SecuritiesResponse:
        """Get list of all securities available for trading on NSE.

        Fetches the complete list of equity securities from NSE's CSV file,
        including symbol, company name, series, listing date, ISIN, and face value.

        Returns:
            SecuritiesResponse containing all listed securities
        """
        csv_url = "https://nsearchives.nseindia.com/content/equities/EQUITY_L.csv"
        csv_content = self._http.get_csv(csv_url)

        if not csv_content:
            return SecuritiesResponse(securities=[], total_count=0)

        # Remove BOM if present
        if csv_content.startswith("\ufeff"):
            csv_content = csv_content[1:]

        reader = csv.DictReader(StringIO(csv_content))
        securities = []

        for row in reader:
            try:
                security = Security.model_validate(row)
                securities.append(security)
            except Exception:
                continue

        return SecuritiesResponse(securities=securities, total_count=len(securities))

    def get_security_by_symbol(self, symbol: str) -> Security | None:
        """Get security details by symbol.

        Args:
            symbol: Stock symbol (e.g., "RELIANCE", "TCS")

        Returns:
            Security or None if not found
        """
        response = self.get_listed_securities()
        return response.get_by_symbol(symbol)

    def get_security_by_isin(self, isin: str) -> Security | None:
        """Get security details by ISIN.

        Args:
            isin: ISIN identifier (e.g., "INE002A01018")

        Returns:
            Security or None if not found
        """
        response = self.get_listed_securities()
        return response.get_by_isin(isin)

    def search_securities(self, query: str) -> list[Security]:
        """Search securities by company name.

        Args:
            query: Search query (case-insensitive partial match)

        Returns:
            List of matching Security objects
        """
        response = self.get_listed_securities()
        return response.search_by_name(query)

    def get_securities_by_series(self, series: str = "EQ") -> list[Security]:
        """Get all securities of a specific trading series.

        Args:
            series: Trading series (EQ, BE, BZ, SM, ST)

        Returns:
            List of Security objects in that series
        """
        response = self.get_listed_securities()
        return response.get_by_series(series)

    def get_recently_listed_securities(self, days: int = 30) -> list[Security]:
        """Get securities listed within the specified days.

        Args:
            days: Number of days to look back (default: 30)

        Returns:
            List of recently listed Security objects
        """
        response = self.get_listed_securities()
        return response.get_recently_listed(days)

    def get_all_symbols(self) -> list[str]:
        """Get list of all trading symbols on NSE.

        Returns:
            List of all symbol strings
        """
        response = self.get_listed_securities()
        return response.get_symbols()

    def get_securities_count(self) -> dict[str, int]:
        """Get count of securities by trading series.

        Returns:
            Dictionary with series as key and count as value
        """
        response = self.get_listed_securities()
        counts = response.get_series_counts()
        counts["total"] = response.total_count
        return counts

    def close(self) -> None:
        """Close the HTTP client."""
        self._http.close()

    def __enter__(self) -> "NSEIndiaClient":
        return self

    def __exit__(self, *args) -> None:
        self.close()

    # Quote API methods
    def _get_quote_api(self, function_name: str, **params) -> dict[str, Any]:
        """Call the NSE Quote API with the given function and parameters."""
        query_params = {"functionName": function_name, **params}
        return self._http.get_json(
            "/api/NextApi/apiClient/GetQuoteApi", params=query_params
        )

    def get_symbol_name(self, symbol: str) -> dict[str, Any]:
        """Get symbol name and company details."""
        return self._get_quote_api("getSymbolName", symbol=symbol.upper())

    def get_metadata(self, symbol: str) -> dict[str, Any]:
        """Get metadata about a symbol (series, F&O status, ISIN, etc.)."""
        return self._get_quote_api("getMetaData", symbol=symbol.upper())

    def get_symbol_data(
        self, symbol: str, market_type: str = "N", series: str = "EQ"
    ) -> dict[str, Any]:
        """Get detailed symbol data including price, volume, and market info."""
        return self._get_quote_api(
            "getSymbolData",
            symbol=symbol.upper(),
            marketType=market_type,
            series=series,
        )

    def get_shareholding_pattern(
        self, symbol: str, no_of_records: int = 5
    ) -> dict[str, Any]:
        """Get shareholding pattern (promoter vs public holdings)."""
        return self._get_quote_api(
            "getShareholdingPattern",
            symbol=symbol.upper(),
            noOfRecords=str(no_of_records),
        )

    def get_financial_status(self, symbol: str) -> list[dict[str, Any]]:
        """Get recent financial results (quarterly)."""
        return self._get_quote_api("getFinancialStatus", symbol=symbol.upper())

    def get_financial_result_data(
        self, symbol: str, no_of_records: int = 5
    ) -> list[dict[str, Any]]:
        """Get detailed financial result data."""
        return self._get_quote_api(
            "getFinancialResultData",
            symbol=symbol.upper(),
            marketApiType="equities",
            noOfRecords=str(no_of_records),
        )

    def get_yearwise_data(self, symbol: str) -> list[dict[str, Any]]:
        """Get year-wise performance data (returns comparison with index)."""
        symbol_series = f"{symbol.upper()}EQN"
        return self._get_quote_api("getYearwiseData", symbol=symbol_series)

    def get_corporate_announcements_quote(
        self, symbol: str, no_of_records: int = 5
    ) -> list[dict[str, Any]]:
        """Get recent corporate announcements for a symbol."""
        return self._get_quote_api(
            "getCorporateAnnouncement",
            symbol=symbol.upper(),
            marketApiType="equities",
            noOfRecords=str(no_of_records),
        )

    def get_corp_actions(
        self, symbol: str, no_of_records: int = 5
    ) -> list[dict[str, Any]]:
        """Get corporate actions (dividends, bonus, splits)."""
        return self._get_quote_api(
            "getCorpAction",
            symbol=symbol.upper(),
            marketApiType="equities",
            noOfRecords=str(no_of_records),
        )

    def get_board_meetings(
        self, symbol: str, no_of_records: int = 4
    ) -> list[dict[str, Any]]:
        """Get board meeting information."""
        return self._get_quote_api(
            "getCorpBoardMeeting",
            symbol=symbol.upper(),
            marketApiType="equities",
            type="W",
            noOfRecords=str(no_of_records),
        )

    def get_integrated_filing_data(self, symbol: str) -> list[dict[str, Any]]:
        """Get integrated filing data (standalone and consolidated financials)."""
        return self._get_quote_api("getIntegratedFilingData", symbol=symbol.upper())

    def get_derivatives_most_active(
        self, symbol: str, call_type: str = "C"
    ) -> dict[str, Any]:
        """Get most active derivatives (calls/puts).

        Args:
            symbol: Stock symbol
            call_type: "C" for calls, "P" for puts, "O" for overall
        """
        return self._get_quote_api(
            "getDerivativesMostActive",
            symbol=symbol.upper(),
            callType=call_type,
        )

    def get_symbol_derivatives_data(self, symbol: str) -> dict[str, Any]:
        """Get detailed derivatives data (futures and options)."""
        return self._get_quote_api("getSymbolDerivativesData", symbol=symbol.upper())

    def get_symbol_derivatives_filter(self, symbol: str) -> dict[str, Any]:
        """Get derivatives filter options (expiry dates, etc.)."""
        return self._get_quote_api(
            "getSymbolDerivativesFilter",
            symbol=symbol.upper(),
            isSymbolIndex="S",
        )

    def get_annual_reports_quote(
        self, symbol: str, no_of_records: int = 3
    ) -> list[dict[str, Any]]:
        """Get annual report links."""
        return self._get_quote_api(
            "getCorpAnnualReport",
            symbol=symbol.upper(),
            marketApiType="equities",
            noOfRecords=str(no_of_records),
        )

    def get_option_chain_dropdown(self, symbol: str) -> dict[str, Any]:
        """Get option chain dropdown data (expiry dates and strike prices)."""
        return self._get_quote_api("getOptionChainDropdown", symbol=symbol.upper())

    def get_option_chain_data(self, symbol: str, expiry_date: str) -> dict[str, Any]:
        """Get full option chain data for a specific expiry.

        Args:
            symbol: Stock symbol
            expiry_date: Expiry date in format "DD-Mon-YYYY" (e.g., "27-Jan-2026")
        """
        return self._get_quote_api(
            "getOptionChainData",
            symbol=symbol.upper(),
            params=f"expiryDate={expiry_date}",
        )

    def get_brsr_reports(self, symbol: str) -> list[dict[str, Any]]:
        """Get BRSR (Business Responsibility and Sustainability Report) links."""
        return self._get_quote_api("getCorpBrsr", symbol=symbol.upper())

    def get_index_list(self, symbol: str) -> list[str]:
        """Get list of indices the stock belongs to."""
        return self._get_quote_api("getIndexList", symbol=symbol.upper())

    # Event Calendar API methods
    def get_event_calendar(
        self,
        symbol: str,
        issuer: str | None = None,
        index: AnnouncementIndex = AnnouncementIndex.EQUITIES,
    ) -> list[CorporateEvent]:
        """Get corporate event calendar for a symbol.

        This returns historical and upcoming corporate events including:
        - Financial results announcements
        - Dividend declarations
        - Bonus issues
        - Fund raising
        - Board meetings
        - Demergers and restructuring

        Args:
            symbol: Stock symbol (e.g., "RELIANCE")
            issuer: Company name (optional, used for filtering)
            index: Index type (default: equities)

        Returns:
            List of CorporateEvent objects sorted by date (oldest first)
        """
        params: dict[str, str] = {
            "index": index.value,
            "symbol": symbol.upper(),
        }

        if issuer:
            params["issuer"] = issuer

        response = self._http.get_json("/api/event-calendar", params=params)

        if not isinstance(response, list):
            return []

        events = []
        for item in response:
            try:
                event = CorporateEvent.model_validate(item)
                events.append(event)
            except Exception:
                # Skip invalid entries
                continue

        return events

    def get_event_calendar_by_date_range(
        self,
        symbol: str,
        from_date: date,
        to_date: date,
        issuer: str | None = None,
        index: AnnouncementIndex = AnnouncementIndex.EQUITIES,
    ) -> list[CorporateEvent]:
        """Get corporate events within a date range.

        Args:
            symbol: Stock symbol (e.g., "RELIANCE")
            from_date: Start date for filtering
            to_date: End date for filtering
            issuer: Company name (optional)
            index: Index type (default: equities)

        Returns:
            List of CorporateEvent objects within the date range
        """
        params: dict[str, str] = {
            "index": index.value,
            "symbol": symbol.upper(),
            "from_date": from_date.strftime("%d-%m-%Y"),
            "to_date": to_date.strftime("%d-%m-%Y"),
        }

        if issuer:
            params["issuer"] = issuer

        response = self._http.get_json("/api/event-calendar", params=params)

        if not isinstance(response, list):
            return []

        events = []
        for item in response:
            try:
                event = CorporateEvent.model_validate(item)
                events.append(event)
            except Exception:
                continue

        return events

    def get_upcoming_events(
        self,
        symbol: str,
        days_ahead: int = 90,
        index: AnnouncementIndex = AnnouncementIndex.EQUITIES,
    ) -> list[CorporateEvent]:
        """Get upcoming corporate events for a symbol.

        Convenience method that filters events from today onwards.

        Args:
            symbol: Stock symbol
            days_ahead: Number of days to look ahead (default: 90)
            index: Index type (default: equities)

        Returns:
            List of upcoming CorporateEvent objects
        """
        from datetime import timedelta

        today = date.today()
        future_date = today + timedelta(days=days_ahead)

        all_events = self.get_event_calendar(symbol=symbol, index=index)

        # Filter for upcoming events
        upcoming = [e for e in all_events if e.event_date >= today and e.event_date <= future_date]
        return sorted(upcoming, key=lambda e: e.event_date)

    # Insider Trading (PIT) API methods
    def get_insider_trading_plans(
        self,
        index: AnnouncementIndex = AnnouncementIndex.EQUITIES,
    ) -> list[InsiderTradingPlan]:
        """Get list of insider trading plans.

        Returns pre-announced trading plans submitted by company insiders
        under SEBI's Prohibition of Insider Trading regulations.

        Args:
            index: Index type (default: equities)

        Returns:
            List of InsiderTradingPlan objects sorted by date (newest first)
        """
        params: dict[str, str] = {
            "index": index.value,
        }

        response = self._http.get_json("/api/corporate-insider-plan", params=params)

        if not isinstance(response, list):
            return []

        plans = []
        for item in response:
            try:
                plan = InsiderTradingPlan.model_validate(item)
                plans.append(plan)
            except Exception:
                continue

        return plans

    def get_insider_transactions(
        self,
        symbol: str,
        issuer: str | None = None,
        index: AnnouncementIndex = AnnouncementIndex.EQUITIES,
    ) -> InsiderTransactionResponse:
        """Get insider trading transactions for a symbol.

        Returns buy/sell transactions by company insiders including
        promoters, directors, key managerial personnel, and designated employees.

        Args:
            symbol: Stock symbol (e.g., "RELIANCE")
            issuer: Company name (optional, for filtering)
            index: Index type (default: equities)

        Returns:
            InsiderTransactionResponse containing list of transactions
            and acquirer names
        """
        params: dict[str, str] = {
            "index": index.value,
            "symbol": symbol.upper(),
        }

        if issuer:
            params["issuer"] = issuer

        response = self._http.get_json("/api/corporates-pit", params=params)

        if not isinstance(response, dict):
            return InsiderTransactionResponse(acqNameList=[], data=[])

        return InsiderTransactionResponse.model_validate(response)

    def get_recent_insider_buys(
        self,
        symbol: str,
        limit: int = 10,
    ) -> list[InsiderTransaction]:
        """Get recent insider buy transactions for a symbol.

        Convenience method to filter only buy transactions.

        Args:
            symbol: Stock symbol
            limit: Maximum number of transactions to return

        Returns:
            List of InsiderTransaction objects (buys only)
        """
        response = self.get_insider_transactions(symbol)
        return response.buy_transactions[:limit]

    def get_recent_insider_sells(
        self,
        symbol: str,
        limit: int = 10,
    ) -> list[InsiderTransaction]:
        """Get recent insider sell transactions for a symbol.

        Convenience method to filter only sell transactions.

        Args:
            symbol: Stock symbol
            limit: Maximum number of transactions to return

        Returns:
            List of InsiderTransaction objects (sells only)
        """
        response = self.get_insider_transactions(symbol)
        return response.sell_transactions[:limit]

    def get_promoter_transactions(
        self,
        symbol: str,
        limit: int = 10,
    ) -> list[InsiderTransaction]:
        """Get promoter transactions for a symbol.

        Convenience method to filter only promoter transactions.

        Args:
            symbol: Stock symbol
            limit: Maximum number of transactions to return

        Returns:
            List of InsiderTransaction objects (promoters only)
        """
        response = self.get_insider_transactions(symbol)
        return response.promoter_transactions[:limit]

    # Option Chain API methods
    def get_option_contract_info(
        self,
        symbol: str,
    ) -> OptionContractInfo:
        """Get option contract information for a symbol.

        Returns available expiry dates and strike prices for options.

        Args:
            symbol: Stock symbol (e.g., "GAIL", "RELIANCE", "NIFTY")

        Returns:
            OptionContractInfo with expiry dates and strike prices
        """
        params: dict[str, str] = {
            "symbol": symbol.upper(),
        }

        response = self._http.get_json("/api/option-chain-contract-info", params=params)

        if not isinstance(response, dict):
            return OptionContractInfo(expiryDates=[], strikePrice=[])

        return OptionContractInfo.model_validate(response)

    def get_option_chain(
        self,
        symbol: str,
        expiry: str,
        security_type: str = "Equity",
    ) -> OptionChainResponse:
        """Get full option chain data for a symbol and expiry.

        Returns complete option chain with CE (call) and PE (put) data
        for all strike prices, including:
        - Open Interest (OI) and change in OI
        - Implied Volatility (IV)
        - Last traded price (LTP)
        - Bid/Ask prices and quantities
        - Volume data

        Args:
            symbol: Stock symbol (e.g., "GAIL", "RELIANCE", "NIFTY")
            expiry: Expiry date in format "DD-Mon-YYYY" (e.g., "27-Jan-2026")
            security_type: Type of security ("Equity" or "Index")

        Returns:
            OptionChainResponse with all strike data
        """
        params: dict[str, str] = {
            "type": security_type,
            "symbol": symbol.upper(),
            "expiry": expiry,
        }

        response = self._http.get_json("/api/option-chain-v3", params=params)

        if not isinstance(response, dict):
            return OptionChainResponse(timestamp="", underlyingValue=0, data=[])

        # Parse the records into OptionChainStrike objects
        records = response.get("records", {})
        timestamp = records.get("timestamp", "")
        underlying_value = records.get("underlyingValue", 0)
        data = records.get("data", [])

        strikes = []
        for item in data:
            try:
                strike = OptionChainStrike.model_validate(item)
                strikes.append(strike)
            except Exception:
                continue

        return OptionChainResponse(
            timestamp=timestamp,
            underlyingValue=underlying_value,
            data=strikes,
        )

    def get_option_chain_analysis(
        self,
        symbol: str,
        expiry: str,
        security_type: str = "Equity",
    ) -> OptionChainAnalysis:
        """Get option chain analysis summary for a symbol and expiry.

        Convenience method that fetches option chain data and creates
        an analysis summary with:
        - PCR (Put-Call Ratio)
        - Max OI strikes for calls and puts
        - ATM strike data with IV
        - Support/Resistance levels

        Args:
            symbol: Stock symbol
            expiry: Expiry date in format "DD-Mon-YYYY"
            security_type: Type of security ("Equity" or "Index")

        Returns:
            OptionChainAnalysis with summary data
        """
        chain = self.get_option_chain(symbol, expiry, security_type)
        return OptionChainAnalysis.from_option_chain(symbol, expiry, chain)

    def get_near_month_option_chain(
        self,
        symbol: str,
        security_type: str = "Equity",
    ) -> OptionChainResponse | None:
        """Get option chain for the nearest expiry date.

        Convenience method that automatically selects the nearest expiry.

        Args:
            symbol: Stock symbol
            security_type: Type of security ("Equity" or "Index")

        Returns:
            OptionChainResponse or None if no expiry available
        """
        contract_info = self.get_option_contract_info(symbol)
        if not contract_info.expiry_dates:
            return None

        near_month = contract_info.expiry_dates[0]
        return self.get_option_chain(symbol, near_month, security_type)

    def get_option_chain_pcr(
        self,
        symbol: str,
        expiry: str | None = None,
        security_type: str = "Equity",
    ) -> dict[str, float]:
        """Get Put-Call Ratio data for a symbol.

        Args:
            symbol: Stock symbol
            expiry: Expiry date (optional, uses near month if not provided)
            security_type: Type of security ("Equity" or "Index")

        Returns:
            Dictionary with PCR data:
            - pcr: Put-Call Ratio
            - total_ce_oi: Total call open interest
            - total_pe_oi: Total put open interest
        """
        if expiry is None:
            contract_info = self.get_option_contract_info(symbol)
            if not contract_info.expiry_dates:
                return {"pcr": 0, "total_ce_oi": 0, "total_pe_oi": 0}
            expiry = contract_info.expiry_dates[0]

        chain = self.get_option_chain(symbol, expiry, security_type)
        return {
            "pcr": chain.pcr,
            "total_ce_oi": chain.total_ce_oi,
            "total_pe_oi": chain.total_pe_oi,
        }

    def get_max_pain(
        self,
        symbol: str,
        expiry: str | None = None,
        security_type: str = "Equity",
    ) -> dict[str, float | int]:
        """Get max pain strike and related data.

        Max pain is the strike price where option writers would have
        minimum losses. It's often where the underlying tends to settle
        at expiry.

        Args:
            symbol: Stock symbol
            expiry: Expiry date (optional, uses near month if not provided)
            security_type: Type of security ("Equity" or "Index")

        Returns:
            Dictionary with max pain data:
            - max_ce_oi_strike: Strike with highest call OI (resistance)
            - max_ce_oi: Highest call OI value
            - max_pe_oi_strike: Strike with highest put OI (support)
            - max_pe_oi: Highest put OI value
            - underlying_value: Current spot price
        """
        if expiry is None:
            contract_info = self.get_option_contract_info(symbol)
            if not contract_info.expiry_dates:
                return {
                    "max_ce_oi_strike": 0,
                    "max_ce_oi": 0,
                    "max_pe_oi_strike": 0,
                    "max_pe_oi": 0,
                    "underlying_value": 0,
                }
            expiry = contract_info.expiry_dates[0]

        chain = self.get_option_chain(symbol, expiry, security_type)
        max_ce = chain.max_ce_oi_strike
        max_pe = chain.max_pe_oi_strike

        return {
            "max_ce_oi_strike": max_ce[0],
            "max_ce_oi": max_ce[1],
            "max_pe_oi_strike": max_pe[0],
            "max_pe_oi": max_pe[1],
            "underlying_value": chain.underlying_value,
        }

    # OI Spurts (Open Interest Changes) API methods
    def get_oi_spurts(self) -> OISpurtsResponse:
        """Get stocks with unusual open interest changes.

        This API returns stocks showing significant changes in open interest,
        which can indicate unusual derivative activity. Useful for:
        - Identifying stocks with OI buildup (potential trend continuation)
        - Spotting long/short unwinding (potential reversals)
        - Finding high activity derivatives

        Returns:
            OISpurtsResponse containing list of OI spurt data
        """
        response = self._http.get_json("/api/live-analysis-oi-spurts-underlyings")

        # API returns {"data": [...]} structure
        if isinstance(response, dict):
            data_list = response.get("data", [])
        elif isinstance(response, list):
            data_list = response
        else:
            return OISpurtsResponse(data=[])

        spurts = []
        for item in data_list:
            try:
                spurt = OISpurtData.model_validate(item)
                spurts.append(spurt)
            except Exception:
                # Skip invalid entries
                continue

        return OISpurtsResponse(data=spurts)

    def get_oi_gainers(self, limit: int = 20) -> list[OISpurtData]:
        """Get stocks with highest OI buildup (increasing OI).

        OI buildup typically indicates new positions being created,
        which can signal trend continuation.

        Args:
            limit: Maximum number of results to return

        Returns:
            List of OISpurtData sorted by % OI change (descending)
        """
        response = self.get_oi_spurts()
        return response.oi_gainers[:limit]

    def get_oi_losers(self, limit: int = 20) -> list[OISpurtData]:
        """Get stocks with highest OI unwinding (decreasing OI).

        OI unwinding typically indicates positions being closed,
        which can signal trend exhaustion or reversal.

        Args:
            limit: Maximum number of results to return

        Returns:
            List of OISpurtData sorted by % OI change (ascending)
        """
        response = self.get_oi_spurts()
        return response.oi_losers[:limit]

    def get_symbol_oi_spurt(self, symbol: str) -> OISpurtData | None:
        """Get OI spurt data for a specific symbol.

        Args:
            symbol: Stock symbol (e.g., "RELIANCE", "TCS")

        Returns:
            OISpurtData or None if symbol not found in spurts
        """
        response = self.get_oi_spurts()
        return response.get_by_symbol(symbol)

    # Most Active Securities API methods
    def get_most_active_equities(
        self,
        sort_by: str = "value",
    ) -> MostActiveResponse:
        """Get most active equities by value or volume.

        Args:
            sort_by: Sort criteria - "value" (default) or "volume"

        Returns:
            MostActiveResponse containing list of most active equities
        """
        params = {"index": sort_by}
        response = self._http.get_json("/api/live-analysis-most-active-securities", params=params)

        if not isinstance(response, dict) or "data" not in response:
            return MostActiveResponse(equities=[])

        equities = []
        for item in response.get("data", []):
            try:
                equity = MostActiveEquity.model_validate(item)
                equities.append(equity)
            except Exception:
                continue

        return MostActiveResponse(
            equities=equities,
            timestamp=response.get("timestamp"),
        )

    def get_most_active_sme(self, sort_by: str = "volume") -> MostActiveSMEResponse:
        """Get most active SME securities by volume.

        Args:
            sort_by: Sort criteria - "volume" (default) or "value"

        Returns:
            MostActiveSMEResponse containing list of most active SME stocks
        """
        params = {"index": sort_by}
        response = self._http.get_json("/api/live-analysis-most-active-sme", params=params)

        if not isinstance(response, dict) or "data" not in response:
            return MostActiveSMEResponse(data=[])

        sme_list = []
        for item in response.get("data", []):
            try:
                sme = MostActiveSME.model_validate(item)
                sme_list.append(sme)
            except Exception:
                continue

        return MostActiveSMEResponse(
            data=sme_list,
            timestamp=response.get("timestamp"),
        )

    def get_most_active_etf(self, sort_by: str = "volume") -> MostActiveETFResponse:
        """Get most active ETFs by volume.

        Args:
            sort_by: Sort criteria - "volume" (default) or "value"

        Returns:
            MostActiveETFResponse containing list of most active ETFs with NAV data
        """
        params = {"index": sort_by}
        response = self._http.get_json("/api/live-analysis-most-active-etf", params=params)

        if not isinstance(response, dict) or "data" not in response:
            return MostActiveETFResponse(data=[])

        etf_list = []
        for item in response.get("data", []):
            try:
                etf = MostActiveETF.model_validate(item)
                etf_list.append(etf)
            except Exception:
                continue

        return MostActiveETFResponse(
            data=etf_list,
            nav_date=response.get("navDate"),
            timestamp=response.get("timestamp"),
            nav_data=response.get("navData", {}),
        )

    def get_price_gainers(self, min_change: int = 20) -> PriceVariationsResponse:
        """Get stocks with significant price gains.

        Args:
            min_change: Minimum percentage change filter (default: 20%)
                Options: 20 (SecGtr20), 10 (SecGtr10), 5 (SecGtr5), 2 (SecGtr2)

        Returns:
            PriceVariationsResponse containing list of price gainers
        """
        key_map = {20: "SecGtr20", 10: "SecGtr10", 5: "SecGtr5", 2: "SecGtr2"}
        key = key_map.get(min_change, "SecGtr20")

        params = {"index": "gainers", "key": key}
        try:
            response = self._http.get_json("/api/live-analysis-variations", params=params)
        except Exception:
            # API may return empty response for some keys - handle gracefully
            return PriceVariationsResponse(data=[])

        if not isinstance(response, dict):
            return PriceVariationsResponse(data=[])

        # API returns nested structure: {"NIFTY": {"data": [...]}, "allSec": {"data": [...]}, ...}
        # Try to get data from the key or from allSec
        data_list = []
        if key in response and isinstance(response[key], dict):
            data_list = response[key].get("data", [])
        elif "allSec" in response and isinstance(response["allSec"], dict):
            data_list = response["allSec"].get("data", [])
        elif "data" in response:
            # Fallback to direct data key
            data_list = response.get("data", [])

        variations = []
        for item in data_list:
            try:
                variation = PriceVariation.model_validate(item)
                variations.append(variation)
            except Exception:
                continue

        return PriceVariationsResponse(
            data=variations,
            timestamp=response.get("timestamp"),
        )

    def get_price_losers(self, min_change: int = 20) -> PriceVariationsResponse:
        """Get stocks with significant price losses.

        Args:
            min_change: Minimum percentage change filter (default: 20%)
                Options: 20 (SecLwr20), 10 (SecLwr10), 5 (SecLwr5), 2 (SecLwr2)

        Returns:
            PriceVariationsResponse containing list of price losers
        """
        key_map = {20: "SecLwr20", 10: "SecLwr10", 5: "SecLwr5", 2: "SecLwr2"}
        key = key_map.get(min_change, "SecLwr20")

        params = {"index": "losers", "key": key}
        try:
            response = self._http.get_json("/api/live-analysis-variations", params=params)
        except Exception:
            # API may return empty response for some keys - handle gracefully
            return PriceVariationsResponse(data=[])

        if not isinstance(response, dict):
            return PriceVariationsResponse(data=[])

        # API returns nested structure: {"NIFTY": {"data": [...]}, "allSec": {"data": [...]}, ...}
        # Try to get data from the key or from allSec
        data_list = []
        if key in response and isinstance(response[key], dict):
            data_list = response[key].get("data", [])
        elif "allSec" in response and isinstance(response["allSec"], dict):
            data_list = response["allSec"].get("data", [])
        elif "data" in response:
            # Fallback to direct data key
            data_list = response.get("data", [])

        variations = []
        for item in data_list:
            try:
                variation = PriceVariation.model_validate(item)
                variations.append(variation)
            except Exception:
                continue

        return PriceVariationsResponse(
            data=variations,
            timestamp=response.get("timestamp"),
        )

    def get_volume_gainers(self) -> VolumeGainersResponse:
        """Get stocks with unusual volume increase.

        Returns stocks where current volume significantly exceeds
        the 1-week and 2-week average volume.

        Returns:
            VolumeGainersResponse containing list of volume gainers
        """
        response = self._http.get_json("/api/live-analysis-volume-gainers")

        if not isinstance(response, dict) or "data" not in response:
            return VolumeGainersResponse(data=[])

        gainers = []
        for item in response.get("data", []):
            try:
                gainer = VolumeGainer.model_validate(item)
                gainers.append(gainer)
            except Exception:
                continue

        return VolumeGainersResponse(
            data=gainers,
            timestamp=response.get("timestamp"),
        )

    # Advances/Declines (Market Breadth) API methods
    def get_advances(self) -> AdvancesResponse:
        """Get list of advancing stocks with market breadth data.

        This API returns stocks that are trading higher than their previous close,
        along with overall market breadth statistics (advances, declines, unchanged).

        Returns:
            AdvancesResponse containing list of advancing stocks and count summary
        """
        response = self._http.get_json("/api/live-analysis-advance")

        if not isinstance(response, dict):
            return AdvancesResponse()

        timestamp = response.get("timestamp", "")
        advance_data = response.get("advance", {})

        # Parse the section data
        section = AdvancesDeclinesSectionData(
            indetifier=advance_data.get("indetifier", "Advances"),
            count=MarketBreadthCount.model_validate(advance_data.get("count", {})),
            data=[],
        )

        for item in advance_data.get("data", []):
            try:
                mover = MarketMover.model_validate(item)
                section.data.append(mover)
            except Exception:
                continue

        return AdvancesResponse(timestamp=timestamp, advance=section)

    def get_declines(self) -> DeclinesResponse:
        """Get list of declining stocks with market breadth data.

        This API returns stocks that are trading lower than their previous close,
        along with overall market breadth statistics.

        Returns:
            DeclinesResponse containing list of declining stocks and count summary
        """
        response = self._http.get_json("/api/live-analysis-decline")

        if not isinstance(response, dict):
            return DeclinesResponse()

        timestamp = response.get("timestamp", "")
        decline_data = response.get("decline", {})

        # Parse the section data
        section = AdvancesDeclinesSectionData(
            indetifier=decline_data.get("indetifier", "Declines"),
            count=MarketBreadthCount.model_validate(decline_data.get("count", {})),
            data=[],
        )

        for item in decline_data.get("data", []):
            try:
                mover = MarketMover.model_validate(item)
                section.data.append(mover)
            except Exception:
                continue

        return DeclinesResponse(timestamp=timestamp, decline=section)

    def get_market_breadth_snapshot(self) -> MarketBreadthSnapshot:
        """Get combined market breadth snapshot with advances and declines.

        Convenience method that fetches both advances and declines data
        and combines them into a single snapshot.

        Returns:
            MarketBreadthSnapshot with advances, declines, and summary
        """
        advances_resp = self.get_advances()
        declines_resp = self.get_declines()

        return MarketBreadthSnapshot(
            timestamp=advances_resp.timestamp or declines_resp.timestamp,
            count=advances_resp.count,
            advances=advances_resp.stocks,
            declines=declines_resp.stocks,
        )

    def get_top_gainers(self, limit: int = 20) -> list[MarketMover]:
        """Get top gaining stocks sorted by percentage change.

        Args:
            limit: Maximum number of stocks to return

        Returns:
            List of MarketMover objects sorted by pchange (descending)
        """
        response = self.get_advances()
        return response.top_gainers[:limit]

    def get_top_losers(self, limit: int = 20) -> list[MarketMover]:
        """Get top losing stocks sorted by percentage change.

        Args:
            limit: Maximum number of stocks to return

        Returns:
            List of MarketMover objects sorted by pchange (ascending)
        """
        response = self.get_declines()
        return response.top_losers[:limit]

    def get_advance_decline_ratio(self) -> dict[str, Any]:
        """Get current advance/decline ratio and market sentiment.

        Returns:
            Dictionary with market breadth data:
            - advances: Number of advancing stocks
            - declines: Number of declining stocks
            - unchanged: Number of unchanged stocks
            - ratio: Advance/Decline ratio
            - sentiment: Market sentiment string
        """
        response = self.get_advances()
        count = response.count

        return {
            "advances": count.advances,
            "declines": count.declines,
            "unchanged": count.unchanged,
            "total": count.total,
            "ratio": count.advance_decline_ratio,
            "advance_percentage": count.advance_percentage,
            "decline_percentage": count.decline_percentage,
            "sentiment": count.market_sentiment,
        }

    def get_symbol_advance_decline_data(self, symbol: str) -> MarketMover | None:
        """Get advance/decline data for a specific symbol.

        Searches both advances and declines lists for the symbol.

        Args:
            symbol: Stock symbol (e.g., "RELIANCE", "TCS")

        Returns:
            MarketMover or None if symbol not found
        """
        # Check in advances
        advances_resp = self.get_advances()
        result = advances_resp.get_by_symbol(symbol)
        if result:
            return result

        # Check in declines
        declines_resp = self.get_declines()
        return declines_resp.get_by_symbol(symbol)

    def get_symbol_summary_data(self, symbol: str) -> dict[str, Any]:
        """Fetch all relevant data for generating a symbol summary.

        Returns a dict containing all the data needed to generate a summary.
        """
        symbol = symbol.upper()
        metadata = self.get_metadata(symbol)

        # Build base data
        data = {
            "symbol_name": self.get_symbol_name(symbol),
            "metadata": metadata,
            "symbol_data": self.get_symbol_data(symbol),
            "shareholding": self.get_shareholding_pattern(symbol),
            "financials": self.get_financial_status(symbol),
            "integrated_filing": self.get_integrated_filing_data(symbol),
            "yearwise": self.get_yearwise_data(symbol),
            "announcements": self.get_corporate_announcements_quote(symbol, 3),
            "corp_actions": self.get_corp_actions(symbol, 3),
            "board_meetings": self.get_board_meetings(symbol, 2),
            "annual_reports": self.get_annual_reports_quote(symbol, 3),
            "brsr_reports": self.get_brsr_reports(symbol),
            "index_list": self.get_index_list(symbol),
            "upcoming_events": self.get_upcoming_events(symbol, days_ahead=180),
        }

        # Add derivatives data only if F&O enabled
        if metadata.get("isFNOSec") == "true":
            try:
                data["derivatives_filter"] = self.get_symbol_derivatives_filter(symbol)
                data["derivatives_data"] = self.get_symbol_derivatives_data(symbol)
                data["most_active_calls"] = self.get_derivatives_most_active(symbol, "C")
                data["most_active_puts"] = self.get_derivatives_most_active(symbol, "P")
                data["most_active_by_oi"] = self.get_derivatives_most_active(symbol, "O")

                # Get option chain for near month expiry
                option_dropdown = self.get_option_chain_dropdown(symbol)
                data["option_chain_dropdown"] = option_dropdown
                expiry_dates = option_dropdown.get("expiryDates", [])
                if expiry_dates:
                    near_month_expiry = expiry_dates[0]
                    data["option_chain"] = self.get_option_chain_data(symbol, near_month_expiry)
            except Exception:
                # Derivatives data not available
                pass

        return data

    # Price Band Hitters API methods
    def get_price_band_hitters(self) -> PriceBandResponse:
        """Get stocks hitting upper and lower price bands.

        Price band hitters are stocks that have hit their circuit limit
        (upper or lower) during the trading session.

        Returns:
            PriceBandResponse containing upper and lower band hitters
        """
        response = self._http.get_json("/api/live-analysis-price-band-hitter")

        if not isinstance(response, dict):
            return PriceBandResponse()

        timestamp = response.get("timestamp", "")

        # Parse upper band hitters
        upper_data = response.get("upper", {})
        upper_category = self._parse_price_band_category(upper_data)

        # Parse lower band hitters
        lower_data = response.get("lower", {})
        lower_category = self._parse_price_band_category(lower_data)

        # Parse count summary
        count_data = response.get("count", {})
        count = None
        if count_data:
            try:
                count = PriceBandCount.model_validate(count_data)
            except Exception:
                pass

        return PriceBandResponse(
            upper=upper_category,
            lower=lower_category,
            count=count,
            timestamp=timestamp,
        )

    def _parse_price_band_category(self, data: dict) -> PriceBandCategory:
        """Parse a price band category (upper or lower) from API response."""
        category = PriceBandCategory()

        # Parse each section
        for section_key in ["AllSec", "SecGtr20", "SecGtr10", "SecLwr10"]:
            section_data = data.get(section_key, [])
            hitters = []
            for item in section_data:
                try:
                    hitter = PriceBandHitter.model_validate(item)
                    hitters.append(hitter)
                except Exception:
                    continue

            if section_key == "AllSec":
                category.all_securities = hitters
            elif section_key == "SecGtr20":
                category.securities_gt_20cr = hitters
            elif section_key == "SecGtr10":
                category.securities_gt_10cr = hitters
            elif section_key == "SecLwr10":
                category.securities_lt_10cr = hitters

        return category

    def get_upper_band_hitters(self, min_turnover: int = 0) -> list[PriceBandHitter]:
        """Get stocks hitting upper price band (circuit limit).

        Args:
            min_turnover: Minimum turnover filter in crores
                0 = All securities, 20 = >20cr, 10 = >10cr

        Returns:
            List of stocks at upper circuit
        """
        response = self.get_price_band_hitters()

        if min_turnover >= 20:
            return response.upper.securities_gt_20cr
        elif min_turnover >= 10:
            return response.upper.securities_gt_10cr
        else:
            return response.upper.all_securities

    def get_lower_band_hitters(self, min_turnover: int = 0) -> list[PriceBandHitter]:
        """Get stocks hitting lower price band (circuit limit).

        Args:
            min_turnover: Minimum turnover filter in crores
                0 = All securities, 20 = >20cr, 10 = >10cr

        Returns:
            List of stocks at lower circuit
        """
        response = self.get_price_band_hitters()

        if min_turnover >= 20:
            return response.lower.securities_gt_20cr
        elif min_turnover >= 10:
            return response.lower.securities_gt_10cr
        else:
            return response.lower.all_securities

    def get_price_band_summary(self) -> dict[str, int]:
        """Get summary count of price band hitters.

        Returns:
            Dictionary with counts: total, upper, lower, both
        """
        response = self.get_price_band_hitters()

        if response.count:
            return {
                "total": response.count.total,
                "upper": response.count.upper,
                "lower": response.count.lower,
                "both": response.count.both,
            }

        # Calculate from data if count not in response
        return {
            "total": response.upper_count + response.lower_count,
            "upper": response.upper_count,
            "lower": response.lower_count,
            "both": 0,
        }

    def is_at_price_band(self, symbol: str) -> tuple[bool, str | None]:
        """Check if a symbol is at upper or lower price band.

        Args:
            symbol: Stock symbol to check

        Returns:
            Tuple of (is_at_band, band_type) where band_type is 'upper', 'lower', or None
        """
        response = self.get_price_band_hitters()
        hitter, band_type = response.get_by_symbol(symbol)
        return hitter is not None, band_type

    # Pre-Open Market API methods
    def get_pre_open_data(self, index: str = "NIFTY") -> PreOpenResponse:
        """Get pre-open market data for an index.

        Pre-open session runs from 9:00 AM to 9:15 AM IST. This API returns
        the Indicative Equilibrium Price (IEP), order book, and stock-wise
        pre-open data.

        Args:
            index: Index key for pre-open data. Common values:
                - "NIFTY" - NIFTY 50 stocks
                - "BANKNIFTY" - Bank NIFTY stocks
                - "NIFTYIT" - NIFTY IT stocks
                - "FO" - F&O securities
                - "ALL" - All securities

        Returns:
            PreOpenResponse containing pre-open data for all stocks in the index
        """
        params = {"key": index}
        response = self._http.get_json("/api/market-data-pre-open", params=params)

        if not isinstance(response, dict):
            return PreOpenResponse()

        # Parse top-level counts
        declines = response.get("declines", 0)
        advances = response.get("advances", 0)
        unchanged = response.get("unchanged", 0)

        # Parse stock data
        stocks = []
        data_list = response.get("data", [])
        for item in data_list:
            try:
                stock = PreOpenStock.model_validate(item)
                stocks.append(stock)
            except Exception:
                continue

        return PreOpenResponse(
            declines=declines,
            advances=advances,
            unchanged=unchanged,
            data=stocks,
        )

    def get_nifty_pre_open(self) -> PreOpenResponse:
        """Get pre-open data for NIFTY 50 stocks.

        Returns:
            PreOpenResponse for NIFTY 50 stocks
        """
        return self.get_pre_open_data("NIFTY")

    def get_bank_nifty_pre_open(self) -> PreOpenResponse:
        """Get pre-open data for Bank NIFTY stocks.

        Returns:
            PreOpenResponse for Bank NIFTY stocks
        """
        return self.get_pre_open_data("BANKNIFTY")

    def get_fo_pre_open(self) -> PreOpenResponse:
        """Get pre-open data for F&O securities.

        Returns:
            PreOpenResponse for F&O securities
        """
        return self.get_pre_open_data("FO")

    def get_pre_open_gainers(self, index: str = "NIFTY", limit: int = 20) -> list[PreOpenStock]:
        """Get top gainers in pre-open session.

        Args:
            index: Index key (NIFTY, BANKNIFTY, FO, ALL)
            limit: Maximum number of results

        Returns:
            List of PreOpenStock sorted by % change (descending)
        """
        response = self.get_pre_open_data(index)
        return response.top_gainers[:limit]

    def get_pre_open_losers(self, index: str = "NIFTY", limit: int = 20) -> list[PreOpenStock]:
        """Get top losers in pre-open session.

        Args:
            index: Index key (NIFTY, BANKNIFTY, FO, ALL)
            limit: Maximum number of results

        Returns:
            List of PreOpenStock sorted by % change (ascending)
        """
        response = self.get_pre_open_data(index)
        return response.top_losers[:limit]

    def get_pre_open_sentiment(self, index: str = "NIFTY") -> dict:
        """Get pre-open market sentiment summary.

        Args:
            index: Index key (NIFTY, BANKNIFTY, FO, ALL)

        Returns:
            Dictionary with sentiment analysis
        """
        response = self.get_pre_open_data(index)

        return {
            "advances": response.advances,
            "declines": response.declines,
            "unchanged": response.unchanged,
            "total": response.total_stocks,
            "advance_decline_ratio": response.advance_decline_ratio,
            "sentiment": response.market_sentiment,
            "gapping_up_count": len(response.gapping_up),
            "gapping_down_count": len(response.gapping_down),
            "buy_pressure_count": len(response.stocks_with_buy_pressure),
            "sell_pressure_count": len(response.stocks_with_sell_pressure),
        }

    def get_pre_open_gaps(
        self, index: str = "NIFTY", min_gap_pct: float = 1.0
    ) -> dict[str, list[PreOpenStock]]:
        """Get stocks with significant gaps in pre-open.

        Args:
            index: Index key (NIFTY, BANKNIFTY, FO, ALL)
            min_gap_pct: Minimum gap percentage (default 1%)

        Returns:
            Dictionary with 'gap_up' and 'gap_down' lists
        """
        response = self.get_pre_open_data(index)

        gap_up = [
            s for s in response.gapping_up
            if s.metadata.gap_percentage >= min_gap_pct
        ]
        gap_down = [
            s for s in response.gapping_down
            if s.metadata.gap_percentage <= -min_gap_pct
        ]

        return {
            "gap_up": sorted(gap_up, key=lambda x: x.metadata.gap_percentage, reverse=True),
            "gap_down": sorted(gap_down, key=lambda x: x.metadata.gap_percentage),
        }

    def get_symbol_pre_open_data(self, symbol: str, index: str = "NIFTY") -> PreOpenStock | None:
        """Get pre-open data for a specific symbol.

        Args:
            symbol: Stock symbol
            index: Index key to search in (NIFTY, BANKNIFTY, FO, ALL)

        Returns:
            PreOpenStock or None if not found
        """
        response = self.get_pre_open_data(index)
        return response.get_by_symbol(symbol)

    def get_pre_open_snapshot(self) -> PreOpenMarketSnapshot:
        """Get pre-open data for all major indices.

        Returns:
            PreOpenMarketSnapshot containing data for NIFTY 50, Bank NIFTY, etc.
        """
        nifty_50 = self.get_pre_open_data("NIFTY")
        nifty_bank = self.get_pre_open_data("BANKNIFTY")
        fo_securities = self.get_pre_open_data("FO")

        return PreOpenMarketSnapshot(
            nifty_50=nifty_50,
            nifty_bank=nifty_bank,
            fo_securities=fo_securities,
        )

    def get_pre_open_buy_pressure(
        self, index: str = "NIFTY", min_ratio: float = 1.5
    ) -> list[PreOpenStock]:
        """Get stocks with significant buy pressure in pre-open.

        Stocks where total buy quantity significantly exceeds sell quantity.

        Args:
            index: Index key (NIFTY, BANKNIFTY, FO, ALL)
            min_ratio: Minimum buy/sell ratio (default 1.5)

        Returns:
            List of stocks sorted by buy/sell ratio (descending)
        """
        response = self.get_pre_open_data(index)

        filtered = [s for s in response.data if s.buy_sell_ratio >= min_ratio]
        return sorted(filtered, key=lambda x: x.buy_sell_ratio, reverse=True)

    def get_pre_open_sell_pressure(
        self, index: str = "NIFTY", max_ratio: float = 0.67
    ) -> list[PreOpenStock]:
        """Get stocks with significant sell pressure in pre-open.

        Stocks where total sell quantity significantly exceeds buy quantity.

        Args:
            index: Index key (NIFTY, BANKNIFTY, FO, ALL)
            max_ratio: Maximum buy/sell ratio (default 0.67)

        Returns:
            List of stocks sorted by buy/sell ratio (ascending)
        """
        response = self.get_pre_open_data(index)

        filtered = [s for s in response.data if s.buy_sell_ratio <= max_ratio]
        return sorted(filtered, key=lambda x: x.buy_sell_ratio)

    # Index Constituents API methods
    def get_index_master(self) -> IndexMaster:
        """Get master list of all available indices on NSE.

        Returns all indices categorized by type:
        - Derivatives Eligible (NIFTY 50, NIFTY BANK, etc.)
        - Broad Market (NIFTY 100, NIFTY 500, etc.)
        - Sectoral (NIFTY IT, NIFTY PHARMA, etc.)
        - Thematic (NIFTY INFRA, NIFTY PSE, etc.)
        - Strategy (NIFTY ALPHA 50, NIFTY LOW VOLATILITY 50, etc.)
        - Others (F&O Securities, Permitted to Trade)

        Returns:
            IndexMaster containing all available indices
        """
        response = self._http.get_json("/api/equity-master")

        if not isinstance(response, dict):
            return IndexMaster()

        return IndexMaster.model_validate(response)

    def get_index_constituents(self, index_name: str) -> IndexConstituentsResponse:
        """Get all constituents of an index with their price data.

        Args:
            index_name: Index name (e.g., "NIFTY 50", "NIFTY BANK", "NIFTY IT")
                       Use get_index_master() to see all available indices.

        Returns:
            IndexConstituentsResponse containing index data and all constituents
        """
        params = {"index": index_name}
        response = self._http.get_json("/api/equity-stockIndices", params=params)

        if not isinstance(response, dict):
            return IndexConstituentsResponse()

        # Parse advance/decline data
        advance_data = response.get("advance", {})
        advance = IndexAdvanceDecline.model_validate(advance_data) if advance_data else IndexAdvanceDecline()

        # Parse constituent data
        constituents = []
        data_list = response.get("data", [])
        for item in data_list:
            try:
                constituent = IndexConstituent.model_validate(item)
                constituents.append(constituent)
            except Exception:
                continue

        return IndexConstituentsResponse(
            name=response.get("name", index_name),
            advance=advance,
            timestamp=response.get("timestamp", ""),
            data=constituents,
        )

    def get_nifty50_constituents(self) -> IndexConstituentsResponse:
        """Get NIFTY 50 index constituents.

        Returns:
            IndexConstituentsResponse for NIFTY 50
        """
        return self.get_index_constituents("NIFTY 50")

    def get_nifty_bank_constituents(self) -> IndexConstituentsResponse:
        """Get NIFTY Bank index constituents.

        Returns:
            IndexConstituentsResponse for NIFTY Bank
        """
        return self.get_index_constituents("NIFTY BANK")

    def get_nifty_it_constituents(self) -> IndexConstituentsResponse:
        """Get NIFTY IT index constituents.

        Returns:
            IndexConstituentsResponse for NIFTY IT
        """
        return self.get_index_constituents("NIFTY IT")

    def get_nifty_next50_constituents(self) -> IndexConstituentsResponse:
        """Get NIFTY Next 50 index constituents.

        Returns:
            IndexConstituentsResponse for NIFTY Next 50
        """
        return self.get_index_constituents("NIFTY NEXT 50")

    def get_nifty100_constituents(self) -> IndexConstituentsResponse:
        """Get NIFTY 100 index constituents.

        Returns:
            IndexConstituentsResponse for NIFTY 100
        """
        return self.get_index_constituents("NIFTY 100")

    def get_nifty500_constituents(self) -> IndexConstituentsResponse:
        """Get NIFTY 500 index constituents.

        Returns:
            IndexConstituentsResponse for NIFTY 500
        """
        return self.get_index_constituents("NIFTY 500")

    def get_index_symbols(self, index_name: str) -> list[str]:
        """Get list of all symbols in an index.

        Args:
            index_name: Index name (e.g., "NIFTY 50", "NIFTY BANK")

        Returns:
            List of stock symbols in the index
        """
        response = self.get_index_constituents(index_name)
        return response.symbols

    def get_index_gainers(self, index_name: str, limit: int = 10) -> list[IndexConstituent]:
        """Get top gainers in an index.

        Args:
            index_name: Index name
            limit: Maximum number of results

        Returns:
            List of top gaining stocks
        """
        response = self.get_index_constituents(index_name)
        return response.top_gainers[:limit]

    def get_index_losers(self, index_name: str, limit: int = 10) -> list[IndexConstituent]:
        """Get top losers in an index.

        Args:
            index_name: Index name
            limit: Maximum number of results

        Returns:
            List of top losing stocks
        """
        response = self.get_index_constituents(index_name)
        return response.top_losers[:limit]

    def get_index_breadth(self, index_name: str) -> dict:
        """Get market breadth for an index.

        Args:
            index_name: Index name

        Returns:
            Dictionary with advances, declines, A/D ratio, sentiment
        """
        response = self.get_index_constituents(index_name)
        advance = response.advance

        return {
            "index_name": response.name,
            "advances": advance.advances_int,
            "declines": advance.declines_int,
            "unchanged": advance.unchanged_int,
            "total": advance.total,
            "advance_decline_ratio": advance.advance_decline_ratio,
            "sentiment": advance.market_sentiment,
            "timestamp": response.timestamp,
        }

    def get_index_near_52_week_highs(
        self, index_name: str
    ) -> list[IndexConstituent]:
        """Get stocks near 52-week high in an index.

        Args:
            index_name: Index name

        Returns:
            List of stocks within 5% of 52-week high
        """
        response = self.get_index_constituents(index_name)
        return response.near_52_week_highs

    def get_index_near_52_week_lows(
        self, index_name: str
    ) -> list[IndexConstituent]:
        """Get stocks near 52-week low in an index.

        Args:
            index_name: Index name

        Returns:
            List of stocks within 5% of 52-week low
        """
        response = self.get_index_constituents(index_name)
        return response.near_52_week_lows

    def get_index_top_by_market_cap(
        self, index_name: str, limit: int = 10
    ) -> list[IndexConstituent]:
        """Get top stocks by market cap in an index.

        Args:
            index_name: Index name
            limit: Maximum number of results

        Returns:
            List of stocks sorted by market cap
        """
        response = self.get_index_constituents(index_name)
        return response.top_by_market_cap(limit)

    def get_index_top_by_volume(
        self, index_name: str, limit: int = 10
    ) -> list[IndexConstituent]:
        """Get top stocks by volume in an index.

        Args:
            index_name: Index name
            limit: Maximum number of results

        Returns:
            List of stocks sorted by volume
        """
        response = self.get_index_constituents(index_name)
        return response.top_by_volume(limit)

    def get_index_yearly_performers(
        self, index_name: str, limit: int = 10
    ) -> dict[str, list[IndexConstituent]]:
        """Get top and worst yearly performers in an index.

        Args:
            index_name: Index name
            limit: Maximum number of results for each list

        Returns:
            Dictionary with 'top' and 'worst' performer lists
        """
        response = self.get_index_constituents(index_name)
        return {
            "top": response.top_yearly_performers(limit),
            "worst": response.worst_yearly_performers(limit),
        }

    def is_symbol_in_index(self, symbol: str, index_name: str) -> bool:
        """Check if a symbol is part of an index.

        Args:
            symbol: Stock symbol
            index_name: Index name

        Returns:
            True if symbol is in the index
        """
        response = self.get_index_constituents(index_name)
        return response.get_by_symbol(symbol) is not None

    def get_symbol_index_data(
        self, symbol: str, index_name: str
    ) -> IndexConstituent | None:
        """Get data for a specific symbol from an index.

        Args:
            symbol: Stock symbol
            index_name: Index name

        Returns:
            IndexConstituent data or None if not found
        """
        response = self.get_index_constituents(index_name)
        return response.get_by_symbol(symbol)

    def get_fno_securities(self) -> IndexConstituentsResponse:
        """Get all F&O eligible securities.

        Returns:
            IndexConstituentsResponse for F&O securities
        """
        return self.get_index_constituents("SECURITIES IN F&O")

    # ==================== Charting / Historical Data ====================

    def search_chart_symbols(
        self, symbol: str, segment: str = ""
    ) -> SymbolSearchResponse:
        """Search for chart symbols by name.

        Args:
            symbol: Symbol to search for (e.g., "RELIANCE", "NIFTY")
            segment: Optional segment filter (empty for all)

        Returns:
            SymbolSearchResponse containing matching symbols
        """
        url = "https://charting.nseindia.com/v1/exchanges/symbolsDynamic"
        payload = {"symbol": symbol, "segment": segment}

        data = self._http.post_json(url, payload, ttl=CacheTTL.DAILY)

        symbols = []
        if data:
            for item in data:
                try:
                    sym = ChartSymbol(
                        symbol=item.get("symbol", ""),
                        scripcode=item.get("scripcode", ""),
                        description=item.get("description", ""),
                        type=item.get("type", "Equity"),
                    )
                    symbols.append(sym)
                except Exception:
                    continue

        return SymbolSearchResponse(query=symbol, symbols=symbols)

    def get_chart_symbol(
        self, symbol: str, symbol_type: str = "Equity"
    ) -> ChartSymbol | None:
        """Get a specific chart symbol with its scripcode.

        Args:
            symbol: Symbol to search (e.g., "RELIANCE")
            symbol_type: Type of symbol ("Equity", "Futures", "Options")

        Returns:
            ChartSymbol or None if not found
        """
        response = self.search_chart_symbols(symbol)

        # Try exact match first
        for sym in response.symbols:
            if sym.symbol_type == symbol_type:
                base = sym.base_symbol.upper()
                if base == symbol.upper():
                    return sym

        # Fall back to first match of the type
        for sym in response.symbols:
            if sym.symbol_type == symbol_type:
                return sym

        return response.symbols[0] if response.symbols else None

    def get_historical_data(
        self,
        symbol: str,
        scripcode: str | None = None,
        chart_type: str = "D",
        interval: int = 1,
        from_timestamp: int = 0,
        to_timestamp: int | None = None,
        symbol_type: str = "Equity",
    ) -> ChartDataResponse:
        """Get historical OHLCV chart data for a symbol.

        Args:
            symbol: Trading symbol (e.g., "RELIANCE-EQ")
            scripcode: Token/scripcode for the symbol (auto-fetched if not provided)
            chart_type: "D" for daily, "I" for intraday
            interval: Time interval (1 for daily, minutes for intraday)
            from_timestamp: Start timestamp (0 for all available data)
            to_timestamp: End timestamp (None for current time)
            symbol_type: "Equity", "Futures", or "Options"

        Returns:
            ChartDataResponse with OHLCV candles
        """
        import time

        # Auto-fetch scripcode if not provided
        if scripcode is None:
            chart_symbol = self.get_chart_symbol(symbol.split("-")[0], symbol_type)
            if chart_symbol is None:
                return ChartDataResponse(
                    symbol=symbol,
                    symbol_type=symbol_type,
                    chart_type=chart_type,
                    interval=interval,
                    candles=[],
                )
            scripcode = chart_symbol.scripcode
            # Use the full symbol from the chart response
            symbol = chart_symbol.symbol

        if to_timestamp is None:
            to_timestamp = int(time.time())

        url = "https://charting.nseindia.com/v1/charts/symbolHistoricalData"
        payload = {
            "token": scripcode,
            "fromDate": from_timestamp,
            "toDate": to_timestamp,
            "symbol": symbol,
            "symbolType": symbol_type,
            "chartType": chart_type,
            "timeInterval": interval,
        }

        # Use shorter TTL for intraday data
        ttl = CacheTTL.SHORT if chart_type == "I" else CacheTTL.DAILY

        data = self._http.post_json(url, payload, ttl=ttl)

        candles = []
        if data:
            for item in data:
                try:
                    candle = ChartCandle(
                        time=item.get("time", 0),
                        open=float(item.get("open", 0)),
                        high=float(item.get("high", 0)),
                        low=float(item.get("low", 0)),
                        close=float(item.get("close", 0)),
                        volume=int(item.get("volume", 0)),
                    )
                    candles.append(candle)
                except Exception:
                    continue

        return ChartDataResponse(
            symbol=symbol,
            symbol_type=symbol_type,
            chart_type=chart_type,
            interval=interval,
            candles=candles,
        )

    def get_daily_chart(
        self,
        symbol: str,
        days: int | None = None,
        from_timestamp: int = 0,
        to_timestamp: int | None = None,
    ) -> ChartDataResponse:
        """Get daily OHLCV chart data for a symbol.

        Args:
            symbol: Stock symbol (e.g., "RELIANCE")
            days: Number of days of data (alternative to timestamps)
            from_timestamp: Start timestamp (0 for all available)
            to_timestamp: End timestamp (None for current time)

        Returns:
            ChartDataResponse with daily candles
        """
        import time

        if days is not None:
            to_timestamp = int(time.time())
            from_timestamp = to_timestamp - (days * 24 * 60 * 60)

        return self.get_historical_data(
            symbol=symbol,
            chart_type="D",
            interval=1,
            from_timestamp=from_timestamp,
            to_timestamp=to_timestamp,
            symbol_type="Equity",
        )

    def get_intraday_chart(
        self,
        symbol: str,
        interval: int = 5,
        days: int = 1,
    ) -> ChartDataResponse:
        """Get intraday OHLCV chart data for a symbol.

        Args:
            symbol: Stock symbol (e.g., "RELIANCE")
            interval: Candle interval in minutes (1, 5, 15, 30, 60)
            days: Number of days of data (default 1)

        Returns:
            ChartDataResponse with intraday candles
        """
        import time

        to_timestamp = int(time.time())
        from_timestamp = to_timestamp - (days * 24 * 60 * 60)

        return self.get_historical_data(
            symbol=symbol,
            chart_type="I",
            interval=interval,
            from_timestamp=from_timestamp,
            to_timestamp=to_timestamp,
            symbol_type="Equity",
        )

    def get_index_chart(
        self,
        index_symbol: str,
        chart_type: str = "D",
        interval: int = 1,
        days: int | None = None,
    ) -> ChartDataResponse:
        """Get chart data for an index.

        Args:
            index_symbol: Index symbol (e.g., "NIFTY 50", "BANKNIFTY")
            chart_type: "D" for daily, "I" for intraday
            interval: Time interval
            days: Number of days of data

        Returns:
            ChartDataResponse with index candles
        """
        import time

        to_timestamp = int(time.time())
        from_timestamp = 0

        if days is not None:
            from_timestamp = to_timestamp - (days * 24 * 60 * 60)

        # Search for the index symbol
        response = self.search_chart_symbols(index_symbol)

        # Find the index type symbol
        index_sym = None
        for sym in response.symbols:
            if sym.symbol_type == "Index" or "index" in sym.symbol_type.lower():
                index_sym = sym
                break

        # Fall back to first result
        if index_sym is None and response.symbols:
            index_sym = response.symbols[0]

        if index_sym is None:
            return ChartDataResponse(
                symbol=index_symbol,
                symbol_type="Index",
                chart_type=chart_type,
                interval=interval,
                candles=[],
            )

        return self.get_historical_data(
            symbol=index_sym.symbol,
            scripcode=index_sym.scripcode,
            chart_type=chart_type,
            interval=interval,
            from_timestamp=from_timestamp,
            to_timestamp=to_timestamp,
            symbol_type=index_sym.symbol_type,
        )

    def get_futures_chart(
        self,
        symbol: str,
        chart_type: str = "D",
        interval: int = 1,
        days: int | None = None,
    ) -> ChartDataResponse:
        """Get chart data for a futures contract.

        Args:
            symbol: Underlying symbol (e.g., "RELIANCE", "NIFTY")
            chart_type: "D" for daily, "I" for intraday
            interval: Time interval
            days: Number of days of data

        Returns:
            ChartDataResponse with futures candles
        """
        import time

        to_timestamp = int(time.time())
        from_timestamp = 0

        if days is not None:
            from_timestamp = to_timestamp - (days * 24 * 60 * 60)

        # Search and find futures symbol
        response = self.search_chart_symbols(symbol)

        futures_sym = None
        for sym in response.symbols:
            if sym.symbol_type == "Futures":
                futures_sym = sym
                break

        if futures_sym is None:
            return ChartDataResponse(
                symbol=symbol,
                symbol_type="Futures",
                chart_type=chart_type,
                interval=interval,
                candles=[],
            )

        return self.get_historical_data(
            symbol=futures_sym.symbol,
            scripcode=futures_sym.scripcode,
            chart_type=chart_type,
            interval=interval,
            from_timestamp=from_timestamp,
            to_timestamp=to_timestamp,
            symbol_type="Futures",
        )

    # ==================== Index Summary / Index Tracker APIs ====================

    def _get_index_tracker_api(
        self, function_name: str, ttl: int = CacheTTL.SHORT, **params: Any
    ) -> dict[str, Any] | None:
        """Internal method to call index tracker API.

        Args:
            function_name: API function name (e.g., "getIndexData")
            ttl: Cache TTL in seconds
            **params: Additional query parameters

        Returns:
            JSON response data or None
        """
        query_params = {"functionName": function_name, **params}
        return self._http.get_json(
            "/api/NextApi/apiClient/indexTrackerApi",
            params=query_params,
            ttl=ttl,
        )

    def get_index_price_data(self, index_name: str) -> IndexPriceData | None:
        """Get index price and valuation data.

        Args:
            index_name: Index name (e.g., "NIFTY 50", "NIFTY BANK")

        Returns:
            IndexPriceData with price, PE, PB, dividend yield, volume, etc.
        """
        data = self._get_index_tracker_api(
            "getIndexData",
            index=index_name,
            ttl=CacheTTL.SHORT,
        )

        if data and "data" in data and data["data"]:
            try:
                return IndexPriceData.model_validate(data["data"][0])
            except Exception:
                return None
        return None

    def get_index_returns(self, index_name: str) -> IndexReturns | None:
        """Get index returns across multiple time periods.

        Args:
            index_name: Index name

        Returns:
            IndexReturns with 1W, 1M, 3M, 6M, 1Y, 2Y, 3Y, 5Y returns
        """
        data = self._get_index_tracker_api(
            "getIndicesReturn",
            index=index_name,
            ttl=CacheTTL.DAILY,
        )

        if data and "data" in data and data["data"]:
            try:
                return IndexReturns.model_validate(data["data"][0])
            except Exception:
                return None
        return None

    def get_index_facts(self, index_name: str) -> IndexFacts | None:
        """Get index factsheet and methodology information.

        Args:
            index_name: Index name

        Returns:
            IndexFacts with description, methodology PDF, factsheet PDF links
        """
        data = self._get_index_tracker_api(
            "getIndexFacts",
            index=index_name,
            ttl=CacheTTL.WEEKLY,
        )

        if data and "data" in data and data["data"]:
            try:
                return IndexFacts.model_validate(data["data"][0])
            except Exception:
                return None
        return None

    def get_index_advance_decline_data(
        self, index_name: str
    ) -> IndexAdvanceDeclineData | None:
        """Get advance/decline data for an index.

        Args:
            index_name: Index name

        Returns:
            IndexAdvanceDeclineData with advances, declines, turnover breakdown
        """
        data = self._get_index_tracker_api(
            "getAdvanceDecline",
            index=index_name,
            ttl=CacheTTL.SHORT,
        )

        if data and "data" in data and data["data"]:
            try:
                return IndexAdvanceDeclineData.model_validate(data["data"][0])
            except Exception:
                return None
        return None

    def get_index_contributors(
        self, index_name: str, positive: bool = True, limit: int = 10
    ) -> list[IndexContributor]:
        """Get stocks contributing to index movement.

        Args:
            index_name: Index name
            positive: True for positive contributors, False for negative
            limit: Maximum number of contributors to return

        Returns:
            List of IndexContributor with point contributions
        """
        # flag="0" returns all contributors (both positive and negative)
        data = self._get_index_tracker_api(
            "getContributionData",
            index=index_name,
            flag="0",
            ttl=CacheTTL.SHORT,
        )

        contributors = []
        if data and "data" in data:
            for item in data["data"]:
                try:
                    contributor = IndexContributor.model_validate(item)
                    # Filter by positive/negative based on isPositive field
                    is_pos = contributor.is_positive == "Y"
                    if positive and is_pos:
                        contributors.append(contributor)
                    elif not positive and not is_pos:
                        contributors.append(contributor)
                    if len(contributors) >= limit:
                        break
                except Exception:
                    continue
        return contributors

    def get_index_top_contributors(
        self, index_name: str, limit: int = 5
    ) -> list[IndexContributor]:
        """Get top positive contributors to index movement.

        Args:
            index_name: Index name
            limit: Maximum number to return

        Returns:
            List of top positive contributors
        """
        return self.get_index_contributors(index_name, positive=True, limit=limit)

    def get_index_bottom_contributors(
        self, index_name: str, limit: int = 5
    ) -> list[IndexContributor]:
        """Get top negative contributors to index movement.

        Args:
            index_name: Index name
            limit: Maximum number to return

        Returns:
            List of top negative (drag) contributors
        """
        return self.get_index_contributors(index_name, positive=False, limit=limit)

    def get_index_heatmap(self, index_name: str) -> list[IndexHeatmapStock]:
        """Get heatmap data for all stocks in an index.

        Args:
            index_name: Index name

        Returns:
            List of IndexHeatmapStock with price and volume data
        """
        data = self._get_index_tracker_api(
            "getIndicesHeatMap",
            index=index_name,
            ttl=CacheTTL.SHORT,
        )

        stocks = []
        if data and "data" in data:
            for item in data["data"]:
                try:
                    stocks.append(IndexHeatmapStock.model_validate(item))
                except Exception:
                    continue
        return stocks

    def get_index_top_gainers_tracker(
        self, index_name: str, limit: int = 5
    ) -> list[IndexTopMover]:
        """Get top gainers in an index (from index tracker API).

        Args:
            index_name: Index name
            limit: Maximum number to return

        Returns:
            List of IndexTopMover for top gainers
        """
        data = self._get_index_tracker_api(
            "getTopFiveStock",
            index=index_name,
            flag="G",  # G for gainers
            ttl=CacheTTL.SHORT,
        )

        gainers = []
        if data and "data" in data and "topGainers" in data["data"]:
            for item in data["data"]["topGainers"][:limit]:
                try:
                    gainers.append(IndexTopMover.model_validate(item))
                except Exception:
                    continue
        return gainers

    def get_index_top_losers_tracker(
        self, index_name: str, limit: int = 5
    ) -> list[IndexTopMover]:
        """Get top losers in an index (from index tracker API).

        Args:
            index_name: Index name
            limit: Maximum number to return

        Returns:
            List of IndexTopMover for top losers
        """
        data = self._get_index_tracker_api(
            "getTopFiveStock",
            index=index_name,
            flag="L",  # L for losers
            ttl=CacheTTL.SHORT,
        )

        losers = []
        if data and "data" in data and "topLoosers" in data["data"]:
            for item in data["data"]["topLoosers"][:limit]:
                try:
                    losers.append(IndexTopMover.model_validate(item))
                except Exception:
                    continue
        return losers

    def get_index_announcements(
        self, index_name: str, limit: int = 10
    ) -> list[IndexAnnouncement]:
        """Get recent corporate announcements for index constituents.

        Args:
            index_name: Index name
            limit: Maximum number to return

        Returns:
            List of IndexAnnouncement
        """
        data = self._get_index_tracker_api(
            "getAnnouncementsIndices",
            index=index_name,
            flag="CAN",
            ttl=CacheTTL.LONG,
        )

        announcements = []
        if data and "data" in data:
            for item in data["data"][:limit]:
                try:
                    announcements.append(IndexAnnouncement.model_validate(item))
                except Exception:
                    continue
        return announcements

    def get_index_board_meetings(
        self, index_name: str, limit: int = 10
    ) -> list[IndexBoardMeeting]:
        """Get upcoming board meetings for index constituents.

        Args:
            index_name: Index name
            limit: Maximum number to return

        Returns:
            List of IndexBoardMeeting
        """
        data = self._get_index_tracker_api(
            "getBoardMeeting",
            index=index_name,
            flag="BM",
            ttl=CacheTTL.DAILY,
        )

        meetings = []
        if data and "data" in data:
            for item in data["data"][:limit]:
                try:
                    meetings.append(IndexBoardMeeting.model_validate(item))
                except Exception:
                    continue
        return meetings

    def get_index_intraday_chart(
        self, index_name: str, period: str = "1D"
    ) -> IndexChartData:
        """Get intraday chart data for an index.

        Args:
            index_name: Index name
            period: Chart period - "1D", "1W", "1M", "1Y"

        Returns:
            IndexChartData with chart points
        """
        data = self._get_index_tracker_api(
            "getIndexChart",
            index=index_name,
            flag=period,
            ttl=CacheTTL.SHORT if period == "1D" else CacheTTL.DAILY,
        )

        chart_data = IndexChartData(identifier="", name=index_name, data_points=[])

        if data and "data" in data and data["data"]:
            raw = data["data"][0] if isinstance(data["data"], list) else data["data"]

            chart_data.identifier = raw.get("identifier", "")
            chart_data.name = raw.get("indexCloseOnlineRecords", {}).get("EODIndexName", index_name)

            # Parse graphData points
            graph_data = raw.get("grapthData", [])  # Note: NSE API has typo "grapth"
            for point in graph_data:
                try:
                    chart_data.data_points.append(
                        IndexChartPoint(
                            timestamp=int(point[0]),
                            value=float(point[1]),
                            market_phase=point[2] if len(point) > 2 else "",
                        )
                    )
                except Exception:
                    continue

        return chart_data

    def get_index_summary(self, index_name: str) -> IndexSummaryData:
        """Get comprehensive index summary with all available data.

        This method aggregates data from multiple index tracker APIs into
        a single IndexSummaryData object.

        Args:
            index_name: Index name (e.g., "NIFTY 50", "NIFTY BANK")

        Returns:
            IndexSummaryData with price, returns, breadth, contributors,
            gainers/losers, heatmap, announcements, and board meetings
        """
        import datetime

        # Fetch all data in parallel (if supported) or sequentially
        price_data = self.get_index_price_data(index_name)
        returns = self.get_index_returns(index_name)
        facts = self.get_index_facts(index_name)
        advance_decline = self.get_index_advance_decline_data(index_name)
        top_contributors = self.get_index_top_contributors(index_name, limit=5)
        bottom_contributors = self.get_index_bottom_contributors(index_name, limit=5)
        top_gainers = self.get_index_top_gainers_tracker(index_name, limit=5)
        top_losers = self.get_index_top_losers_tracker(index_name, limit=5)
        heatmap = self.get_index_heatmap(index_name)
        announcements = self.get_index_announcements(index_name, limit=5)
        board_meetings = self.get_index_board_meetings(index_name, limit=5)

        timestamp = ""
        if price_data and price_data.time_val:
            timestamp = price_data.time_val
        else:
            timestamp = datetime.datetime.now().strftime("%d-%b-%Y %H:%M")

        return IndexSummaryData(
            index_name=index_name,
            timestamp=timestamp,
            price_data=price_data,
            returns=returns,
            facts=facts,
            advance_decline=advance_decline,
            top_contributors=top_contributors,
            bottom_contributors=bottom_contributors,
            top_gainers=top_gainers,
            top_losers=top_losers,
            heatmap=heatmap,
            announcements=announcements,
            board_meetings=board_meetings,
        )

    def get_index_summary_markdown(self, index_name: str) -> str:
        """Get index summary formatted as markdown.

        Args:
            index_name: Index name

        Returns:
            Markdown formatted summary string
        """
        summary = self.get_index_summary(index_name)
        return summary.format_summary()

    def get_nifty50_summary(self) -> IndexSummaryData:
        """Get comprehensive summary for NIFTY 50 index.

        Returns:
            IndexSummaryData for NIFTY 50
        """
        return self.get_index_summary("NIFTY 50")

    def get_banknifty_summary(self) -> IndexSummaryData:
        """Get comprehensive summary for Bank NIFTY index.

        Returns:
            IndexSummaryData for NIFTY BANK
        """
        return self.get_index_summary("NIFTY BANK")

    def get_niftyit_summary(self) -> IndexSummaryData:
        """Get comprehensive summary for NIFTY IT index.

        Returns:
            IndexSummaryData for NIFTY IT
        """
        return self.get_index_summary("NIFTY IT")

    # ==================== GIFT NIFTY (MoneyControl API) ====================

    GIFT_NIFTY_SYMBOL = "in;gsx"
    MONEYCONTROL_BASE_URL = "https://priceapi.moneycontrol.com"

    def _fetch_gift_nifty_url(
        self, url: str, cache_key: str | None = None, ttl: int = CacheTTL.VERY_SHORT
    ) -> dict[str, Any]:
        """Fetch GIFT NIFTY data from URL with caching.

        Args:
            url: URL to fetch
            cache_key: Optional cache key for file caching
            ttl: Cache TTL in seconds

        Returns:
            JSON response as dict
        """
        import httpx

        # Check cache if enabled
        if cache_key and self._http._cache_config.enabled:
            cached, found = self._http._cache.get(cache_key, None)
            if found:
                return cached

        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
            "Accept": "application/json",
        }

        with httpx.Client(headers=headers, timeout=30.0) as client:
            response = client.get(url)
            response.raise_for_status()
            result = response.json()

        # Cache the result
        if cache_key and self._http._cache_config.enabled:
            self._http._cache.set(cache_key, None, result, ttl)

        return result

    def get_gift_nifty_history(
        self,
        resolution: str = "1D",
        countback: int = 300,
        from_date: date | None = None,
        to_date: date | None = None,
        as_df: bool = False,
    ) -> dict[str, Any] | Any:
        """Get GIFT NIFTY historical OHLCV data from MoneyControl.

        GIFT NIFTY trades on SGX (Singapore Exchange) and provides
        price discovery for Indian markets before they open.

        Args:
            resolution: Chart resolution - "1", "5", "15", "30", "60", "240", "1D", "1W", "1M"
            countback: Number of candles to fetch (default: 300)
            from_date: Start date (optional, overrides countback if provided with to_date)
            to_date: End date (optional)
            as_df: If True, return pandas DataFrame instead of dict

        Returns:
            Dict with keys: t (timestamps), o (open), h (high), l (low), c (close), v (volume)
            Or pandas DataFrame if as_df=True with columns: datetime, open, high, low, close, volume

        Example:
            >>> # Get as dict
            >>> data = client.get_gift_nifty_history(resolution="1D", countback=30)
            >>> # Get as DataFrame
            >>> df = client.get_gift_nifty_history(resolution="1D", countback=30, as_df=True)
            >>> print(df.tail())
        """
        import time
        import urllib.parse

        # Calculate time range
        if from_date and to_date:
            from_time = int(datetime.datetime.combine(from_date, datetime.time.min).timestamp())
            to_time = int(datetime.datetime.combine(to_date, datetime.time.max).timestamp())
        else:
            now = int(time.time())
            from_time = now - (365 * 24 * 60 * 60)  # 1 year ago
            to_time = now + (24 * 60 * 60)  # Tomorrow

        symbol_encoded = urllib.parse.quote(self.GIFT_NIFTY_SYMBOL, safe="")
        url = (
            f"{self.MONEYCONTROL_BASE_URL}/globaltechCharts/globalMarket/index/history"
            f"?symbol={symbol_encoded}"
            f"&resolution={resolution}"
            f"&from={from_time}"
            f"&to={to_time}"
            f"&countback={countback}"
            f"&currencyCode=USD"
        )

        # Cache key based on params - daily data can be cached longer
        cache_key = f"gift_nifty_history_{resolution}_{from_time}_{to_time}_{countback}"
        ttl = CacheTTL.DAILY if resolution in ("1D", "1W", "1M") else CacheTTL.VERY_SHORT

        data = self._fetch_gift_nifty_url(url, cache_key=cache_key, ttl=ttl)

        if not as_df:
            return data

        # Convert to DataFrame
        try:
            import pandas as pd

            if data.get("s") != "ok":
                return pd.DataFrame()

            df = pd.DataFrame({
                "datetime": pd.to_datetime(data.get("t", []), unit="s"),
                "open": data.get("o", []),
                "high": data.get("h", []),
                "low": data.get("l", []),
                "close": data.get("c", []),
                "volume": data.get("v", []),
            })
            df.set_index("datetime", inplace=True)
            return df
        except ImportError:
            raise ImportError("pandas is required for as_df=True. Install with: pip install pandas")

    def get_gift_nifty_intraday(
        self,
        duration: str = "1D",
        as_df: bool = False,
    ) -> dict[str, Any] | Any:
        """Get GIFT NIFTY intraday tick data from MoneyControl.

        Args:
            duration: Duration - "1D" (1 day), "1W" (1 week), "1M" (1 month)
            as_df: If True, return pandas DataFrame instead of dict

        Returns:
            Dict with 'data' key containing list of {time, value} dicts.
            Or pandas DataFrame if as_df=True with columns: datetime, price

        Example:
            >>> data = client.get_gift_nifty_intraday(duration="1D")
            >>> df = client.get_gift_nifty_intraday(duration="1D", as_df=True)
        """
        url = (
            f"{self.MONEYCONTROL_BASE_URL}/globaltechCharts/globalMarket/index/intra"
            f"?symbol={self.GIFT_NIFTY_SYMBOL}"
            f"&duration={duration}"
            f"&firstCall=true"
        )

        cache_key = f"gift_nifty_intra_{duration}"
        data = self._fetch_gift_nifty_url(url, cache_key=cache_key, ttl=CacheTTL.VERY_SHORT)

        if not as_df:
            return data

        # Convert to DataFrame
        try:
            import pandas as pd

            if data.get("s") != "ok" or not data.get("data"):
                return pd.DataFrame()

            points = data["data"]
            df = pd.DataFrame({
                "datetime": pd.to_datetime([p["time"] for p in points], unit="s"),
                "price": [p["value"] for p in points],
            })
            df.set_index("datetime", inplace=True)
            return df
        except ImportError:
            raise ImportError("pandas is required for as_df=True. Install with: pip install pandas")

    def get_gift_nifty_current(self) -> dict[str, Any]:
        """Get current GIFT NIFTY price and basic stats.

        Returns:
            Dict with current price, day's OHLC, and change info.

        Example:
            >>> info = client.get_gift_nifty_current()
            >>> print(f"GIFT NIFTY: {info['current']} ({info['change_percent']:+.2f}%)")
        """
        # Get latest intraday data for current price
        intra = self.get_gift_nifty_intraday(duration="1D")

        # Get today's OHLCV from history
        history = self.get_gift_nifty_history(resolution="1D", countback=2)

        result = {
            "symbol": "GIFT NIFTY",
            "current": None,
            "open": None,
            "high": None,
            "low": None,
            "prev_close": None,
            "change": None,
            "change_percent": None,
            "intraday_high": None,
            "intraday_low": None,
        }

        # Current price from intraday
        if intra.get("s") == "ok" and intra.get("data"):
            points = intra["data"]
            if points:
                result["current"] = points[-1]["value"]
                result["intraday_high"] = max(p["value"] for p in points)
                result["intraday_low"] = min(p["value"] for p in points)

        # OHLC from history
        if history.get("s") == "ok":
            t = history.get("t", [])
            o = history.get("o", [])
            h = history.get("h", [])
            l = history.get("l", [])
            c = history.get("c", [])

            if len(t) >= 1:
                # Latest candle (today or most recent)
                result["open"] = o[-1] if o else None
                result["high"] = h[-1] if h else None
                result["low"] = l[-1] if l else None

            if len(c) >= 2:
                # Previous close for change calculation
                result["prev_close"] = c[-2]

        # Calculate change
        if result["current"] and result["prev_close"]:
            result["change"] = result["current"] - result["prev_close"]
            result["change_percent"] = (result["change"] / result["prev_close"]) * 100

        return result

    def save_gift_nifty_history_csv(
        self,
        filepath: str | Path,
        resolution: str = "1D",
        countback: int = 300,
        from_date: date | None = None,
        to_date: date | None = None,
    ) -> Path:
        """Save GIFT NIFTY historical data to CSV file.

        Args:
            filepath: Path to save CSV file
            resolution: Chart resolution
            countback: Number of candles
            from_date: Start date (optional)
            to_date: End date (optional)

        Returns:
            Path to saved file
        """
        df = self.get_gift_nifty_history(
            resolution=resolution,
            countback=countback,
            from_date=from_date,
            to_date=to_date,
            as_df=True,
        )

        filepath = Path(filepath)
        filepath.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(filepath)
        return filepath
