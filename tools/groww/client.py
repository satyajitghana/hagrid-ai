"""Client for fetching market data from Groww APIs."""

import logging
from typing import Any

from .core.http_client import GrowwHTTPClient
from .core.exceptions import (
    GrowwNotFoundError,
    GrowwParseError,
)

logger = logging.getLogger(__name__)


class GrowwClient:
    """Client for fetching market data from Groww.

    Supports:
    - Stock search
    - Options chain data with greeks
    - Live OHLC prices
    - Company details and fundamentals
    - Market movers (top gainers/losers)
    - Global and Indian indices
    """

    # API URLs
    SEARCH_URL = "https://groww.in/v1/api/search/v3/query/global/st_p_query"
    OPTION_CHAIN_URL = "https://groww.in/v1/pro-option-chain/{symbol}"
    LIVE_PRICE_URL = "https://groww.in/v1/api/stocks_data/v1/accord_points/exchange/{exchange}/segment/CASH/latest_prices_ohlc/{symbol}"
    COMPANY_URL = "https://groww.in/v1/api/stocks_data/v1/company/search_id/{search_id}"
    MARKET_MOVERS_URL = "https://groww.in/v1/api/stocks_data/v2/explore/list/top"
    GLOBAL_INSTRUMENTS_URL = "https://groww.in/v1/api/stocks_data/v1/global_instruments?instrumentType=GLOBAL_INSTRUMENTS"
    INDIAN_INDICES_URL = "https://groww.in/v1/api/stocks_data/v1/company/search_id/nifty?fields=ALL_ASSETS&page=0&size=50"

    # Symbol mapping for indices (user-friendly -> Groww URL slug)
    INDEX_MAP: dict[str, str] = {
        "NIFTY": "nifty",
        "NIFTY50": "nifty",
        "BANKNIFTY": "nifty-bank",
        "NIFTYBANK": "nifty-bank",
        "FINNIFTY": "finnifty",
        "MIDCPNIFTY": "nifty-midcap-select",
    }

    def __init__(self, timeout: float = 30.0) -> None:
        """Initialize the client.

        Args:
            timeout: Request timeout in seconds
        """
        self.http_client = GrowwHTTPClient(timeout=timeout)

    def search(self, query: str, size: int = 6) -> list[dict[str, Any]]:
        """Search for stocks and options by name or symbol.

        Args:
            query: Search query (stock name or symbol)
            size: Number of results to return (default: 6)

        Returns:
            List of search results with keys:
            - search_id: Groww search identifier (URL slug)
            - title: Display name
            - entity_type: "Stocks" or "Option"
            - nse_scrip_code: NSE symbol (if available)
            - bse_scrip_code: BSE symbol (if available)
            - logo_url: Company logo URL (if available)

        Raises:
            GrowwConnectionError: If connection fails
            GrowwAPIError: If request fails
        """
        params = {
            "page": 0,
            "query": query,
            "size": size,
            "web": "true",
        }

        data = self.http_client.get_json(self.SEARCH_URL, params=params)

        results = []
        # API returns data nested under "data.content"
        inner_data = data.get("data", data)
        content = inner_data.get("content", [])

        for item in content:
            entity_type = item.get("entity_type", "")
            result = {
                "search_id": item.get("search_id", ""),
                "title": item.get("title", ""),
                "entity_type": entity_type,
                "nse_scrip_code": item.get("nse_scrip_code"),
                "bse_scrip_code": item.get("bse_scrip_code"),
                "logo_url": item.get("logo_url"),
            }
            results.append(result)

        return results

    def get_option_chain(
        self,
        symbol: str,
        expiry_date: str | None = None,
    ) -> dict[str, Any]:
        """Fetch options chain data with greeks for a symbol.

        Args:
            symbol: Symbol to fetch (e.g., "NIFTY", "BANKNIFTY", "reliance-industries-ltd")
                   Index symbols are automatically mapped to Groww format.
            expiry_date: Expiry date in YYYY-MM-DD format (optional, defaults to nearest)

        Returns:
            Dict with keys:
            - symbol: The symbol used
            - spot_price: Current spot price
            - expiry_date: Selected expiry date
            - available_expiries: List of available expiry dates
            - option_chain: List of strike data with CE/PE info

            Each option_chain entry has:
            - strike_price: Strike price
            - ce: Call option data (ltp, iv, delta, gamma, theta, vega, oi, volume)
            - pe: Put option data (same structure)

        Raises:
            GrowwConnectionError: If connection fails
            GrowwNotFoundError: If symbol not found
            GrowwAPIError: If request fails
        """
        # Map user-friendly symbol to Groww format
        mapped_symbol = self.INDEX_MAP.get(symbol.upper(), symbol)

        url = self.OPTION_CHAIN_URL.format(symbol=mapped_symbol)
        params: dict[str, Any] = {"responseStructure": "LIST"}

        if expiry_date:
            params["expiryDate"] = expiry_date

        data = self.http_client.get_json(url, params=params)

        # Check if this is an index or stock
        is_index = mapped_symbol in self.INDEX_MAP.values()

        # Get spot price from company data
        company_data = data.get("company", {})
        live_data = company_data.get("liveData", {})
        spot_price = live_data.get("ltp", 0)
        # Note: spot price is NOT in paise, only option prices are

        # Get option chain data (structure: optionChain.optionContracts, optionChain.aggregatedDetails)
        option_chain_wrapper = data.get("optionChain", {})
        aggregated_details = option_chain_wrapper.get("aggregatedDetails", {})

        # Get expiries from aggregatedDetails
        expiry_dates = aggregated_details.get("expiryDates", [])
        selected_expiry = aggregated_details.get("currentExpiry", "")

        # Parse option chain contracts
        option_chain_data = option_chain_wrapper.get("optionContracts", [])
        option_chain = []

        for item in option_chain_data:
            strike_price = item.get("strikePrice", 0) / 100  # Convert from paise

            ce_data = self._parse_option_data(item.get("ce", {}), is_index)
            pe_data = self._parse_option_data(item.get("pe", {}), is_index)

            option_chain.append({
                "strike_price": strike_price,
                "ce": ce_data,
                "pe": pe_data,
            })

        return {
            "symbol": symbol,
            "spot_price": spot_price,
            "expiry_date": selected_expiry,
            "available_expiries": expiry_dates,
            "option_chain": option_chain,
        }

    def _parse_option_data(
        self,
        option: dict[str, Any],
        is_index: bool,
    ) -> dict[str, Any] | None:
        """Parse option data (CE or PE) from API response."""
        if not option:
            return None

        live_data = option.get("liveData", {})
        greeks = option.get("greeks", {})

        ltp = live_data.get("ltp", 0)
        # For indices, prices are in paise (ltp is in paise)
        if is_index and ltp:
            ltp = ltp / 100

        return {
            "ltp": ltp,
            "iv": greeks.get("iv"),
            "delta": greeks.get("delta"),
            "gamma": greeks.get("gamma"),
            "theta": greeks.get("theta"),
            "vega": greeks.get("vega"),
            "oi": live_data.get("oi", 0),
            "volume": live_data.get("volume", 0),  # API uses "volume" not "vol"
            "day_change": live_data.get("dayChange"),
            "day_change_perc": live_data.get("dayChangePerc"),
        }

    def get_live_price(
        self,
        symbol: str,
        exchange: str = "NSE",
    ) -> dict[str, Any]:
        """Fetch live OHLC price for a stock.

        Args:
            symbol: NSE/BSE script code (e.g., "RELIANCE", "INFY", "TCS")
            exchange: Exchange - "NSE" or "BSE" (default: "NSE")

        Returns:
            Dict with keys:
            - symbol: Stock symbol
            - exchange: Exchange
            - ltp: Last traded price
            - open: Open price
            - high: High price
            - low: Low price
            - close: Previous close
            - volume: Trading volume
            - day_change: Absolute change
            - day_change_perc: Percentage change
            - year_high: 52-week high
            - year_low: 52-week low
            - timestamp: Last update timestamp

        Raises:
            GrowwConnectionError: If connection fails
            GrowwNotFoundError: If symbol not found
            GrowwAPIError: If request fails
        """
        url = self.LIVE_PRICE_URL.format(exchange=exchange, symbol=symbol)
        data = self.http_client.get_json(url)

        return {
            "symbol": symbol,
            "exchange": exchange,
            "ltp": data.get("ltp"),
            "open": data.get("open"),
            "high": data.get("high"),
            "low": data.get("low"),
            "close": data.get("close"),
            "volume": data.get("volume"),
            "day_change": data.get("dayChange"),
            "day_change_perc": data.get("dayChangePerc"),
            "year_high": data.get("high52"),
            "year_low": data.get("low52"),
            "timestamp": data.get("tsInMillis"),
        }

    def get_company_details(self, search_id: str) -> dict[str, Any]:
        """Fetch company details and fundamentals.

        Args:
            search_id: Groww search ID (URL slug like "reliance-industries-ltd")

        Returns:
            Dict with comprehensive company data including:
            - basic: Company name, sector, industry, about
            - stats: P/E, P/B, market cap, ROE, EPS, dividend yield
            - financials: Revenue, profit, quarterly/annual data
            - shareholding: Promoter, FII, DII, retail percentages
            - live_data: Current price, day change

        Raises:
            GrowwConnectionError: If connection fails
            GrowwNotFoundError: If company not found
            GrowwAPIError: If request fails
        """
        url = self.COMPANY_URL.format(search_id=search_id)
        params = {"page": 0, "size": 10}

        data = self.http_client.get_json(url, params=params)

        header = data.get("header", {})
        stats = data.get("stats", {})
        financials = data.get("financials", {})
        shareholding = data.get("shareholdingPattern", {})
        live_data = data.get("liveData", {})
        about = data.get("about", {})

        # Parse shareholding
        shareholding_data = {}
        if shareholding:
            labels = shareholding.get("labels", [])
            values = shareholding.get("values", [])
            if labels and values and len(values) > 0:
                latest_values = values[0]
                for i, label in enumerate(labels):
                    if i < len(latest_values):
                        shareholding_data[label.lower().replace(" ", "_")] = latest_values[i]

        return {
            "basic": {
                "name": header.get("displayName", ""),
                "nse_symbol": header.get("nseScriptCode"),
                "bse_symbol": header.get("bseScriptCode"),
                "sector": about.get("sector"),
                "industry": about.get("industry"),
                "founded": about.get("foundedYear"),
                "ceo": about.get("ceo"),
                "headquarters": about.get("hq"),
                "website": about.get("website"),
                "about": about.get("longDescription", "")[:500] if about.get("longDescription") else None,
            },
            "stats": {
                "market_cap": stats.get("marketCap"),
                "pe_ratio": stats.get("peRatio"),
                "pb_ratio": stats.get("pbRatio"),
                "roe": stats.get("roe"),
                "eps": stats.get("eps"),
                "dividend_yield": stats.get("divYield"),
                "book_value": stats.get("bookValue"),
                "face_value": stats.get("faceValue"),
                "debt_to_equity": stats.get("debtToEquity"),
                "roce": stats.get("roce"),
            },
            "live_data": {
                "ltp": live_data.get("ltp"),
                "open": live_data.get("open"),
                "high": live_data.get("high"),
                "low": live_data.get("low"),
                "close": live_data.get("close"),
                "day_change": live_data.get("dayChange"),
                "day_change_perc": live_data.get("dayChangePerc"),
                "year_high": live_data.get("high52"),
                "year_low": live_data.get("low52"),
            },
            "shareholding": shareholding_data,
            "financials_summary": {
                "revenue": financials.get("ttmRevenue"),
                "net_profit": financials.get("ttmNetProfit"),
                "operating_profit_margin": financials.get("ttmOpm"),
                "net_profit_margin": financials.get("ttmNpm"),
            },
        }

    def get_market_movers(
        self,
        categories: list[str] | None = None,
        size: int = 5,
    ) -> dict[str, list[dict[str, Any]]]:
        """Fetch market movers - top gainers, losers, and popular stocks.

        Args:
            categories: List of categories to fetch. Options:
                - "TOP_GAINERS"
                - "TOP_LOSERS"
                - "POPULAR_STOCKS_MOST_BOUGHT"
                Defaults to TOP_GAINERS and TOP_LOSERS
            size: Number of stocks per category (default: 5)

        Returns:
            Dict with category names as keys, each containing list of stocks:
            - search_id: Groww search ID
            - symbol: NSE symbol
            - name: Company name
            - ltp: Last traded price
            - day_change: Absolute change
            - day_change_perc: Percentage change

        Raises:
            GrowwConnectionError: If connection fails
            GrowwAPIError: If request fails
        """
        if categories is None:
            categories = ["TOP_GAINERS", "TOP_LOSERS"]

        params = {
            "discoveryFilterTypes": ",".join(categories),
            "page": 0,
            "size": size,
        }

        data = self.http_client.get_json(self.MARKET_MOVERS_URL, params=params)

        result = {}
        # API returns data in exploreCompanies.CATEGORY_NAME format
        explore_companies = data.get("exploreCompanies", {})

        for category in categories:
            stocks = explore_companies.get(category, [])

            result[category.lower()] = []
            for stock in stocks:
                company = stock.get("company", {})
                stats = stock.get("stats", {})

                result[category.lower()].append({
                    "search_id": company.get("searchId", ""),
                    "symbol": company.get("nseScriptCode", ""),
                    "name": company.get("companyName", ""),
                    "ltp": stats.get("ltp"),
                    "day_change": stats.get("dayChange"),
                    "day_change_perc": stats.get("dayChangePerc"),
                })

        return result

    def get_global_indices(self) -> list[dict[str, Any]]:
        """Fetch live prices for global indices.

        Returns live market data for major global indices including:
        - SGX Nifty (GIFT Nifty)
        - Dow Futures, Dow Jones
        - S&P 500
        - NIKKEI 225
        - Hang Seng
        - DAX (Germany)
        - CAC 40 (France)
        - KOSPI (South Korea)
        - FTSE 100 (UK)

        Returns:
            List of dicts with keys:
            - symbol: Index symbol (e.g., "SGX NIFTY", "^DJI")
            - name: Display name (e.g., "GIFT NIFTY", "Dow")
            - country: Country name
            - continent: Continent (ASIA, US, EUROPE)
            - value: Current price
            - open, high, low, close: OHLC prices
            - day_change: Absolute change
            - day_change_perc: Percentage change

        Raises:
            GrowwConnectionError: If connection fails
            GrowwAPIError: If request fails
        """
        data = self.http_client.get_json(self.GLOBAL_INSTRUMENTS_URL)

        instruments = data.get("aggregatedGlobalInstrumentDto", [])
        result = []

        for item in instruments:
            price = item.get("livePriceDto", {})
            details = item.get("instrumentDetailDto", {})

            result.append({
                "symbol": details.get("symbol", ""),
                "name": details.get("name", ""),
                "country": details.get("country", ""),
                "continent": details.get("continent", ""),
                "value": price.get("value"),
                "open": price.get("open"),
                "high": price.get("high"),
                "low": price.get("low"),
                "close": price.get("close"),
                "day_change": price.get("dayChange"),
                "day_change_perc": price.get("dayChangePerc"),
            })

        return result

    def get_indian_indices(self) -> list[dict[str, Any]]:
        """Fetch Indian market indices data.

        Returns data for major Indian indices including:
        - NIFTY 50, NIFTY Bank, NIFTY Financial Services
        - BSE Sensex, BSE Bankex
        - India VIX
        - NIFTY Next 50, NIFTY 100, NIFTY 500
        - NIFTY Midcap 100/150, NIFTY Smallcap 100/250
        - Sectoral indices: IT, Pharma, Auto, FMCG, Metal, PSU Bank

        Returns:
            List of dicts with keys:
            - search_id: Groww search identifier
            - symbol: Index symbol (e.g., "NIFTY", "BANKNIFTY")
            - display_name: Full name (e.g., "NIFTY 50")
            - short_name: Short name
            - is_fno_enabled: Whether F&O trading is available
            - nse_script_code: NSE script code (if available)
            - bse_script_code: BSE script code (if available)
            - year_low: 52-week low price
            - year_high: 52-week high price

        Raises:
            GrowwConnectionError: If connection fails
            GrowwAPIError: If request fails
        """
        data = self.http_client.get_json(self.INDIAN_INDICES_URL)

        assets = data.get("allAssets", [])
        result = []

        for item in assets:
            header = item.get("header", {})

            result.append({
                "search_id": header.get("searchId", ""),
                "symbol": header.get("isin", ""),
                "display_name": header.get("displayName", ""),
                "short_name": header.get("shortName", ""),
                "is_fno_enabled": header.get("isFnoEnabled", False),
                "nse_script_code": header.get("nseScriptCode"),
                "bse_script_code": header.get("bseScriptCode"),
                "year_low": item.get("yearLowPrice"),
                "year_high": item.get("yearHighPrice"),
            })

        return result

    def close(self) -> None:
        """Close the HTTP client."""
        self.http_client.close()

    def __enter__(self) -> "GrowwClient":
        """Context manager entry."""
        return self

    def __exit__(self, *args: Any) -> None:
        """Context manager exit."""
        self.close()
