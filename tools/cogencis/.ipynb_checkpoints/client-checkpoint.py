"""Cogencis API Client."""

import logging
from typing import Any

from .core.http_client import CogencisHTTPClient
from .core.exceptions import CogencisValidationError
from .models.symbol import (
    SymbolLookupResponse,
    SymbolData,
    SearchOn,
)
from .models.auditor import AuditorResponse, AuditorData
from .models.news import NewsResponse, NewsStory
from .models.shareholder import (
    KeyShareholderResponse,
    KeyShareholder,
)
from .models.block_deal import (
    BlockDealResponse,
    BlockDeal,
    BlockDealType,
)
from .models.insider_trading import (
    InsiderTradingResponse,
    InsiderTrade,
)
from .models.sast import (
    SASTResponse,
    SASTTransaction,
)
from .models.capital_history import (
    CapitalHistoryResponse,
    CapitalHistoryEntry,
)
from .models.announcement import (
    AnnouncementResponse,
    Announcement,
)
from .models.corporate_action import (
    CorporateActionResponse,
    CorporateAction,
)
from .models.tribunal import (
    TribunalResponse,
    TribunalCase,
)

logger = logging.getLogger(__name__)


class CogencisClient:
    """
    Client for interacting with Cogencis API.
    
    Example:
        >>> client = CogencisClient(bearer_token="your_token")
        >>> symbols = client.symbol_lookup("reliance")
        >>> for symbol in symbols:
        ...     print(f"{symbol.company_name}: {symbol.last_price}")
    """

    def __init__(
        self,
        bearer_token: str,
        base_url: str | None = None,
        timeout: float = 30.0,
    ) -> None:
        """
        Initialize the Cogencis client.

        Args:
            bearer_token: JWT bearer token for authentication
            base_url: Optional custom base URL for the API
            timeout: Request timeout in seconds
        """
        self._http = CogencisHTTPClient(
            bearer_token=bearer_token,
            base_url=base_url,
            timeout=timeout,
        )

    # ==========================================================================
    # Symbol Lookup API
    # ==========================================================================

    def symbol_lookup(
        self,
        search_term: str,
        search_on: SearchOn | str = SearchOn.ALL,
        index_name: str = "idxLookup",
        page_no: int = 1,
        page_size: int = 10,
    ) -> list[SymbolData]:
        """
        Search for symbols by name, ISIN, or symbol.

        Args:
            search_term: The term to search for (e.g., "reliance")
            search_on: Fields to search on (name, isin, symbol, or combinations)
            index_name: Index name for lookup (default: "idxLookup")
            page_no: Page number for pagination (1-based)
            page_size: Number of results per page

        Returns:
            List of matching symbols

        Example:
            >>> symbols = client.symbol_lookup("reliance")
            >>> for s in symbols:
            ...     print(f"{s.ticker}: {s.company_name}")
        """
        if not search_term:
            raise CogencisValidationError("search_term cannot be empty")

        # Convert enum to string if needed
        search_on_str = search_on.value if isinstance(search_on, SearchOn) else search_on

        params = {
            "searchTerm": search_term,
            "searchOn": search_on_str,
            "indexName": index_name,
            "pageNo": page_no,
            "pageSize": page_size,
        }

        data = self._http.get("/marketdata/symbollookup", params=params)
        response = SymbolLookupResponse.model_validate(data)
        return response.symbols

    def symbol_lookup_response(
        self,
        search_term: str,
        search_on: SearchOn | str = SearchOn.ALL,
        index_name: str = "idxLookup",
        page_no: int = 1,
        page_size: int = 10,
    ) -> SymbolLookupResponse:
        """
        Search for symbols and return the full response object.

        Similar to symbol_lookup but returns the complete response
        including pagination info.

        Args:
            search_term: The term to search for
            search_on: Fields to search on
            index_name: Index name for lookup
            page_no: Page number for pagination
            page_size: Number of results per page

        Returns:
            Complete SymbolLookupResponse object
        """
        if not search_term:
            raise CogencisValidationError("search_term cannot be empty")

        search_on_str = search_on.value if isinstance(search_on, SearchOn) else search_on

        params = {
            "searchTerm": search_term,
            "searchOn": search_on_str,
            "indexName": index_name,
            "pageNo": page_no,
            "pageSize": page_size,
        }

        data = self._http.get("/marketdata/symbollookup", params=params)
        return SymbolLookupResponse.model_validate(data)

    # ==========================================================================
    # Auditors API
    # ==========================================================================

    def get_auditors(
        self,
        path: str,
        detailed: bool = True,
    ) -> list[AuditorData]:
        """
        Get auditor information for a company.

        Args:
            path: The company path from symbol lookup 
                  (e.g., "ine002a01018/relindus/ns/reliance/reliance-industries_")
            detailed: Whether to return detailed information

        Returns:
            List of auditor information

        Example:
            >>> auditors = client.get_auditors(
            ...     "ine002a01018/relindus/ns/reliance/reliance-industries_"
            ... )
            >>> for a in auditors:
            ...     print(f"{a.auditor_personnel}: {a.appointment_date}")
        """
        if not path:
            raise CogencisValidationError("path cannot be empty")

        params = {
            "path": path,
            "detailed": str(detailed).lower(),
        }

        data = self._http.get("/auditors", params=params)
        response = AuditorResponse.model_validate(data)
        return response.auditors

    def get_auditors_response(
        self,
        path: str,
        detailed: bool = True,
    ) -> AuditorResponse:
        """
        Get auditor information and return the full response object.

        Args:
            path: The company path from symbol lookup
            detailed: Whether to return detailed information

        Returns:
            Complete AuditorResponse object
        """
        if not path:
            raise CogencisValidationError("path cannot be empty")

        params = {
            "path": path,
            "detailed": str(detailed).lower(),
        }

        data = self._http.get("/auditors", params=params)
        return AuditorResponse.model_validate(data)

    # ==========================================================================
    # News API
    # ==========================================================================

    def get_news(
        self,
        isins: str | list[str],
        page_no: int = 1,
        page_size: int = 20,
        web_news: bool = True,
        for_website: bool = True,
    ) -> list[NewsStory]:
        """
        Get news stories for specified ISINs.

        Args:
            isins: Single ISIN or list of ISINs (e.g., "ine002a01018" or ["ine002a01018"])
            page_no: Page number for pagination (1-based)
            page_size: Number of results per page
            web_news: Filter for web news
            for_website: Format for website display

        Returns:
            List of news stories

        Example:
            >>> news = client.get_news("ine002a01018", page_size=10)
            >>> for story in news:
            ...     print(f"{story.headline}")
            ...     print(f"  Source: {story.source_name}")
        """
        if not isins:
            raise CogencisValidationError("isins cannot be empty")

        # Convert list to comma-separated string
        if isinstance(isins, list):
            isins_str = ",".join(isins)
        else:
            isins_str = isins

        params = {
            "isins": isins_str.lower(),  # API expects lowercase
            "pageNo": page_no,
            "pageSize": page_size,
            "sWebNews": str(web_news).lower(),
            "forWebSite": str(for_website).lower(),
        }

        data = self._http.get("/web/news/stories", params=params)
        response = NewsResponse.model_validate(data)
        return response.stories

    def get_news_response(
        self,
        isins: str | list[str],
        page_no: int = 1,
        page_size: int = 20,
        web_news: bool = True,
        for_website: bool = True,
    ) -> NewsResponse:
        """
        Get news stories and return the full response object.

        Similar to get_news but returns the complete response
        including pagination info.

        Args:
            isins: Single ISIN or list of ISINs
            page_no: Page number for pagination
            page_size: Number of results per page
            web_news: Filter for web news
            for_website: Format for website display

        Returns:
            Complete NewsResponse object
        """
        if not isins:
            raise CogencisValidationError("isins cannot be empty")

        if isinstance(isins, list):
            isins_str = ",".join(isins)
        else:
            isins_str = isins

        params = {
            "isins": isins_str.lower(),
            "pageNo": page_no,
            "pageSize": page_size,
            "sWebNews": str(web_news).lower(),
            "forWebSite": str(for_website).lower(),
        }

        data = self._http.get("/web/news/stories", params=params)
        return NewsResponse.model_validate(data)

    # ==========================================================================
    # Key Shareholders API
    # ==========================================================================

    def get_key_shareholders(
        self,
        path: str,
        page_no: int = 1,
        page_size: int = 20,
        detailed: bool = True,
    ) -> list[KeyShareholder]:
        """
        Get key shareholder information for a company.

        Args:
            path: The company path from symbol lookup
                  (e.g., "ine002a01018/relindus/ns/reliance/reliance-industries_")
            page_no: Page number for pagination (1-based)
            page_size: Number of results per page
            detailed: Whether to return detailed information

        Returns:
            List of key shareholders with their historical holdings

        Example:
            >>> shareholders = client.get_key_shareholders(
            ...     "ine002a01018/relindus/ns/reliance/reliance-industries_"
            ... )
            >>> for sh in shareholders:
            ...     if not sh.is_group:
            ...         holding = sh.get_latest_holding()
            ...         if holding:
            ...             print(f"{sh.description}: {holding.percentage}%")
        """
        if not path:
            raise CogencisValidationError("path cannot be empty")

        params = {
            "path": path,
            "pageNo": page_no,
            "pageSize": page_size,
            "detailed": str(detailed).lower(),
        }

        data = self._http.get("/keyshareholders", params=params)
        response = KeyShareholderResponse.model_validate(data)
        return response.shareholders

    def get_key_shareholders_response(
        self,
        path: str,
        page_no: int = 1,
        page_size: int = 20,
        detailed: bool = True,
    ) -> KeyShareholderResponse:
        """
        Get key shareholders and return the full response object.

        Args:
            path: The company path from symbol lookup
            page_no: Page number for pagination
            page_size: Number of results per page
            detailed: Whether to return detailed information

        Returns:
            Complete KeyShareholderResponse object
        """
        if not path:
            raise CogencisValidationError("path cannot be empty")

        params = {
            "path": path,
            "pageNo": page_no,
            "pageSize": page_size,
            "detailed": str(detailed).lower(),
        }

        data = self._http.get("/keyshareholders", params=params)
        return KeyShareholderResponse.model_validate(data)

    # ==========================================================================
    # Block Deals API
    # ==========================================================================

    def get_block_deals(
        self,
        path: str,
        deal_type: BlockDealType | int = BlockDealType.BLOCK_DEAL,
        page_no: int = 1,
        page_size: int = 20,
        detailed: bool = True,
    ) -> list[BlockDeal]:
        """
        Get block deal information for a company.

        Args:
            path: The company path from symbol lookup
                  (e.g., "ine002a01018/relindus/ns/reliance/reliance-industries_")
            deal_type: Type of deals (1=Block Deals, 2=Bulk Deals)
            page_no: Page number for pagination (1-based)
            page_size: Number of results per page
            detailed: Whether to return detailed information

        Returns:
            List of block/bulk deals

        Example:
            >>> # Get block deals
            >>> deals = client.get_block_deals(
            ...     "ine002a01018/relindus/ns/reliance/reliance-industries_"
            ... )
            >>> for deal in deals:
            ...     print(f"{deal.client_name}: {deal.transaction_type}")
            ...     print(f"  Qty: {deal.quantity:,} @ ₹{deal.weighted_avg_price}")
        """
        if not path:
            raise CogencisValidationError("path cannot be empty")

        type_val = deal_type.value if isinstance(deal_type, BlockDealType) else deal_type

        params = {
            "path": path,
            "type": type_val,
            "pageNo": page_no,
            "pageSize": page_size,
            "detailed": str(detailed).lower(),
            "jsonArray": "true",
        }

        data = self._http.get("/blockdeals", params=params)
        response = BlockDealResponse.model_validate(data)
        return response.deals

    def get_bulk_deals(
        self,
        path: str,
        page_no: int = 1,
        page_size: int = 20,
        detailed: bool = True,
    ) -> list[BlockDeal]:
        """
        Get bulk deal information for a company (convenience method).

        Args:
            path: The company path from symbol lookup
            page_no: Page number for pagination (1-based)
            page_size: Number of results per page
            detailed: Whether to return detailed information

        Returns:
            List of bulk deals
        """
        return self.get_block_deals(
            path=path,
            deal_type=BlockDealType.BULK_DEAL,
            page_no=page_no,
            page_size=page_size,
            detailed=detailed,
        )

    def get_block_deals_response(
        self,
        path: str,
        deal_type: BlockDealType | int = BlockDealType.BLOCK_DEAL,
        page_no: int = 1,
        page_size: int = 20,
        detailed: bool = True,
    ) -> BlockDealResponse:
        """
        Get block deals and return the full response object.

        Args:
            path: The company path from symbol lookup
            deal_type: Type of deals (1=Block Deals, 2=Bulk Deals)
            page_no: Page number for pagination
            page_size: Number of results per page
            detailed: Whether to return detailed information

        Returns:
            Complete BlockDealResponse object
        """
        if not path:
            raise CogencisValidationError("path cannot be empty")

        type_val = deal_type.value if isinstance(deal_type, BlockDealType) else deal_type

        params = {
            "path": path,
            "type": type_val,
            "pageNo": page_no,
            "pageSize": page_size,
            "detailed": str(detailed).lower(),
            "jsonArray": "true",
        }

        data = self._http.get("/blockdeals", params=params)
        return BlockDealResponse.model_validate(data)

    # ==========================================================================
    # Insider Trading API
    # ==========================================================================

    def get_insider_trades(
        self,
        path: str,
        page_no: int = 1,
        page_size: int = 20,
        detailed: bool = True,
    ) -> list[InsiderTrade]:
        """
        Get insider trading information for a company.

        Args:
            path: The company path from symbol lookup
                  (e.g., "ine002a01018/relindus/ns/reliance/reliance-industries_")
            page_no: Page number for pagination (1-based)
            page_size: Number of results per page
            detailed: Whether to return detailed information

        Returns:
            List of insider trades

        Example:
            >>> trades = client.get_insider_trades(
            ...     "ine002a01018/relindus/ns/reliance/reliance-industries_"
            ... )
            >>> for trade in trades:
            ...     print(f"{trade.acquirer_name}: {trade.transaction_type}")
            ...     print(f"  Qty: {trade.quantity:,} ({trade.category})")
        """
        if not path:
            raise CogencisValidationError("path cannot be empty")

        params = {
            "path": path,
            "pageNo": page_no,
            "pageSize": page_size,
            "detailed": str(detailed).lower(),
            "jsonArray": "true",
        }

        data = self._http.get("/insidertrading", params=params)
        response = InsiderTradingResponse.model_validate(data)
        return response.trades

    def get_insider_trades_response(
        self,
        path: str,
        page_no: int = 1,
        page_size: int = 20,
        detailed: bool = True,
    ) -> InsiderTradingResponse:
        """
        Get insider trades and return the full response object.

        Args:
            path: The company path from symbol lookup
            page_no: Page number for pagination
            page_size: Number of results per page
            detailed: Whether to return detailed information

        Returns:
            Complete InsiderTradingResponse object
        """
        if not path:
            raise CogencisValidationError("path cannot be empty")

        params = {
            "path": path,
            "pageNo": page_no,
            "pageSize": page_size,
            "detailed": str(detailed).lower(),
            "jsonArray": "true",
        }

        data = self._http.get("/insidertrading", params=params)
        return InsiderTradingResponse.model_validate(data)

    # ==========================================================================
    # SAST (Substantial Acquisition) API
    # ==========================================================================

    def get_sast(
        self,
        path: str,
        page_no: int = 1,
        page_size: int = 20,
        detailed: bool = True,
    ) -> list[SASTTransaction]:
        """
        Get SAST (Substantial Acquisition of Shares and Takeovers) information.

        Args:
            path: The company path from symbol lookup
                  (e.g., "ine002a01018/relindus/ns/reliance/reliance-industries_")
            page_no: Page number for pagination (1-based)
            page_size: Number of results per page
            detailed: Whether to return detailed information

        Returns:
            List of SAST transactions

        Example:
            >>> transactions = client.get_sast(
            ...     "ine002a01018/relindus/ns/reliance/reliance-industries_"
            ... )
            >>> for txn in transactions:
            ...     print(f"{txn.acquirer_name}: {txn.transaction_type}")
            ...     print(f"  Qty: {txn.quantity:,} shares")
        """
        if not path:
            raise CogencisValidationError("path cannot be empty")

        params = {
            "path": path,
            "pageNo": page_no,
            "pageSize": page_size,
            "detailed": str(detailed).lower(),
            "jsonArray": "true",
        }

        data = self._http.get("/sast", params=params)
        response = SASTResponse.model_validate(data)
        return response.transactions

    def get_sast_response(
        self,
        path: str,
        page_no: int = 1,
        page_size: int = 20,
        detailed: bool = True,
    ) -> SASTResponse:
        """
        Get SAST transactions and return the full response object.

        Args:
            path: The company path from symbol lookup
            page_no: Page number for pagination
            page_size: Number of results per page
            detailed: Whether to return detailed information

        Returns:
            Complete SASTResponse object
        """
        if not path:
            raise CogencisValidationError("path cannot be empty")

        params = {
            "path": path,
            "pageNo": page_no,
            "pageSize": page_size,
            "detailed": str(detailed).lower(),
            "jsonArray": "true",
        }

        data = self._http.get("/sast", params=params)
        return SASTResponse.model_validate(data)

    # ==========================================================================
    # Capital History API
    # ==========================================================================

    def get_capital_history(
        self,
        path: str,
        page_no: int = 1,
        page_size: int = 20,
        detailed: bool = True,
    ) -> list[CapitalHistoryEntry]:
        """
        Get capital history (stock splits, bonus issues, rights, etc.).

        Args:
            path: The company path from symbol lookup
                  (e.g., "ine002a01018/relindus/ns/reliance/reliance-industries_")
            page_no: Page number for pagination (1-based)
            page_size: Number of results per page
            detailed: Whether to return detailed information

        Returns:
            List of capital history entries

        Example:
            >>> history = client.get_capital_history(
            ...     "ine002a01018/relindus/ns/reliance/reliance-industries_"
            ... )
            >>> for entry in history:
            ...     print(f"{entry.date}: {entry.event_type}")
            ...     if entry.change_in_shares:
            ...         print(f"  Change: {entry.change_in_shares:,.0f} shares")
        """
        if not path:
            raise CogencisValidationError("path cannot be empty")

        params = {
            "path": path,
            "pageNo": page_no,
            "pageSize": page_size,
            "detailed": str(detailed).lower(),
            "jsonArray": "true",
        }

        data = self._http.get("/capitalhistory", params=params)
        response = CapitalHistoryResponse.model_validate(data)
        return response.entries

    def get_capital_history_response(
        self,
        path: str,
        page_no: int = 1,
        page_size: int = 20,
        detailed: bool = True,
    ) -> CapitalHistoryResponse:
        """
        Get capital history and return the full response object.

        Args:
            path: The company path from symbol lookup
            page_no: Page number for pagination
            page_size: Number of results per page
            detailed: Whether to return detailed information

        Returns:
            Complete CapitalHistoryResponse object
        """
        if not path:
            raise CogencisValidationError("path cannot be empty")

        params = {
            "path": path,
            "pageNo": page_no,
            "pageSize": page_size,
            "detailed": str(detailed).lower(),
            "jsonArray": "true",
        }

        data = self._http.get("/capitalhistory", params=params)
        return CapitalHistoryResponse.model_validate(data)

    # ==========================================================================
    # Announcements API
    # ==========================================================================

    def get_announcements(
        self,
        path: str,
        page_no: int = 1,
        page_size: int = 20,
        detailed: bool = True,
    ) -> list[Announcement]:
        """
        Get company announcements (board meetings, results, etc.).

        Args:
            path: The company path from symbol lookup
                  (e.g., "ine002a01018/relindus/ns/reliance/reliance-industries_")
            page_no: Page number for pagination (1-based)
            page_size: Number of results per page
            detailed: Whether to return detailed information

        Returns:
            List of announcements

        Example:
            >>> announcements = client.get_announcements(
            ...     "ine002a01018/relindus/ns/reliance/reliance-industries_"
            ... )
            >>> for ann in announcements:
            ...     print(f"{ann.datetime_parsed}: {ann.details}")
            ...     if ann.has_pdf:
            ...         print(f"  PDF: {ann.pdf_link}")
        """
        if not path:
            raise CogencisValidationError("path cannot be empty")

        params = {
            "path": path,
            "pageNo": page_no,
            "pageSize": page_size,
            "detailed": str(detailed).lower(),
            "jsonArray": "true",
        }

        data = self._http.get("/announcements", params=params)
        response = AnnouncementResponse.model_validate(data)
        return response.announcements

    def get_announcements_response(
        self,
        path: str,
        page_no: int = 1,
        page_size: int = 20,
        detailed: bool = True,
    ) -> AnnouncementResponse:
        """
        Get announcements and return the full response object.

        Args:
            path: The company path from symbol lookup
            page_no: Page number for pagination
            page_size: Number of results per page
            detailed: Whether to return detailed information

        Returns:
            Complete AnnouncementResponse object
        """
        if not path:
            raise CogencisValidationError("path cannot be empty")

        params = {
            "path": path,
            "pageNo": page_no,
            "pageSize": page_size,
            "detailed": str(detailed).lower(),
            "jsonArray": "true",
        }

        data = self._http.get("/announcements", params=params)
        return AnnouncementResponse.model_validate(data)

    # ==========================================================================
    # Corporate Actions API
    # ==========================================================================

    def get_corporate_actions(
        self,
        path: str,
        page_no: int = 1,
        page_size: int = 20,
        detailed: bool = True,
    ) -> list[CorporateAction]:
        """
        Get corporate actions (dividends, bonus, rights, splits, etc.).

        Args:
            path: The company path from symbol lookup
                  (e.g., "ine002a01018/relindus/ns/reliance/reliance-industries_")
            page_no: Page number for pagination (1-based)
            page_size: Number of results per page
            detailed: Whether to return detailed information

        Returns:
            List of corporate actions

        Example:
            >>> actions = client.get_corporate_actions(
            ...     "ine002a01018/relindus/ns/reliance/reliance-industries_"
            ... )
            >>> for action in actions:
            ...     print(f"{action.ex_date_parsed}: {action.purpose}")
            ...     if action.is_dividend:
            ...         print(f"  Dividend: ₹{action.dividend_amount}")
        """
        if not path:
            raise CogencisValidationError("path cannot be empty")

        params = {
            "path": path,
            "pageNo": page_no,
            "pageSize": page_size,
            "detailed": str(detailed).lower(),
            "jsonArray": "true",
        }

        data = self._http.get("/corporateaction", params=params)
        response = CorporateActionResponse.model_validate(data)
        return response.actions

    def get_corporate_actions_response(
        self,
        path: str,
        page_no: int = 1,
        page_size: int = 20,
        detailed: bool = True,
    ) -> CorporateActionResponse:
        """
        Get corporate actions and return the full response object.

        Args:
            path: The company path from symbol lookup
            page_no: Page number for pagination
            page_size: Number of results per page
            detailed: Whether to return detailed information

        Returns:
            Complete CorporateActionResponse object
        """
        if not path:
            raise CogencisValidationError("path cannot be empty")

        params = {
            "path": path,
            "pageNo": page_no,
            "pageSize": page_size,
            "detailed": str(detailed).lower(),
            "jsonArray": "true",
        }

        data = self._http.get("/corporateaction", params=params)
        return CorporateActionResponse.model_validate(data)

    # ==========================================================================
    # Tribunals API
    # ==========================================================================

    def get_tribunal_cases(
        self,
        isin: str,
        page_no: int = 1,
        page_size: int = 20,
        detailed: bool = True,
    ) -> list[TribunalCase]:
        """
        Get tribunal cases (NCLT, NCLAT, SAT, NGT, etc.).

        Note: This endpoint uses ISIN instead of path.

        Args:
            isin: The ISIN of the company (e.g., "ine002a01018")
            page_no: Page number for pagination (1-based)
            page_size: Number of results per page
            detailed: Whether to return detailed information

        Returns:
            List of tribunal cases

        Example:
            >>> cases = client.get_tribunal_cases("ine002a01018")
            >>> for case in cases:
            ...     print(f"{case.date}: {case.tribunal_name}")
            ...     print(f"  {case.case_title}")
            ...     print(f"  Order: {case.order_type}")
        """
        if not isin:
            raise CogencisValidationError("isin cannot be empty")

        params = {
            "isin": isin.lower(),
            "pageNo": page_no,
            "pageSize": page_size,
            "detailed": str(detailed).lower(),
            "jsonArray": "true",
        }

        data = self._http.get("/tribunals", params=params)
        response = TribunalResponse.model_validate(data)
        return response.cases

    def get_tribunal_cases_response(
        self,
        isin: str,
        page_no: int = 1,
        page_size: int = 20,
        detailed: bool = True,
    ) -> TribunalResponse:
        """
        Get tribunal cases and return the full response object.

        Args:
            isin: The ISIN of the company
            page_no: Page number for pagination
            page_size: Number of results per page
            detailed: Whether to return detailed information

        Returns:
            Complete TribunalResponse object
        """
        if not isin:
            raise CogencisValidationError("isin cannot be empty")

        params = {
            "isin": isin.lower(),
            "pageNo": page_no,
            "pageSize": page_size,
            "detailed": str(detailed).lower(),
            "jsonArray": "true",
        }

        data = self._http.get("/tribunals", params=params)
        return TribunalResponse.model_validate(data)

    # ==========================================================================
    # Utility Methods
    # ==========================================================================

    def get_news_for_symbol(
        self,
        search_term: str,
        page_size: int = 20,
    ) -> list[NewsStory]:
        """
        Convenience method to search for a symbol and get its news.

        Args:
            search_term: Symbol or company name to search for
            page_size: Number of news stories to return

        Returns:
            List of news stories for the first matching symbol

        Example:
            >>> news = client.get_news_for_symbol("reliance industries")
            >>> print(f"Found {len(news)} stories")
        """
        symbols = self.symbol_lookup(search_term, page_size=1)
        if not symbols:
            return []

        symbol = symbols[0]
        return self.get_news(symbol.isin, page_size=page_size)

    def get_company_info(
        self,
        search_term: str,
    ) -> dict[str, Any]:
        """
        Convenience method to get comprehensive company information.

        Args:
            search_term: Symbol or company name to search for

        Returns:
            Dictionary containing symbol, shareholders, and recent trades

        Example:
            >>> info = client.get_company_info("reliance")
            >>> print(f"Company: {info['symbol'].company_name}")
            >>> print(f"Promoter holding: {info['promoter_holding']}%")
        """
        symbols = self.symbol_lookup(search_term, page_size=1)
        if not symbols:
            return {}

        symbol = symbols[0]
        path = symbol.path

        # Get shareholders
        shareholders = self.get_key_shareholders(path, page_size=20)
        promoters = [s for s in shareholders if s.is_promoter and not s.is_group]
        
        # Calculate total promoter holding
        promoter_holding = 0.0
        for p in promoters:
            holding = p.get_latest_holding()
            if holding:
                promoter_holding += holding.percentage

        return {
            "symbol": symbol,
            "shareholders": shareholders,
            "promoters": promoters,
            "promoter_holding": promoter_holding,
            "path": path,
        }

    def get_company_markdown(self, search_term: str) -> str:
        """
        Get a comprehensive markdown report for a company.

        Includes company details, key shareholders, recent news, corporate actions,
        and recent announcements.

        Args:
            search_term: Symbol or company name to search for

        Returns:
            Markdown formatted string
        """
        # 1. Search for symbol
        symbols = self.symbol_lookup(search_term, page_size=1)
        if not symbols:
            return f"# Report for '{search_term}'\n\nNo company found."

        symbol = symbols[0]
        path = symbol.path
        isin = symbol.isin

        md = f"# Report for {symbol.company_name}\n\n"
        
        # 2. Company Info
        md += f"## Overview\n"
        md += f"**Symbol:** {symbol.ticker}\n"
        md += f"**ISIN:** {symbol.isin}\n"
        md += f"**Exchange:** {symbol.exchange}\n"
        md += f"**Last Price:** ₹{symbol.last_price}\n"
        if symbol.price_change is not None:
            md += f"**Change:** ₹{symbol.price_change} ({symbol.percent_change}%)\n"
        md += "\n"

        # 3. Key Shareholders
        try:
            shareholders = self.get_key_shareholders(path, page_size=10)
            if shareholders:
                md += f"## Key Shareholders\n"
                
                # Promoters
                promoters = [s for s in shareholders if s.is_promoter and not s.is_group]
                if promoters:
                    md += "**Promoters:**\n"
                    for p in promoters[:5]:
                        holding = p.get_latest_holding()
                        pct = f"{holding.percentage}%" if holding else "N/A"
                        md += f"- {p.description}: {pct}\n"
                    md += "\n"
                
                # Public/Institutional
                others = [s for s in shareholders if not s.is_promoter and not s.is_group]
                if others:
                    md += "**Major Public Shareholders:**\n"
                    for s in others[:5]:
                        holding = s.get_latest_holding()
                        pct = f"{holding.percentage}%" if holding else "N/A"
                        md += f"- {s.description}: {pct}\n"
                    md += "\n"
        except Exception as e:
            logger.error(f"Failed to fetch shareholders: {e}")

        # 4. Corporate Actions (Latest 5)
        try:
            actions = self.get_corporate_actions(path, page_size=5)
            if actions:
                md += f"## Recent Corporate Actions\n"
                md += "| Date | Purpose | Details |\n"
                md += "|---|---|---|\n"
                for act in actions:
                    details = ""
                    if act.is_dividend:
                        details = f"Dividend: ₹{act.dividend_amount}"
                    elif act.is_bonus:
                        details = f"Bonus: {act.bonus_ratio}"
                    elif act.is_split:
                        details = f"Split: {act.face_value_old} -> {act.face_value_new}"
                    
                    md += f"| {act.ex_date_parsed} | {act.purpose} | {details} |\n"
                md += "\n"
        except Exception as e:
            logger.error(f"Failed to fetch corporate actions: {e}")

        # 5. Announcements (Latest 5)
        try:
            announcements = self.get_announcements(path, page_size=5)
            if announcements:
                md += f"## Recent Announcements\n"
                for ann in announcements:
                    md += f"- **{ann.datetime_parsed}**: {ann.details}\n"
                    if ann.has_pdf:
                        md += f"  [PDF Link]({ann.pdf_link})\n"
                md += "\n"
        except Exception as e:
            logger.error(f"Failed to fetch announcements: {e}")

        # 6. News (Latest 5)
        try:
            news = self.get_news(isin, page_size=5)
            if news:
                md += f"## Latest News\n"
                for n in news:
                    headline = n.headline
                    source = n.source_name
                    date = n.source_datetime_parsed
                    link = n.source_link or "#"
                    md += f"- **[{headline}]({link})** ({source}, {date})\n"
                    if n.synopsis:
                        md += f"  > {n.synopsis}\n"
                md += "\n"
        except Exception as e:
            logger.error(f"Failed to fetch news: {e}")

        return md

    def close(self) -> None:
        """Close the client and release resources."""
        self._http.close()

    def __enter__(self) -> "CogencisClient":
        """Context manager entry."""
        return self
def __exit__(self, *args: Any) -> None:
    """Context manager exit."""
    self.close()
            