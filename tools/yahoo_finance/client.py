"""Yahoo Finance API Client."""

import logging
from typing import Any, List, Optional, Union
from datetime import datetime, timedelta
import pandas as pd

import yfinance as yf
from .models.ticker import (
    TickerInfo, TickerHistory, TickerFinancials, PriceHistoryEntry,
    TickerHolders, TickerAnalysis, TickerCalendar, TickerOptions,
    TickerSustainability, TickerDividends, DividendEntry,
    TickerSplits, SplitEntry, TickerActions, ActionEntry,
    TickerCapitalGains, CapitalGainEntry, TickerShares, SharesEntry,
    TickerFastInfo, TickerHistoryMetadata, TickerSECFilings, SECFiling,
    TickerISIN, FundsData
)
from .models.market import (
    GlobalIndex, MarketStatus, CalendarsData, SearchResults,
    LookupResults, SectorData, IndustryData, ScreenerResult,
    BulkDownloadResult
)

logger = logging.getLogger(__name__)


class YFinanceClient:
    """
    Client for interacting with Yahoo Finance via yfinance library.

    This client provides access to:
    - Ticker data (info, history, financials, holders, analysis, etc.)
    - Market data (status, summary)
    - Calendars (earnings, IPO, splits, economic events)
    - Search and Lookup functionality
    - Sector and Industry data
    - Screener functionality
    - Bulk download

    Note: Live/WebSocket APIs are not supported.
    """

    def __init__(self) -> None:
        """Initialize the YFinance client."""
        pass

    def _df_to_list_of_dicts(self, df: pd.DataFrame, transpose: bool = True) -> List[dict]:
        """Helper to convert DataFrame to list of dicts."""
        if df is None:
            return []

        # Handle dict input (yfinance sometimes returns dict instead of DataFrame)
        if isinstance(df, dict):
            return [df] if df else []

        # Handle DataFrame
        if hasattr(df, 'empty') and df.empty:
            return []

        try:
            if transpose:
                df_T = df.T
                df_T.index.name = "Date" if df_T.index.name is None else df_T.index.name
                df_T = df_T.reset_index()
                if 'Date' in df_T.columns:
                    df_T['Date'] = df_T['Date'].astype(str)
                return df_T.to_dict(orient="records")
            else:
                df_reset = df.reset_index()
                return df_reset.to_dict(orient="records")
        except Exception as e:
            logger.error(f"Error converting DataFrame: {e}")
            return []

    def _series_to_list_of_dicts(self, series: pd.Series, value_name: str = "value") -> List[dict]:
        """Helper to convert Series to list of dicts with date and value."""
        if series is None:
            return []

        # Handle dict input (yfinance sometimes returns dict instead of Series)
        if isinstance(series, dict):
            return [{"date": k, value_name: v} for k, v in series.items()] if series else []

        # Handle Series
        if hasattr(series, 'empty') and series.empty:
            return []

        try:
            df = series.reset_index()
            df.columns = ["date", value_name]
            return df.to_dict(orient="records")
        except Exception as e:
            logger.error(f"Error converting Series: {e}")
            return []

    # ==================== TICKER INFO ====================

    def get_ticker_info(self, symbol: str) -> TickerInfo:
        """
        Get comprehensive information for a ticker.

        Args:
            symbol: Ticker symbol (e.g., "AAPL", "MSFT", "RELIANCE.NS")

        Returns:
            TickerInfo object
        """
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            return TickerInfo(symbol=symbol, info=info)
        except Exception as e:
            logger.error(f"Error fetching info for {symbol}: {e}")
            return TickerInfo(symbol=symbol, info={})

    def get_fast_info(self, symbol: str) -> TickerFastInfo:
        """
        Get fast/lightweight price info for a ticker.

        This is faster than get_ticker_info() as it only fetches essential price data.

        Args:
            symbol: Ticker symbol

        Returns:
            TickerFastInfo object
        """
        try:
            ticker = yf.Ticker(symbol)
            fi = ticker.fast_info
            return TickerFastInfo(
                symbol=symbol,
                currency=getattr(fi, 'currency', None),
                day_high=getattr(fi, 'day_high', None),
                day_low=getattr(fi, 'day_low', None),
                exchange=getattr(fi, 'exchange', None),
                fifty_day_average=getattr(fi, 'fifty_day_average', None),
                last_price=getattr(fi, 'last_price', None),
                last_volume=getattr(fi, 'last_volume', None),
                market_cap=getattr(fi, 'market_cap', None),
                open=getattr(fi, 'open', None),
                previous_close=getattr(fi, 'previous_close', None),
                quote_type=getattr(fi, 'quote_type', None),
                regular_market_previous_close=getattr(fi, 'regular_market_previous_close', None),
                shares=getattr(fi, 'shares', None),
                ten_day_average_volume=getattr(fi, 'ten_day_average_volume', None),
                three_month_average_volume=getattr(fi, 'three_month_average_volume', None),
                timezone=getattr(fi, 'timezone', None),
                two_hundred_day_average=getattr(fi, 'two_hundred_day_average', None),
                year_change=getattr(fi, 'year_change', None),
                year_high=getattr(fi, 'year_high', None),
                year_low=getattr(fi, 'year_low', None),
            )
        except Exception as e:
            logger.error(f"Error fetching fast_info for {symbol}: {e}")
            return TickerFastInfo(symbol=symbol)

    def get_isin(self, symbol: str) -> TickerISIN:
        """
        Get ISIN (International Securities Identification Number) for a ticker.

        Args:
            symbol: Ticker symbol

        Returns:
            TickerISIN object
        """
        try:
            ticker = yf.Ticker(symbol)
            isin = ticker.isin
            return TickerISIN(symbol=symbol, isin=isin if isin != "-" else None)
        except Exception as e:
            logger.error(f"Error fetching ISIN for {symbol}: {e}")
            return TickerISIN(symbol=symbol)

    # ==================== HISTORICAL DATA ====================

    def get_historical_data(
        self,
        symbol: str,
        period: str = "1mo",
        interval: str = "1d",
        start: Optional[str] = None,
        end: Optional[str] = None,
        prepost: bool = False,
        auto_adjust: bool = True,
        repair: bool = False,
    ) -> TickerHistory:
        """
        Get historical market data.

        Args:
            symbol: Ticker symbol
            period: Data period (1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max)
            interval: Data interval (1m, 2m, 5m, 15m, 30m, 60m, 90m, 1h, 1d, 5d, 1wk, 1mo, 3mo)
            start: Start date string (YYYY-MM-DD)
            end: End date string (YYYY-MM-DD)
            prepost: Include pre and post market data
            auto_adjust: Adjust all OHLC automatically
            repair: Detect and repair price errors

        Returns:
            TickerHistory object
        """
        try:
            ticker = yf.Ticker(symbol)
            hist_df = ticker.history(
                period=period,
                interval=interval,
                start=start,
                end=end,
                prepost=prepost,
                auto_adjust=auto_adjust,
                repair=repair
            )

            history_entries = []
            for index, row in hist_df.iterrows():
                entry = PriceHistoryEntry(
                    date=index,
                    open=row["Open"],
                    high=row["High"],
                    low=row["Low"],
                    close=row["Close"],
                    volume=int(row["Volume"]),
                    dividends=row.get("Dividends", 0.0),
                    stock_splits=row.get("Stock Splits", 0.0)
                )
                history_entries.append(entry)

            return TickerHistory(
                symbol=symbol,
                period=period,
                interval=interval,
                history=history_entries
            )
        except Exception as e:
            logger.error(f"Error fetching history for {symbol}: {e}")
            return TickerHistory(symbol=symbol, period=period, interval=interval, history=[])

    def get_history_metadata(self, symbol: str) -> TickerHistoryMetadata:
        """
        Get history metadata for a ticker.

        Args:
            symbol: Ticker symbol

        Returns:
            TickerHistoryMetadata object
        """
        try:
            ticker = yf.Ticker(symbol)
            metadata = ticker.get_history_metadata()
            return TickerHistoryMetadata(symbol=symbol, metadata=metadata if metadata else {})
        except Exception as e:
            logger.error(f"Error fetching history metadata for {symbol}: {e}")
            return TickerHistoryMetadata(symbol=symbol)

    # ==================== DIVIDENDS, SPLITS, ACTIONS ====================

    def get_dividends(self, symbol: str, period: str = "max") -> TickerDividends:
        """
        Get dividend history for a ticker.

        Args:
            symbol: Ticker symbol
            period: Period to fetch (default: max)

        Returns:
            TickerDividends object
        """
        try:
            ticker = yf.Ticker(symbol)
            divs = ticker.get_dividends()

            entries = []
            if divs is not None and not divs.empty:
                for date, value in divs.items():
                    entries.append(DividendEntry(date=date, dividend=float(value)))

            return TickerDividends(symbol=symbol, dividends=entries)
        except Exception as e:
            logger.error(f"Error fetching dividends for {symbol}: {e}")
            return TickerDividends(symbol=symbol)

    def get_splits(self, symbol: str) -> TickerSplits:
        """
        Get stock split history for a ticker.

        Args:
            symbol: Ticker symbol

        Returns:
            TickerSplits object
        """
        try:
            ticker = yf.Ticker(symbol)
            splits = ticker.get_splits()

            entries = []
            if splits is not None and not splits.empty:
                for date, value in splits.items():
                    entries.append(SplitEntry(date=date, split_ratio=float(value)))

            return TickerSplits(symbol=symbol, splits=entries)
        except Exception as e:
            logger.error(f"Error fetching splits for {symbol}: {e}")
            return TickerSplits(symbol=symbol)

    def get_actions(self, symbol: str) -> TickerActions:
        """
        Get corporate actions (dividends + splits) for a ticker.

        Args:
            symbol: Ticker symbol

        Returns:
            TickerActions object
        """
        try:
            ticker = yf.Ticker(symbol)
            actions = ticker.get_actions()

            entries = []
            if actions is not None and not actions.empty:
                for date, row in actions.iterrows():
                    entries.append(ActionEntry(
                        date=date,
                        dividends=float(row.get('Dividends', 0)),
                        stock_splits=float(row.get('Stock Splits', 0))
                    ))

            return TickerActions(symbol=symbol, actions=entries)
        except Exception as e:
            logger.error(f"Error fetching actions for {symbol}: {e}")
            return TickerActions(symbol=symbol)

    def get_capital_gains(self, symbol: str) -> TickerCapitalGains:
        """
        Get capital gains distributions for a ticker (mainly for mutual funds/ETFs).

        Args:
            symbol: Ticker symbol

        Returns:
            TickerCapitalGains object
        """
        try:
            ticker = yf.Ticker(symbol)
            cg = ticker.get_capital_gains()

            entries = []
            if cg is not None and not cg.empty:
                for date, value in cg.items():
                    entries.append(CapitalGainEntry(date=date, capital_gain=float(value)))

            return TickerCapitalGains(symbol=symbol, capital_gains=entries)
        except Exception as e:
            logger.error(f"Error fetching capital gains for {symbol}: {e}")
            return TickerCapitalGains(symbol=symbol)

    def get_shares_full(self, symbol: str) -> TickerShares:
        """
        Get full shares outstanding history for a ticker.

        Args:
            symbol: Ticker symbol

        Returns:
            TickerShares object
        """
        try:
            ticker = yf.Ticker(symbol)
            shares = ticker.get_shares_full()

            entries = []
            if shares is not None and not shares.empty:
                for date, value in shares.items():
                    if pd.notna(value):
                        entries.append(SharesEntry(date=date, shares=int(value)))

            return TickerShares(symbol=symbol, shares=entries)
        except Exception as e:
            logger.error(f"Error fetching shares for {symbol}: {e}")
            return TickerShares(symbol=symbol)

    # ==================== FINANCIALS ====================

    def get_financials(self, symbol: str) -> TickerFinancials:
        """
        Get financial statements (income statement, balance sheet, cash flow).
        Includes annual, quarterly, and TTM data.

        Args:
            symbol: Ticker symbol

        Returns:
            TickerFinancials object
        """
        try:
            ticker = yf.Ticker(symbol)

            return TickerFinancials(
                symbol=symbol,
                income_statement=self._df_to_list_of_dicts(ticker.financials),
                balance_sheet=self._df_to_list_of_dicts(ticker.balance_sheet),
                cash_flow=self._df_to_list_of_dicts(ticker.cashflow),
                quarterly_income_statement=self._df_to_list_of_dicts(ticker.quarterly_financials),
                quarterly_balance_sheet=self._df_to_list_of_dicts(ticker.quarterly_balance_sheet),
                quarterly_cash_flow=self._df_to_list_of_dicts(ticker.quarterly_cashflow),
                ttm_income_statement=self._df_to_list_of_dicts(getattr(ticker, 'ttm_income_stmt', None)),
                ttm_cash_flow=self._df_to_list_of_dicts(getattr(ticker, 'ttm_cashflow', None)),
            )
        except Exception as e:
            logger.error(f"Error fetching financials for {symbol}: {e}")
            return TickerFinancials(symbol=symbol)

    def get_sec_filings(self, symbol: str) -> TickerSECFilings:
        """
        Get SEC filings for a ticker.

        Args:
            symbol: Ticker symbol

        Returns:
            TickerSECFilings object
        """
        try:
            ticker = yf.Ticker(symbol)
            filings_data = ticker.sec_filings

            filings = []
            if filings_data:
                for f in filings_data:
                    # Handle exhibits - can be dict or list
                    exhibits_raw = f.get('exhibits', [])
                    if isinstance(exhibits_raw, dict):
                        exhibits = [{"name": k, "url": v} for k, v in exhibits_raw.items()]
                    else:
                        exhibits = exhibits_raw if exhibits_raw else []

                    filings.append(SECFiling(
                        date=f.get('date'),
                        type=f.get('type'),
                        title=f.get('title'),
                        edgar_url=f.get('edgarUrl'),
                        exhibits=exhibits
                    ))

            return TickerSECFilings(symbol=symbol, filings=filings)
        except Exception as e:
            logger.error(f"Error fetching SEC filings for {symbol}: {e}")
            return TickerSECFilings(symbol=symbol)

    # ==================== HOLDERS ====================

    def get_holders(self, symbol: str) -> TickerHolders:
        """
        Get holder information including major, institutional, mutual fund holders,
        and insider transactions.

        Args:
            symbol: Ticker symbol

        Returns:
            TickerHolders object
        """
        try:
            ticker = yf.Ticker(symbol)
            return TickerHolders(
                symbol=symbol,
                major_holders=self._df_to_list_of_dicts(ticker.major_holders, transpose=False),
                institutional_holders=self._df_to_list_of_dicts(ticker.institutional_holders, transpose=False),
                mutualfund_holders=self._df_to_list_of_dicts(ticker.mutualfund_holders, transpose=False),
                insider_roster_holders=self._df_to_list_of_dicts(ticker.insider_roster_holders, transpose=False),
                insider_purchases=self._df_to_list_of_dicts(getattr(ticker, 'insider_purchases', None), transpose=False),
                insider_transactions=self._df_to_list_of_dicts(getattr(ticker, 'insider_transactions', None), transpose=False),
            )
        except Exception as e:
            logger.error(f"Error fetching holders for {symbol}: {e}")
            return TickerHolders(symbol=symbol)

    # ==================== ANALYSIS ====================

    def get_analysis(self, symbol: str) -> TickerAnalysis:
        """
        Get analysis data including recommendations, price targets, and estimates.

        Args:
            symbol: Ticker symbol

        Returns:
            TickerAnalysis object
        """
        try:
            ticker = yf.Ticker(symbol)
            return TickerAnalysis(
                symbol=symbol,
                recommendations=self._df_to_list_of_dicts(ticker.recommendations, transpose=False),
                recommendations_summary=self._df_to_list_of_dicts(ticker.recommendations_summary, transpose=False),
                upgrades_downgrades=self._df_to_list_of_dicts(ticker.upgrades_downgrades, transpose=False),
                analyst_price_targets=ticker.analyst_price_targets if ticker.analyst_price_targets else {},
                earnings_estimate=self._df_to_list_of_dicts(ticker.earnings_estimate, transpose=True),
                revenue_estimate=self._df_to_list_of_dicts(ticker.revenue_estimate, transpose=True),
                earnings_history=self._df_to_list_of_dicts(ticker.earnings_history, transpose=False),
                eps_trend=self._df_to_list_of_dicts(ticker.eps_trend, transpose=True),
                eps_revisions=self._df_to_list_of_dicts(ticker.eps_revisions, transpose=True),
                growth_estimates=self._df_to_list_of_dicts(ticker.growth_estimates, transpose=True),
            )
        except Exception as e:
            logger.error(f"Error fetching analysis for {symbol}: {e}")
            return TickerAnalysis(symbol=symbol)

    # ==================== CALENDAR ====================

    def get_calendar(self, symbol: str) -> TickerCalendar:
        """
        Get calendar events for a ticker.

        Args:
            symbol: Ticker symbol

        Returns:
            TickerCalendar object
        """
        try:
            ticker = yf.Ticker(symbol)
            return TickerCalendar(
                symbol=symbol,
                calendar=ticker.calendar if isinstance(ticker.calendar, dict) else {},
                earnings_dates=self._df_to_list_of_dicts(ticker.earnings_dates, transpose=False)
            )
        except Exception as e:
            logger.error(f"Error fetching calendar for {symbol}: {e}")
            return TickerCalendar(symbol=symbol)

    # ==================== OPTIONS ====================

    def get_options(self, symbol: str, expiration: Optional[str] = None) -> TickerOptions:
        """
        Get options chain for a ticker.

        Args:
            symbol: Ticker symbol
            expiration: Specific expiration date (optional, defaults to nearest)

        Returns:
            TickerOptions object
        """
        try:
            ticker = yf.Ticker(symbol)
            exp_dates = ticker.options

            calls = []
            puts = []

            if exp_dates:
                exp_to_use = expiration if expiration and expiration in exp_dates else exp_dates[0]
                chain = ticker.option_chain(exp_to_use)
                calls = self._df_to_list_of_dicts(chain.calls, transpose=False)
                puts = self._df_to_list_of_dicts(chain.puts, transpose=False)

            return TickerOptions(
                symbol=symbol,
                expiration_dates=list(exp_dates) if exp_dates else [],
                calls=calls,
                puts=puts
            )
        except Exception as e:
            logger.error(f"Error fetching options for {symbol}: {e}")
            return TickerOptions(symbol=symbol)

    # ==================== SUSTAINABILITY ====================

    def get_sustainability(self, symbol: str) -> TickerSustainability:
        """
        Get ESG/sustainability scores for a ticker.

        Args:
            symbol: Ticker symbol

        Returns:
            TickerSustainability object
        """
        try:
            ticker = yf.Ticker(symbol)
            sus = ticker.sustainability
            sus_dict = {}
            if sus is not None and not sus.empty:
                sus_dict = sus.to_dict()[list(sus.columns)[0]]

            return TickerSustainability(
                symbol=symbol,
                sustainability=sus_dict
            )
        except Exception as e:
            logger.error(f"Error fetching sustainability for {symbol}: {e}")
            return TickerSustainability(symbol=symbol)

    # ==================== FUNDS DATA (ETFs/Mutual Funds) ====================

    def get_funds_data(self, symbol: str) -> FundsData:
        """
        Get fund-specific data for ETFs and Mutual Funds.

        Includes fund overview, operations, holdings, sector weightings, etc.

        Args:
            symbol: ETF or Mutual Fund symbol (e.g., "SPY", "VFIAX")

        Returns:
            FundsData object
        """
        try:
            ticker = yf.Ticker(symbol)
            fd = ticker.funds_data

            if fd is None:
                return FundsData(symbol=symbol)

            # Convert DataFrames to dicts - use try/except for DataFrame checks
            top_holdings = []
            try:
                th = getattr(fd, 'top_holdings', None)
                if th is not None and isinstance(th, pd.DataFrame) and not th.empty:
                    top_holdings = self._df_to_list_of_dicts(th, transpose=False)
            except Exception:
                pass

            sector_weightings = {}
            try:
                sw = getattr(fd, 'sector_weightings', None)
                if sw is not None:
                    if isinstance(sw, pd.DataFrame) and not sw.empty:
                        sector_weightings = sw.to_dict()
                    elif isinstance(sw, dict):
                        sector_weightings = sw
            except Exception:
                pass

            # Helper to safely get dict attributes
            def safe_get_dict(attr_name):
                try:
                    val = getattr(fd, attr_name, None)
                    if val is None:
                        return {}
                    if isinstance(val, pd.DataFrame):
                        return val.to_dict() if not val.empty else {}
                    if isinstance(val, dict):
                        return val
                    return {}
                except Exception:
                    return {}

            return FundsData(
                symbol=symbol,
                description=getattr(fd, 'description', None),
                fund_overview=safe_get_dict('fund_overview'),
                fund_operations=safe_get_dict('fund_operations'),
                asset_classes=safe_get_dict('asset_classes'),
                top_holdings=top_holdings,
                equity_holdings=safe_get_dict('equity_holdings'),
                bond_holdings=safe_get_dict('bond_holdings'),
                bond_ratings=safe_get_dict('bond_ratings'),
                sector_weightings=sector_weightings,
            )
        except Exception as e:
            logger.error(f"Error fetching funds data for {symbol}: {e}")
            return FundsData(symbol=symbol)

    # ==================== NEWS ====================

    def get_news(self, symbol: str) -> List[dict]:
        """
        Get news for a ticker.

        Args:
            symbol: Ticker symbol

        Returns:
            List of news articles
        """
        try:
            ticker = yf.Ticker(symbol)
            return ticker.news or []
        except Exception as e:
            logger.error(f"Error fetching news for {symbol}: {e}")
            return []

    # ==================== MARKET ====================

    def get_market_status(self, market: str = "US") -> MarketStatus:
        """
        Get market status and summary.

        Available markets: US, GB, ASIA, EUROPE, RATES, COMMODITIES, CURRENCIES, CRYPTOCURRENCIES

        Args:
            market: Market identifier

        Returns:
            MarketStatus object
        """
        try:
            m = yf.Market(market)
            return MarketStatus(
                market=market,
                status=m.status if hasattr(m, 'status') else {},
                summary=m.summary if hasattr(m, 'summary') else {}
            )
        except Exception as e:
            logger.error(f"Error fetching market status for {market}: {e}")
            return MarketStatus(market=market)

    # ==================== CALENDARS ====================

    def get_calendars(
        self,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
    ) -> CalendarsData:
        """
        Get market calendars (earnings, IPO, splits, economic events).

        Args:
            start: Start date (default: today)
            end: End date (default: today + 7 days)

        Returns:
            CalendarsData object
        """
        try:
            if start is None:
                start = datetime.now()
            if end is None:
                end = start + timedelta(days=7)

            cal = yf.Calendars(start, end)

            earnings = []
            ipo_info = []
            splits = []
            economic_events = []

            try:
                ec = cal.earnings_calendar
                if ec is not None and not ec.empty:
                    earnings = self._df_to_list_of_dicts(ec, transpose=False)
            except Exception:
                pass

            try:
                ipo = cal.ipo_info_calendar
                if ipo is not None and not ipo.empty:
                    ipo_info = self._df_to_list_of_dicts(ipo, transpose=False)
            except Exception:
                pass

            try:
                sp = cal.splits_calendar
                if sp is not None and not sp.empty:
                    splits = self._df_to_list_of_dicts(sp, transpose=False)
            except Exception:
                pass

            try:
                econ = cal.economic_events_calendar
                if econ is not None and not econ.empty:
                    economic_events = self._df_to_list_of_dicts(econ, transpose=False)
            except Exception:
                pass

            return CalendarsData(
                start_date=start,
                end_date=end,
                earnings=earnings,
                ipo_info=ipo_info,
                splits=splits,
                economic_events=economic_events
            )
        except Exception as e:
            logger.error(f"Error fetching calendars: {e}")
            return CalendarsData()

    # ==================== SEARCH & LOOKUP ====================

    def search(
        self,
        query: str,
        max_results: int = 10,
        news_count: int = 5,
        include_research: bool = False
    ) -> SearchResults:
        """
        Search for tickers and news.

        Args:
            query: Search query
            max_results: Maximum number of quote results
            news_count: Number of news results
            include_research: Include research reports

        Returns:
            SearchResults object
        """
        try:
            search = yf.Search(
                query,
                max_results=max_results,
                news_count=news_count,
                include_research=include_research
            )

            return SearchResults(
                query=query,
                quotes=search.quotes or [],
                news=search.news or [],
                research=search.research if include_research and hasattr(search, 'research') else []
            )
        except Exception as e:
            logger.error(f"Error searching for {query}: {e}")
            return SearchResults(query=query)

    def lookup(self, query: str, count: int = 10) -> LookupResults:
        """
        Lookup tickers by query with filtering by type.

        Args:
            query: Lookup query
            count: Number of results per category

        Returns:
            LookupResults object
        """
        try:
            lk = yf.Lookup(query)

            # Helper to safely get lookup results (returns DataFrame)
            def safe_get_lookup(method_name, cnt):
                try:
                    method = getattr(lk, method_name, None)
                    if method:
                        result = method(count=cnt)
                        if isinstance(result, pd.DataFrame) and not result.empty:
                            return self._df_to_list_of_dicts(result, transpose=False)
                    return []
                except Exception:
                    return []

            return LookupResults(
                query=query,
                all=safe_get_lookup('get_all', count),
                stocks=safe_get_lookup('get_stock', count),
                mutual_funds=safe_get_lookup('get_mutualfund', count),
                etfs=safe_get_lookup('get_etf', count),
                indices=safe_get_lookup('get_index', count),
                futures=safe_get_lookup('get_future', count),
                currencies=safe_get_lookup('get_currency', count),
                cryptocurrencies=safe_get_lookup('get_cryptocurrency', count),
            )
        except Exception as e:
            logger.error(f"Error looking up {query}: {e}")
            return LookupResults(query=query)

    # ==================== SECTOR & INDUSTRY ====================

    def get_sector(self, sector_key: str) -> SectorData:
        """
        Get sector data including top companies, ETFs, and industries.

        Sector keys: technology, healthcare, financial-services, consumer-cyclical,
        communication-services, industrials, consumer-defensive, energy,
        basic-materials, real-estate, utilities

        Args:
            sector_key: Sector identifier

        Returns:
            SectorData object
        """
        try:
            sector = yf.Sector(sector_key)

            industries = []
            if hasattr(sector, 'industries') and sector.industries is not None:
                if isinstance(sector.industries, pd.DataFrame):
                    industries = self._df_to_list_of_dicts(sector.industries, transpose=False)
                elif isinstance(sector.industries, dict):
                    industries = [{"key": k, "name": v} for k, v in sector.industries.items()]

            return SectorData(
                key=sector_key,
                name=getattr(sector, 'name', None),
                symbol=getattr(sector, 'symbol', None),
                overview=getattr(sector, 'overview', {}) or {},
                top_companies=self._df_to_list_of_dicts(getattr(sector, 'top_companies', None), transpose=False),
                top_etfs=self._df_to_list_of_dicts(getattr(sector, 'top_etfs', None), transpose=False),
                top_mutual_funds=self._df_to_list_of_dicts(getattr(sector, 'top_mutual_funds', None), transpose=False),
                industries=industries,
                research_reports=getattr(sector, 'research_reports', []) or [],
            )
        except Exception as e:
            logger.error(f"Error fetching sector {sector_key}: {e}")
            return SectorData(key=sector_key)

    def get_industry(self, industry_key: str) -> IndustryData:
        """
        Get industry data including top companies.

        Industry keys can be obtained from sector.industries or ticker.info['industryKey']

        Args:
            industry_key: Industry identifier

        Returns:
            IndustryData object
        """
        try:
            industry = yf.Industry(industry_key)

            return IndustryData(
                key=industry_key,
                name=getattr(industry, 'name', None),
                symbol=getattr(industry, 'symbol', None),
                sector_key=getattr(industry, 'sector_key', None),
                sector_name=getattr(industry, 'sector_name', None),
                overview=getattr(industry, 'overview', {}) or {},
                top_companies=self._df_to_list_of_dicts(getattr(industry, 'top_companies', None), transpose=False),
                top_performing_companies=self._df_to_list_of_dicts(getattr(industry, 'top_performing_companies', None), transpose=False),
                top_growth_companies=self._df_to_list_of_dicts(getattr(industry, 'top_growth_companies', None), transpose=False),
                research_reports=getattr(industry, 'research_reports', []) or [],
            )
        except Exception as e:
            logger.error(f"Error fetching industry {industry_key}: {e}")
            return IndustryData(key=industry_key)

    # ==================== SCREENER ====================

    def screen(
        self,
        query: str,
        count: int = 25,
        offset: int = 0,
        sort_field: Optional[str] = None,
        sort_asc: bool = False
    ) -> ScreenerResult:
        """
        Run a predefined stock screener.

        Available predefined queries:
        - aggressive_small_caps
        - day_gainers
        - day_losers
        - growth_technology_stocks
        - most_actives
        - most_shorted_stocks
        - small_cap_gainers
        - undervalued_growth_stocks
        - undervalued_large_caps
        - conservative_foreign_funds
        - high_yield_bond
        - portfolio_anchors
        - solid_large_growth_funds
        - solid_midcap_growth_funds
        - top_mutual_funds

        Args:
            query: Predefined query name
            count: Number of results
            offset: Result offset
            sort_field: Field to sort by
            sort_asc: Sort ascending

        Returns:
            ScreenerResult object
        """
        try:
            kwargs = {
                "count": count,
                "offset": offset,
            }
            if sort_field:
                kwargs["sortField"] = sort_field
                kwargs["sortAsc"] = sort_asc

            response = yf.screen(query, **kwargs)

            results = []
            if response and 'quotes' in response:
                results = response['quotes']

            total = response.get('total', len(results)) if response else 0

            return ScreenerResult(
                query_name=query,
                total=total,
                results=results
            )
        except Exception as e:
            logger.error(f"Error running screen {query}: {e}")
            return ScreenerResult(query_name=query)

    def screen_custom(
        self,
        filters: List[dict],
        operator: str = "and",
        count: int = 100,
        offset: int = 0,
        sort_field: str = "ticker",
        sort_asc: bool = False
    ) -> ScreenerResult:
        """
        Run a custom stock screener with filters.

        Filter format: {"operator": "gt|lt|eq|btwn|is-in", "field": "field_name", "values": [...]}

        Example filters:
        - {"operator": "gt", "field": "percentchange", "values": [3]}
        - {"operator": "eq", "field": "region", "values": ["us"]}
        - {"operator": "btwn", "field": "intradaymarketcap", "values": [2000000000, 10000000000]}
        - {"operator": "is-in", "field": "exchange", "values": ["NMS", "NYQ"]}

        Args:
            filters: List of filter dictionaries
            operator: Logical operator to combine filters ("and" or "or")
            count: Number of results
            offset: Result offset
            sort_field: Field to sort by
            sort_asc: Sort ascending

        Returns:
            ScreenerResult object
        """
        try:
            from yfinance import EquityQuery

            # Build query from filters
            queries = []
            for f in filters:
                op = f.get("operator", "eq")
                field = f.get("field")
                values = f.get("values", [])

                if field:
                    queries.append(EquityQuery(op, [field] + list(values)))

            if not queries:
                return ScreenerResult(query_name="custom")

            if len(queries) == 1:
                query = queries[0]
            else:
                query = EquityQuery(operator, queries)

            response = yf.screen(
                query,
                size=count,
                offset=offset,
                sortField=sort_field,
                sortAsc=sort_asc
            )

            results = []
            if response and 'quotes' in response:
                results = response['quotes']

            total = response.get('total', len(results)) if response else 0

            return ScreenerResult(
                query_name="custom",
                total=total,
                results=results
            )
        except Exception as e:
            logger.error(f"Error running custom screen: {e}")
            return ScreenerResult(query_name="custom")

    # ==================== BULK DOWNLOAD ====================

    def download(
        self,
        symbols: List[str],
        period: str = "1mo",
        interval: str = "1d",
        start: Optional[str] = None,
        end: Optional[str] = None,
        group_by: str = "ticker",
        auto_adjust: bool = True,
        repair: bool = False,
        threads: bool = True,
    ) -> BulkDownloadResult:
        """
        Download historical data for multiple tickers at once.

        Args:
            symbols: List of ticker symbols
            period: Data period (1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max)
            interval: Data interval (1m, 2m, 5m, 15m, 30m, 60m, 90m, 1h, 1d, 5d, 1wk, 1mo, 3mo)
            start: Start date string (YYYY-MM-DD)
            end: End date string (YYYY-MM-DD)
            group_by: Group by 'ticker' or 'column'
            auto_adjust: Adjust all OHLC automatically
            repair: Detect and repair price errors
            threads: Use multiple threads for downloading

        Returns:
            BulkDownloadResult object
        """
        try:
            tickers_str = " ".join(symbols)

            df = yf.download(
                tickers_str,
                period=period,
                interval=interval,
                start=start,
                end=end,
                group_by=group_by,
                auto_adjust=auto_adjust,
                repair=repair,
                threads=threads,
                progress=False
            )

            data = []
            if df is not None and not df.empty:
                df_reset = df.reset_index()
                # Flatten MultiIndex columns to strings
                if isinstance(df_reset.columns, pd.MultiIndex):
                    df_reset.columns = ['_'.join(map(str, col)).strip('_') for col in df_reset.columns.values]
                data = df_reset.to_dict(orient="records")

            return BulkDownloadResult(
                symbols=symbols,
                period=period,
                interval=interval,
                start=start,
                end=end,
                data=data
            )
        except Exception as e:
            logger.error(f"Error downloading data for {symbols}: {e}")
            return BulkDownloadResult(symbols=symbols, period=period, interval=interval)

    # ==================== GLOBAL INDEXES ====================

    def get_global_indexes(self) -> List[GlobalIndex]:
        """
        Get information about major global indexes.

        Returns:
            List of GlobalIndex objects
        """
        indexes_to_fetch = [
            ("^GSPC", "S&P 500", "USA"),
            ("^DJI", "Dow Jones Industrial Average", "USA"),
            ("^IXIC", "NASDAQ Composite", "USA"),
            ("^FTSE", "FTSE 100", "UK"),
            ("^GDAXI", "DAX PERFORMANCE-INDEX", "Germany"),
            ("^FCHI", "CAC 40", "France"),
            ("^N225", "Nikkei 225", "Japan"),
            ("^HSI", "HANG SENG INDEX", "Hong Kong"),
            ("000001.SS", "SSE Composite Index", "China"),
            ("^BSESN", "S&P BSE SENSEX", "India"),
            ("^NSEI", "NIFTY 50", "India"),
            ("^AXJO", "S&P/ASX 200", "Australia"),
            ("^BVSP", "IBOVESPA", "Brazil"),
        ]

        results = []
        for symbol, name, country in indexes_to_fetch:
            try:
                ticker = yf.Ticker(symbol)
                if hasattr(ticker, "fast_info"):
                    fast_info = ticker.fast_info
                    last_price = fast_info.last_price
                    prev_close = fast_info.previous_close
                else:
                    hist = ticker.history(period="1d")
                    if not hist.empty:
                        last_price = hist["Close"].iloc[-1]
                        prev_close = hist["Open"].iloc[0]
                    else:
                        last_price = None
                        prev_close = None

                change = None
                change_percent = None

                if last_price and prev_close:
                    change = last_price - prev_close
                    change_percent = (change / prev_close) * 100

                results.append(GlobalIndex(
                    symbol=symbol,
                    name=name,
                    country=country,
                    last_price=last_price,
                    change=change,
                    change_percent=change_percent,
                    market_state="Unknown"
                ))
            except Exception as e:
                logger.error(f"Error fetching data for {symbol}: {e}")
                results.append(GlobalIndex(symbol=symbol, name=name, country=country))

        return results

    # ==================== MARKDOWN REPORT ====================

    def get_ticker_markdown(self, symbol: str) -> str:
        """
        Generate a comprehensive markdown report for a ticker.

        Args:
            symbol: Ticker symbol

        Returns:
            Markdown formatted string
        """
        md = f"# Report for {symbol}\n\n"

        # 1. Info
        info = self.get_ticker_info(symbol)
        i = info.info
        md += f"## Overview\n"
        md += f"**Name:** {i.get('shortName', 'N/A')}\n"
        md += f"**Sector:** {i.get('sector', 'N/A')}\n"
        md += f"**Industry:** {i.get('industry', 'N/A')}\n"
        md += f"**Country:** {i.get('country', 'N/A')}\n"
        md += f"**Website:** {i.get('website', 'N/A')}\n\n"
        md += f"**Business Summary:**\n{i.get('longBusinessSummary', 'N/A')}\n\n"

        # 2. Market Data
        md += f"## Market Data\n"
        md += f"**Current Price:** {i.get('currentPrice', 'N/A')} {i.get('currency', '')}\n"
        md += f"**Market Cap:** {i.get('marketCap', 'N/A')}\n"
        md += f"**52 Week High:** {i.get('fiftyTwoWeekHigh', 'N/A')}\n"
        md += f"**52 Week Low:** {i.get('fiftyTwoWeekLow', 'N/A')}\n"
        md += f"**PE Ratio:** {i.get('trailingPE', 'N/A')}\n"
        md += f"**Dividend Yield:** {i.get('dividendYield', 'N/A')}\n\n"

        # 3. History (Last 5 days)
        hist = self.get_historical_data(symbol, period="5d")
        md += f"## Recent Price History (Last 5 Days)\n"
        if hist.history:
            md += "| Date | Open | High | Low | Close | Volume |\n"
            md += "|---|---|---|---|---|---|\n"
            for h in hist.history:
                date_str = h.date.strftime('%Y-%m-%d')
                md += f"| {date_str} | {h.open:.2f} | {h.high:.2f} | {h.low:.2f} | {h.close:.2f} | {h.volume} |\n"
        else:
            md += "No historical data available.\n"
        md += "\n"

        # 4. Analysis
        analysis = self.get_analysis(symbol)
        md += f"## Analyst Recommendations\n"
        target = analysis.analyst_price_targets
        if target:
             md += f"**Target Mean:** {target.get('mean', 'N/A')}\n"
             md += f"**Target High:** {target.get('high', 'N/A')}\n"
             md += f"**Target Low:** {target.get('low', 'N/A')}\n"
             md += f"**Number of Analysts:** {target.get('numberOfAnalysts', 'N/A')}\n"
        else:
            md += "No analyst targets available.\n"
        md += "\n"

        # 5. News
        news = self.get_news(symbol)
        md += f"## Latest News\n"
        if news:
            for n in news[:5]:
                # Handle nested content structure
                if 'content' in n:
                    content = n['content']
                    title = content.get('title', 'No Title')
                    link = content.get('canonicalUrl', {}).get('url', '#')
                    publisher = content.get('provider', {}).get('displayName', 'Unknown')
                    pub_date = content.get('pubDate', '')
                    md += f"- **[{title}]({link})** ({publisher}, {pub_date[:10] if pub_date else 'N/A'})\n"
                else:
                    title = n.get('title', 'No Title')
                    link = n.get('link', '#')
                    publisher = n.get('publisher', 'Unknown')
                    pub_time = n.get('providerPublishTime', 0)
                    if pub_time:
                        pub_str = datetime.fromtimestamp(pub_time).strftime('%Y-%m-%d %H:%M')
                    else:
                        pub_str = 'N/A'
                    md += f"- **[{title}]({link})** ({publisher}, {pub_str})\n"
        else:
             md += "No news available.\n"

        return md
