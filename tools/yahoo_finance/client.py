"""Yahoo Finance API Client."""

import logging
from typing import Any, List, Optional
from datetime import datetime
import pandas as pd

import yfinance as yf
from .models.ticker import (
    TickerInfo, TickerHistory, TickerFinancials, PriceHistoryEntry,
    TickerHolders, TickerAnalysis, TickerCalendar, TickerOptions, TickerSustainability
)
from .models.market import GlobalIndex

logger = logging.getLogger(__name__)

class YFinanceClient:
    """
    Client for interacting with Yahoo Finance via yfinance library.
    """

    def __init__(self) -> None:
        """
        Initialize the YFinance client.
        """
        pass
    
    def _df_to_list_of_dicts(self, df: pd.DataFrame, transpose: bool = True) -> List[dict]:
        """Helper to convert DataFrame to list of dicts."""
        if df is None or df.empty:
            return []
        
        try:
            if transpose:
                # Transpose so dates/columns become rows
                df_T = df.T
                df_T.index.name = "Date" if df_T.index.name is None else df_T.index.name
                df_T = df_T.reset_index()
                # Convert timestamps to strings for better serialization
                if 'Date' in df_T.columns:
                    df_T['Date'] = df_T['Date'].astype(str)
                return df_T.to_dict(orient="records")
            else:
                # Keep original structure, just reset index to include it
                df_reset = df.reset_index()
                return df_reset.to_dict(orient="records")
        except Exception as e:
            logger.error(f"Error converting DataFrame: {e}")
            return []

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

    def get_historical_data(
        self,
        symbol: str,
        period: str = "1mo",
        interval: str = "1d",
        start: Optional[str] = None,
        end: Optional[str] = None,
    ) -> TickerHistory:
        """
        Get historical market data.

        Args:
            symbol: Ticker symbol
            period: Data period (e.g., "1d", "1mo", "1y", "max")
            interval: Data interval (e.g., "1m", "1h", "1d", "1wk")
            start: Start date string (YYYY-MM-DD)
            end: End date string (YYYY-MM-DD)

        Returns:
            TickerHistory object
        """
        try:
            ticker = yf.Ticker(symbol)
            
            # history() returns a pandas DataFrame
            hist_df = ticker.history(period=period, interval=interval, start=start, end=end)
            
            history_entries = []
            for index, row in hist_df.iterrows():
                # index is DatetimeIndex
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

    def get_financials(self, symbol: str) -> TickerFinancials:
        """
        Get financial statements (income statement, balance sheet, cash flow).

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
            )
        except Exception as e:
            logger.error(f"Error fetching financials for {symbol}: {e}")
            return TickerFinancials(symbol=symbol)

    def get_holders(self, symbol: str) -> TickerHolders:
        """Get major, institutional, and mutual fund holders."""
        try:
            ticker = yf.Ticker(symbol)
            return TickerHolders(
                symbol=symbol,
                major_holders=self._df_to_list_of_dicts(ticker.major_holders, transpose=False),
                institutional_holders=self._df_to_list_of_dicts(ticker.institutional_holders, transpose=False),
                mutualfund_holders=self._df_to_list_of_dicts(ticker.mutualfund_holders, transpose=False),
                insider_roster_holders=self._df_to_list_of_dicts(ticker.insider_roster_holders, transpose=False),
            )
        except Exception as e:
            logger.error(f"Error fetching holders for {symbol}: {e}")
            return TickerHolders(symbol=symbol)

    def get_analysis(self, symbol: str) -> TickerAnalysis:
        """Get analysis data including recommendations and estimates."""
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

    def get_calendar(self, symbol: str) -> TickerCalendar:
        """Get calendar events."""
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
            
    def get_options(self, symbol: str) -> TickerOptions:
        """Get options chain summary."""
        try:
            ticker = yf.Ticker(symbol)
            exp_dates = ticker.options
            
            calls = []
            puts = []
            
            if exp_dates:
                # Fetch chain for nearest expiration
                chain = ticker.option_chain(exp_dates[0])
                calls = self._df_to_list_of_dicts(chain.calls, transpose=False)
                puts = self._df_to_list_of_dicts(chain.puts, transpose=False)
                
            return TickerOptions(
                symbol=symbol,
                expiration_dates=list(exp_dates),
                calls=calls,
                puts=puts
            )
        except Exception as e:
            logger.error(f"Error fetching options for {symbol}: {e}")
            return TickerOptions(symbol=symbol)

    def get_sustainability(self, symbol: str) -> TickerSustainability:
        """Get sustainability scores."""
        try:
            ticker = yf.Ticker(symbol)
            sus = ticker.sustainability
            sus_dict = {}
            if sus is not None and not sus.empty:
                sus_dict = sus.to_dict(orient="index")
                # Flatten structure if needed, but dict of dicts is fine for generic holder
                # Usually it's index=Value, col=Value
                sus_dict = sus.to_dict()[list(sus.columns)[0]]
                
            return TickerSustainability(
                symbol=symbol,
                sustainability=sus_dict
            )
        except Exception as e:
            logger.error(f"Error fetching sustainability for {symbol}: {e}")
            return TickerSustainability(symbol=symbol)

    def get_global_indexes(self) -> List[GlobalIndex]:
        """
        Get information about major global indexes.
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
                # Use fast_info for basic price data if available (newer yfinance versions)
                if hasattr(ticker, "fast_info"):
                    fast_info = ticker.fast_info
                    last_price = fast_info.last_price
                    prev_close = fast_info.previous_close
                else:
                    # Fallback to history for older versions or if fast_info fails
                    hist = ticker.history(period="1d")
                    if not hist.empty:
                        last_price = hist["Close"].iloc[-1]
                        prev_close = hist["Open"].iloc[0] # Approx
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

    def get_ticker_markdown(self, symbol: str) -> str:
        """
        Generate a comprehensive markdown report for a ticker.
        Includes info, price, financials, holders, and analysis.
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

        # 4. Financials (Income Statement - Latest 2)
        fin = self.get_financials(symbol)
        md += f"## Financials (Income Statement - Latest)\n"
        if fin.income_statement:
            md += "| Metric | " + " | ".join([list(x.values())[0] for x in fin.income_statement[:2]]) + " |\n" # Headers (Dates) are tricky here because of dict structure
            # A better way is to iterate keys
            # Let's simplify: just print the raw first entry to show structure or key metrics
            # But since structure is list of dicts where each dict is a period...
            # We need to transpose back mentally to display table
            
            # Let's grab first 2 periods
            periods = fin.income_statement[:2]
            if periods:
                 # Get all keys (metrics) from the first period, excluding 'Date'
                metrics = [k for k in periods[0].keys() if k != 'Date']
                md += "| Metric | " + " | ".join([p.get('Date', 'N/A') for p in periods]) + " |\n"
                md += "|---|---|---|\n"
                for m in metrics:
                    vals = [str(p.get(m, 'N/A')) for p in periods]
                    md += f"| {m} | {' | '.join(vals)} |\n"
        else:
            md += "No financial data available.\n"
        md += "\n"

        # 5. Analysis
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
        
        # 6. News
        news = self.get_news(symbol)
        md += f"## Latest News\n"
        if news:
            for n in news[:5]: # Top 5 news
                title = n.get('title', 'No Title')
                link = n.get('link', '#')
                publisher = n.get('publisher', 'Unknown')
                pub_time = datetime.fromtimestamp(n.get('providerPublishTime', 0)).strftime('%Y-%m-%d %H:%M')
                md += f"- **[{title}]({link})** ({publisher}, {pub_time})\n"
        else:
             md += "No news available.\n"
             
        return md

    def get_news(self, symbol: str) -> List[dict]:
        """
        Get news for a ticker.
        """
        try:
            ticker = yf.Ticker(symbol)
            return ticker.news
        except Exception as e:
            logger.error(f"Error fetching news for {symbol}: {e}")
            return []
