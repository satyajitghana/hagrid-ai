"""Agno Toolkit for Yahoo Finance market data - for agent integration."""

from typing import Optional
from agno.tools import Toolkit
from .client import YFinanceClient


class YahooFinanceToolkit(Toolkit):
    """Toolkit for Yahoo Finance market data.

    Provides tools for agents to fetch stock information, historical prices,
    financial data, analyst recommendations, and more from Yahoo Finance.
    """

    # Known NSE symbols that need .NS suffix for Yahoo Finance
    KNOWN_NSE_SYMBOLS = {
        'SBIN', 'ICICIBANK', 'HDFCBANK', 'RELIANCE', 'TCS', 'INFY',
        'ITC', 'KOTAKBANK', 'LT', 'AXISBANK', 'BHARTIARTL', 'HCLTECH',
        'WIPRO', 'BAJFINANCE', 'ASIANPAINT', 'MARUTI', 'TITAN',
        'ULTRACEMCO', 'NESTLEIND', 'SUNPHARMA', 'ONGC', 'NTPC',
        'POWERGRID', 'M&M', 'TATASTEEL', 'JSWSTEEL', 'HINDALCO',
        'ADANIGREEN', 'ADANIENT', 'ADANIPORTS', 'BAJAJ-AUTO',
        'HEROMOTOCO', 'EICHERMOT', 'DRREDDY', 'CIPLA', 'DIVISLAB',
        'APOLLOHOSP', 'SBILIFE', 'HDFCLIFE', 'BRITANNIA', 'HINDUNILVR',
        'IREDA', 'IRFC', 'YESBANK', 'PNB', 'BANKBARODA', 'CANBK',
        'INDUSINDBK', 'FEDERALBNK', 'IDFCFIRSTB', 'AUBANK', 'BANDHANBNK',
        'RBLBANK', 'TATACONSUM', 'TATAMOTORS', 'TATAPOWER', 'TATAELXSI',
        'TECHM', 'LTIM', 'MPHASIS', 'COFORGE', 'PERSISTENT', 'CYIENT',
        'ZOMATO', 'PAYTM', 'NYKAA', 'POLICYBZR', 'DELHIVERY', 'VEDL',
        'COALINDIA', 'GRASIM', 'SHREECEM', 'AMBUJACEM', 'ACC',
        'PIDILITIND', 'BERGEPAINT', 'HAVELLS', 'VOLTAS', 'SIEMENS',
        'ABB', 'CUMMINSIND', 'TORNTPHARM', 'LUPIN', 'BIOCON',
        'GODREJCP', 'DABUR', 'MARICO', 'COLPAL', 'JUBLFOOD',
        'TRENT', 'PAGEIND', 'MUTHOOTFIN', 'BAJAJFINSV', 'CHOLAFIN',
        'SBICARD', 'ICICIPRULI', 'ICICIGI', 'HDFCAMC', 'NAUKRI',
        'DMART', 'HAL', 'BEL', 'BHEL', 'RECLTD', 'PFC', 'GAIL',
        'IOC', 'BPCL', 'HINDPETRO', 'PIIND', 'UPL', 'SRF',
        'TATACOMM', 'IDEA', 'INDIGO', 'CONCOR', 'MOTHERSON',
        'BOSCHLTD', 'MRF', 'ESCORTS', 'ASHOKLEY', 'BALKRISIND',
        'BATAINDIA', 'AUROPHARMA', 'ALKEM', 'GLENMARK', 'IPCALAB',
        'LAURUSLABS', 'METROPOLIS', 'LALPATHLAB', 'MAXHEALTH',
        'FORTIS', 'OBEROIRLTY', 'DLF', 'GODREJPROP', 'PHOENIXLTD',
        'PRESTIGE', 'SOBHA', 'LODHA', 'ABCAPITAL', 'L&TFH',
        'MANAPPURAM', 'LICHSGFIN', 'CANFINHOME', 'AADHARHFC',
        'MAZDOCK', 'COCHINSHIP', 'GRSE', 'IRCON', 'RVNL', 'NBCC',
        'NMDC', 'SAIL', 'NATIONALUM', 'HINDZINC', 'MOIL',
        'GMRINFRA', 'ADANIPOWER', 'TATAPOWER', 'NHPC', 'SJVN',
        'CESC', 'TORNTPOWER', 'JSL', 'JINDALSAW', 'APOLLOTYRE',
        'CEATLTD', 'JKC', 'RAMCOCEM', 'JKCEMENT', 'DALBHARAT',
        'STARCEMENT', 'INDIACEM', 'PRISMJOHN', 'ORIENTCEM',
    }

    def __init__(self, **kwargs):
        """Initialize the Yahoo Finance toolkit."""
        self.client = YFinanceClient()

        tools = [
            # Ticker data
            self.get_stock_info,
            self.get_stock_price,
            self.get_historical_prices,
            self.get_financials,
            self.get_analyst_recommendations,
            self.get_holders_info,
            self.get_options_chain,
            self.get_dividends_splits,
            self.get_news,
            self.get_sec_filings,

            # Market data
            self.get_market_status,
            self.get_earnings_calendar,
            self.get_global_indexes,

            # Search & lookup
            self.search_tickers,
            self.lookup_symbol,

            # Sector & industry
            self.get_sector_info,
            self.get_industry_info,

            # Screener
            self.screen_stocks,

            # Bulk operations
            self.download_multiple,

            # Funds data
            self.get_fund_data,
        ]

        instructions = """Use these tools for global market data from Yahoo Finance:
- Stock info, prices, historical data, and financials
- Analyst recommendations and price targets
- Options chains (US stocks only)
- Holders information (institutional, mutual fund, insider)
- Market status, earnings calendar, global indexes
- Sector and industry analysis
- Stock screening (gainers, losers, most active, etc.)
- ETF/Mutual fund holdings and allocations

For Indian stocks, append ".NS" (NSE) or ".BO" (BSE) to the symbol.
Examples: "RELIANCE.NS", "TCS.NS", "INFY.BO"."""

        super().__init__(name="yahoo_finance", tools=tools, instructions=instructions, **kwargs)

    def _normalize_symbol(self, symbol: str) -> str:
        """
        Auto-append .NS suffix for Indian stock symbols if needed.

        - If symbol already has .NS or .BO suffix, return as-is
        - If symbol is in known NSE list, append .NS
        - Otherwise return as-is (global stocks)

        Args:
            symbol: Stock ticker symbol

        Returns:
            Normalized symbol with appropriate suffix
        """
        if not symbol:
            return symbol

        # Already has suffix
        if symbol.endswith('.NS') or symbol.endswith('.BO'):
            return symbol

        # Check if it's a known Indian symbol
        upper_symbol = symbol.upper()
        if upper_symbol in self.KNOWN_NSE_SYMBOLS:
            return f"{symbol}.NS"

        return symbol

    def _format_error(self, symbol: str, error: Exception) -> str:
        """
        Format error message with helpful hints for Indian stocks.

        If the symbol doesn't have .NS/.BO suffix and looks like it could be
        an Indian stock, suggest trying with the suffix.
        """
        error_str = str(error)
        base_msg = f"Error fetching data for {symbol}: {error_str}"

        # Check if this might be an Indian stock without suffix
        if not symbol.endswith('.NS') and not symbol.endswith('.BO'):
            # Common patterns that suggest Indian stock
            is_likely_indian = (
                '404' in error_str or
                'not found' in error_str.lower() or
                'no data' in error_str.lower()
            )
            if is_likely_indian:
                return (
                    f"{base_msg}\n\n"
                    f"**TIP:** If '{symbol}' is an Indian stock, try adding '.NS' suffix "
                    f"(e.g., '{symbol}.NS' for NSE or '{symbol}.BO' for BSE)."
                )

        return base_msg

    # ==================== TICKER DATA ====================

    def get_stock_info(self, symbol: str) -> str:
        """Get comprehensive stock information including price, valuation, and company details.

        Use this tool to get an overview of a stock including its current price,
        market cap, P/E ratio, sector, industry, and business description.

        Args:
            symbol: Stock ticker symbol (e.g., "AAPL", "MSFT", "RELIANCE.NS")

        Returns:
            Formatted stock information as markdown text
        """
        try:
            symbol = self._normalize_symbol(symbol)
            info = self.client.get_ticker_info(symbol)
            i = info.info

            if not i:
                return f"No information found for {symbol}"

            lines = [
                f"# {i.get('shortName', symbol)} ({symbol})",
                "",
                f"**Sector:** {i.get('sector', 'N/A')}",
                f"**Industry:** {i.get('industry', 'N/A')}",
                f"**Country:** {i.get('country', 'N/A')}",
                f"**Website:** {i.get('website', 'N/A')}",
                "",
                "## Price Data",
                f"**Current Price:** {i.get('currentPrice', 'N/A')} {i.get('currency', '')}",
                f"**Previous Close:** {i.get('previousClose', 'N/A')}",
                f"**Open:** {i.get('open', 'N/A')}",
                f"**Day High:** {i.get('dayHigh', 'N/A')}",
                f"**Day Low:** {i.get('dayLow', 'N/A')}",
                "",
                "## Valuation",
                f"**Market Cap:** {self._format_number(i.get('marketCap'))}",
                f"**Enterprise Value:** {self._format_number(i.get('enterpriseValue'))}",
                f"**P/E Ratio:** {i.get('trailingPE', 'N/A')}",
                f"**Forward P/E:** {i.get('forwardPE', 'N/A')}",
                f"**PEG Ratio:** {i.get('pegRatio', 'N/A')}",
                f"**Price/Book:** {i.get('priceToBook', 'N/A')}",
                "",
                "## Performance",
                f"**52W High:** {i.get('fiftyTwoWeekHigh', 'N/A')}",
                f"**52W Low:** {i.get('fiftyTwoWeekLow', 'N/A')}",
                f"**50-Day Avg:** {i.get('fiftyDayAverage', 'N/A')}",
                f"**200-Day Avg:** {i.get('twoHundredDayAverage', 'N/A')}",
                "",
                "## Dividends",
                f"**Dividend Yield:** {self._format_pct(i.get('dividendYield'))}",
                f"**Dividend Rate:** {i.get('dividendRate', 'N/A')}",
                "",
            ]

            # Add business summary (truncated)
            summary = i.get('longBusinessSummary', '')
            if summary:
                if len(summary) > 500:
                    summary = summary[:497] + "..."
                lines.append("## Business Summary")
                lines.append(summary)

            return "\n".join(lines)

        except Exception as e:
            return self._format_error(symbol, e)

    def get_stock_price(self, symbol: str) -> str:
        """Get current stock price and basic trading data (fast/lightweight).

        Use this tool for quick price lookups when you don't need full company info.

        Args:
            symbol: Stock ticker symbol (e.g., "AAPL", "MSFT", "RELIANCE.NS")

        Returns:
            Current price and basic trading data as text
        """
        try:
            symbol = self._normalize_symbol(symbol)
            fi = self.client.get_fast_info(symbol)

            lines = [
                f"# {symbol} Quick Price",
                "",
                f"**Last Price:** {fi.last_price}",
                f"**Previous Close:** {fi.previous_close}",
                f"**Open:** {fi.open}",
                f"**Day High:** {fi.day_high}",
                f"**Day Low:** {fi.day_low}",
                "",
                f"**Volume:** {self._format_number(fi.last_volume)}",
                f"**Market Cap:** {self._format_number(fi.market_cap)}",
                "",
                f"**50-Day Avg:** {fi.fifty_day_average}",
                f"**200-Day Avg:** {fi.two_hundred_day_average}",
                f"**Year High:** {fi.year_high}",
                f"**Year Low:** {fi.year_low}",
            ]

            if fi.year_change is not None:
                lines.append(f"**Year Change:** {self._format_pct(fi.year_change)}")

            return "\n".join(lines)

        except Exception as e:
            return self._format_error(symbol, e)

    def get_historical_prices(
        self,
        symbol: str,
        period: str = "1mo",
        interval: str = "1d",
        limit: int = 30
    ) -> str:
        """Get historical price data for a stock.

        Use this tool to get OHLCV price history for technical analysis or
        to see how a stock has performed over time.

        Args:
            symbol: Stock ticker symbol
            period: Data period - 1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max
            interval: Data interval - 1m, 5m, 15m, 30m, 1h, 1d, 1wk, 1mo
            limit: Maximum rows to return (default 30)

        Returns:
            CSV formatted price history
        """
        try:
            symbol = self._normalize_symbol(symbol)
            hist = self.client.get_historical_data(symbol, period=period, interval=interval)

            if not hist.history:
                return f"No historical data available for {symbol}"

            lines = [f"# {symbol} Price History ({period}, {interval})", ""]
            lines.append("| Date | Open | High | Low | Close | Volume |")
            lines.append("|------|------|------|-----|-------|--------|")

            for h in hist.history[-limit:]:
                date_str = h.date.strftime('%Y-%m-%d %H:%M') if interval in ['1m', '5m', '15m', '30m', '1h'] else h.date.strftime('%Y-%m-%d')
                lines.append(f"| {date_str} | {h.open:.2f} | {h.high:.2f} | {h.low:.2f} | {h.close:.2f} | {h.volume:,} |")

            return "\n".join(lines)

        except Exception as e:
            return self._format_error(symbol, e)

    def get_financials(self, symbol: str, statement_type: str = "income") -> str:
        """Get financial statements for a company.

        Use this tool to analyze a company's financial health including
        income statement, balance sheet, and cash flow.

        Args:
            symbol: Stock ticker symbol
            statement_type: Type of statement - "income", "balance", "cashflow", or "all"

        Returns:
            Financial statement data as markdown table
        """
        try:
            symbol = self._normalize_symbol(symbol)
            fin = self.client.get_financials(symbol)
            lines = [f"# {symbol} Financial Statements", ""]

            if statement_type in ["income", "all"]:
                lines.append("## Income Statement (Annual)")
                if fin.income_statement:
                    lines.extend(self._format_financial_table(fin.income_statement[:5]))
                else:
                    lines.append("No income statement data available.")
                lines.append("")

            if statement_type in ["balance", "all"]:
                lines.append("## Balance Sheet (Annual)")
                if fin.balance_sheet:
                    lines.extend(self._format_financial_table(fin.balance_sheet[:5]))
                else:
                    lines.append("No balance sheet data available.")
                lines.append("")

            if statement_type in ["cashflow", "all"]:
                lines.append("## Cash Flow (Annual)")
                if fin.cash_flow:
                    lines.extend(self._format_financial_table(fin.cash_flow[:5]))
                else:
                    lines.append("No cash flow data available.")
                lines.append("")

            return "\n".join(lines)

        except Exception as e:
            return self._format_error(symbol, e)

    def get_analyst_recommendations(self, symbol: str, limit: int = 10) -> str:
        """Get analyst recommendations and price targets for a stock.

        Use this tool to see what analysts think about a stock, including
        buy/sell/hold recommendations and price targets.

        Args:
            symbol: Stock ticker symbol
            limit: Maximum number of recommendations to show

        Returns:
            Analyst recommendations as markdown
        """
        try:
            symbol = self._normalize_symbol(symbol)
            analysis = self.client.get_analysis(symbol)
            lines = [f"# {symbol} Analyst Analysis", ""]

            # Price targets
            target = analysis.analyst_price_targets
            if target:
                lines.append("## Price Targets")
                lines.append(f"**Current:** {target.get('current', 'N/A')}")
                lines.append(f"**Mean Target:** {target.get('mean', 'N/A')}")
                lines.append(f"**High Target:** {target.get('high', 'N/A')}")
                lines.append(f"**Low Target:** {target.get('low', 'N/A')}")
                lines.append(f"**Number of Analysts:** {target.get('numberOfAnalysts', 'N/A')}")
                lines.append("")

            # Recommendation summary
            if analysis.recommendations_summary:
                lines.append("## Recommendation Summary")
                lines.append("| Period | Strong Buy | Buy | Hold | Sell | Strong Sell |")
                lines.append("|--------|------------|-----|------|------|-------------|")
                for rec in analysis.recommendations_summary[:3]:
                    period = rec.get('period', 'N/A')
                    sb = rec.get('strongBuy', 0)
                    b = rec.get('buy', 0)
                    h = rec.get('hold', 0)
                    s = rec.get('sell', 0)
                    ss = rec.get('strongSell', 0)
                    lines.append(f"| {period} | {sb} | {b} | {h} | {s} | {ss} |")
                lines.append("")

            # Recent recommendations
            if analysis.recommendations:
                lines.append("## Recent Recommendations")
                lines.append("| Date | Firm | To Grade | From Grade |")
                lines.append("|------|------|----------|------------|")
                for rec in analysis.recommendations[:limit]:
                    date = str(rec.get('index', rec.get('Date', 'N/A')))[:10]
                    firm = rec.get('Firm', 'N/A')
                    to_grade = rec.get('To Grade', 'N/A')
                    from_grade = rec.get('From Grade', '-')
                    lines.append(f"| {date} | {firm} | {to_grade} | {from_grade} |")
                lines.append("")

            # Earnings estimates
            if analysis.earnings_estimate:
                lines.append("## Earnings Estimates")
                for est in analysis.earnings_estimate[:4]:
                    period = est.get('Date', 'N/A')
                    avg = est.get('avg', 'N/A')
                    low = est.get('low', 'N/A')
                    high = est.get('high', 'N/A')
                    lines.append(f"**{period}:** Avg: {avg}, Low: {low}, High: {high}")
                lines.append("")

            if len(lines) <= 2:
                return f"No analyst data available for {symbol}"

            return "\n".join(lines)

        except Exception as e:
            return self._format_error(symbol, e)

    def get_holders_info(self, symbol: str) -> str:
        """Get shareholder information including institutional and insider holdings.

        Use this tool to see who owns a stock - major holders, institutions,
        mutual funds, and insider transactions.

        Args:
            symbol: Stock ticker symbol

        Returns:
            Holder information as markdown
        """
        try:
            symbol = self._normalize_symbol(symbol)
            holders = self.client.get_holders(symbol)
            lines = [f"# {symbol} Shareholders", ""]

            # Major holders
            if holders.major_holders:
                lines.append("## Major Holders")
                for h in holders.major_holders:
                    val = h.get(0, h.get('Value', 'N/A'))
                    desc = h.get(1, h.get('Breakdown', 'N/A'))
                    lines.append(f"- **{val}**: {desc}")
                lines.append("")

            # Institutional holders
            if holders.institutional_holders:
                lines.append("## Top Institutional Holders")
                lines.append("| Holder | Shares | Value | % Out |")
                lines.append("|--------|--------|-------|-------|")
                for h in holders.institutional_holders[:10]:
                    holder = h.get('Holder', 'N/A')
                    shares = self._format_number(h.get('Shares'))
                    value = self._format_number(h.get('Value'))
                    pct = h.get('% Out', 'N/A')
                    pct_str = f"{pct:.2%}" if isinstance(pct, (int, float)) else pct
                    lines.append(f"| {holder[:30]} | {shares} | {value} | {pct_str} |")
                lines.append("")

            # Mutual fund holders
            if holders.mutualfund_holders:
                lines.append("## Top Mutual Fund Holders")
                lines.append("| Holder | Shares | Value | % Out |")
                lines.append("|--------|--------|-------|-------|")
                for h in holders.mutualfund_holders[:10]:
                    holder = h.get('Holder', 'N/A')
                    shares = self._format_number(h.get('Shares'))
                    value = self._format_number(h.get('Value'))
                    pct = h.get('% Out', 'N/A')
                    pct_str = f"{pct:.2%}" if isinstance(pct, (int, float)) else pct
                    lines.append(f"| {holder[:30]} | {shares} | {value} | {pct_str} |")
                lines.append("")

            # Insider transactions
            if holders.insider_transactions:
                lines.append("## Recent Insider Transactions")
                lines.append("| Insider | Transaction | Shares | Value |")
                lines.append("|---------|-------------|--------|-------|")
                for h in holders.insider_transactions[:10]:
                    insider = h.get('Insider', h.get('Name', 'N/A'))
                    trans = h.get('Transaction', h.get('Text', 'N/A'))
                    shares = h.get('Shares', 'N/A')
                    value = h.get('Value', 'N/A')
                    lines.append(f"| {str(insider)[:20]} | {trans} | {shares} | {value} |")
                lines.append("")

            if len(lines) <= 2:
                return f"No holder data available for {symbol}"

            return "\n".join(lines)

        except Exception as e:
            return self._format_error(symbol, e)

    def get_options_chain(self, symbol: str, expiration: Optional[str] = None) -> str:
        """Get options chain data for a stock.

        Use this tool to see available options (calls and puts) for a stock,
        including strike prices, premiums, volume, and open interest.

        Note: Options data is only available for US stocks.

        Args:
            symbol: Stock ticker symbol
            expiration: Specific expiration date (optional, uses nearest by default)

        Returns:
            Options chain data as markdown
        """
        try:
            symbol = self._normalize_symbol(symbol)
            options = self.client.get_options(symbol, expiration=expiration)

            if not options.expiration_dates:
                return f"No options data available for {symbol}. Options may not be available for this ticker."

            lines = [f"# {symbol} Options Chain", ""]
            lines.append(f"**Expiration Dates:** {', '.join(options.expiration_dates[:5])}...")
            lines.append("")

            # Calls
            if options.calls:
                lines.append("## Calls (Top 15)")
                lines.append("| Strike | Last | Bid | Ask | Volume | OI | IV |")
                lines.append("|--------|------|-----|-----|--------|----|----|")
                for c in options.calls[:15]:
                    strike = c.get('strike', 'N/A')
                    last = c.get('lastPrice', 'N/A')
                    bid = c.get('bid', 'N/A')
                    ask = c.get('ask', 'N/A')
                    vol = c.get('volume', 'N/A')
                    oi = c.get('openInterest', 'N/A')
                    iv = c.get('impliedVolatility', 0)
                    iv_str = f"{iv:.2%}" if isinstance(iv, (int, float)) else 'N/A'
                    lines.append(f"| {strike} | {last} | {bid} | {ask} | {vol} | {oi} | {iv_str} |")
                lines.append("")

            # Puts
            if options.puts:
                lines.append("## Puts (Top 15)")
                lines.append("| Strike | Last | Bid | Ask | Volume | OI | IV |")
                lines.append("|--------|------|-----|-----|--------|----|----|")
                for p in options.puts[:15]:
                    strike = p.get('strike', 'N/A')
                    last = p.get('lastPrice', 'N/A')
                    bid = p.get('bid', 'N/A')
                    ask = p.get('ask', 'N/A')
                    vol = p.get('volume', 'N/A')
                    oi = p.get('openInterest', 'N/A')
                    iv = p.get('impliedVolatility', 0)
                    iv_str = f"{iv:.2%}" if isinstance(iv, (int, float)) else 'N/A'
                    lines.append(f"| {strike} | {last} | {bid} | {ask} | {vol} | {oi} | {iv_str} |")
                lines.append("")

            return "\n".join(lines)

        except Exception as e:
            return self._format_error(symbol, e)

    def get_dividends_splits(self, symbol: str, limit: int = 15) -> str:
        """Get dividend history and stock split history for a stock.

        Use this tool to see a stock's dividend payment history and any
        stock splits that have occurred.

        Args:
            symbol: Stock ticker symbol
            limit: Maximum number of entries to show per category

        Returns:
            Dividend and split history as markdown
        """
        try:
            symbol = self._normalize_symbol(symbol)
            divs = self.client.get_dividends(symbol)
            splits = self.client.get_splits(symbol)

            lines = [f"# {symbol} Corporate Actions", ""]

            # Dividends
            lines.append("## Dividend History")
            if divs.dividends:
                lines.append(f"Total dividend payments: {len(divs.dividends)}")
                lines.append("")
                lines.append("| Date | Dividend |")
                lines.append("|------|----------|")
                for d in divs.dividends[-limit:]:
                    date_str = d.date.strftime('%Y-%m-%d')
                    lines.append(f"| {date_str} | ${d.dividend:.4f} |")

                # Calculate annual totals
                annual = {}
                for d in divs.dividends:
                    year = d.date.year
                    annual[year] = annual.get(year, 0) + d.dividend
                lines.append("")
                lines.append("### Annual Totals")
                for year in sorted(annual.keys(), reverse=True)[:5]:
                    lines.append(f"- **{year}:** ${annual[year]:.4f}")
            else:
                lines.append("No dividend history available.")
            lines.append("")

            # Splits
            lines.append("## Stock Split History")
            if splits.splits:
                lines.append("| Date | Split Ratio |")
                lines.append("|------|-------------|")
                for s in splits.splits[-limit:]:
                    date_str = s.date.strftime('%Y-%m-%d')
                    ratio = s.split_ratio
                    if ratio >= 1:
                        ratio_str = f"{int(ratio)}:1"
                    else:
                        ratio_str = f"1:{int(1/ratio)}"
                    lines.append(f"| {date_str} | {ratio_str} |")
            else:
                lines.append("No stock splits recorded.")

            return "\n".join(lines)

        except Exception as e:
            return self._format_error(symbol, e)

    def get_news(self, symbol: str, limit: int = 10) -> str:
        """Get latest news for a stock.

        Use this tool to fetch recent news articles related to a stock.

        Args:
            symbol: Stock ticker symbol
            limit: Maximum number of news articles to return

        Returns:
            News articles as markdown
        """
        try:
            symbol = self._normalize_symbol(symbol)
            news = self.client.get_news(symbol)

            if not news:
                return f"No news available for {symbol}"

            lines = [f"# {symbol} Latest News", ""]

            for n in news[:limit]:
                # Handle nested content structure
                if 'content' in n:
                    content = n['content']
                    title = content.get('title', 'No Title')
                    link = content.get('canonicalUrl', {}).get('url', '#')
                    publisher = content.get('provider', {}).get('displayName', 'Unknown')
                    pub_date = content.get('pubDate', '')[:10] if content.get('pubDate') else 'N/A'
                    summary = content.get('summary', '')
                else:
                    title = n.get('title', 'No Title')
                    link = n.get('link', '#')
                    publisher = n.get('publisher', 'Unknown')
                    pub_date = 'N/A'
                    summary = ''

                lines.append(f"### [{title}]({link})")
                lines.append(f"*{publisher} - {pub_date}*")
                if summary:
                    if len(summary) > 200:
                        summary = summary[:197] + "..."
                    lines.append(f"\n{summary}")
                lines.append("")

            return "\n".join(lines)

        except Exception as e:
            return self._format_error(symbol, e)

    def get_sec_filings(self, symbol: str, limit: int = 15) -> str:
        """Get SEC filings for a US stock.

        Use this tool to fetch SEC filings (10-K, 10-Q, 8-K, etc.) for US stocks.

        Note: SEC filings are only available for US stocks.

        Args:
            symbol: Stock ticker symbol
            limit: Maximum number of filings to return

        Returns:
            SEC filings as markdown
        """
        try:
            symbol = self._normalize_symbol(symbol)
            filings = self.client.get_sec_filings(symbol)

            if not filings.filings:
                return f"No SEC filings available for {symbol}. SEC filings are only available for US stocks."

            lines = [f"# {symbol} SEC Filings", ""]
            lines.append(f"Total filings: {len(filings.filings)}")
            lines.append("")
            lines.append("| Date | Type | Title |")
            lines.append("|------|------|-------|")

            for f in filings.filings[:limit]:
                date_str = f.date.strftime('%Y-%m-%d') if f.date else "N/A"
                ftype = f.type or "N/A"
                title = f.title[:50] + "..." if f.title and len(f.title) > 50 else (f.title or "N/A")
                lines.append(f"| {date_str} | {ftype} | {title} |")

            return "\n".join(lines)

        except Exception as e:
            return self._format_error(symbol, e)

    # ==================== MARKET DATA ====================

    def get_market_status(self, market: str = "US") -> str:
        """Get market status for a region.

        Use this tool to check if markets are open/closed in different regions.

        Args:
            market: Market code - US, GB, ASIA, EUROPE, RATES, COMMODITIES, CURRENCIES, CRYPTOCURRENCIES

        Returns:
            Market status information as text
        """
        try:
            ms = self.client.get_market_status(market)

            lines = [f"# {market} Market Status", ""]

            if ms.status:
                lines.append("## Status")
                for key, value in ms.status.items():
                    lines.append(f"**{key}:** {value}")
                lines.append("")

            if ms.summary:
                lines.append("## Summary")
                for key, value in list(ms.summary.items())[:10]:
                    if isinstance(value, dict):
                        lines.append(f"**{key}:**")
                        for k, v in list(value.items())[:5]:
                            lines.append(f"  - {k}: {v}")
                    else:
                        lines.append(f"**{key}:** {value}")

            if len(lines) <= 2:
                return f"No market status data available for {market}"

            return "\n".join(lines)

        except Exception as e:
            return f"Error fetching market status for {market}: {str(e)}"

    def get_earnings_calendar(self, days: int = 7) -> str:
        """Get upcoming earnings announcements.

        Use this tool to see which companies are reporting earnings soon.

        Args:
            days: Number of days to look ahead (default 7)

        Returns:
            Earnings calendar as markdown table
        """
        try:
            from datetime import datetime, timedelta
            start = datetime.now()
            end = start + timedelta(days=days)

            cal = self.client.get_calendars(start=start, end=end)

            lines = [f"# Earnings Calendar (Next {days} Days)", ""]

            if not cal.earnings:
                return "No upcoming earnings announcements found."

            lines.append("| Date | Symbol | Company | EPS Estimate |")
            lines.append("|------|--------|---------|--------------|")

            for event in cal.earnings[:30]:
                date = event.get('startdatetime', 'N/A')
                if date and date != 'N/A':
                    try:
                        dt = datetime.fromisoformat(date.replace('Z', '+00:00'))
                        date_str = dt.strftime('%Y-%m-%d')
                    except:
                        date_str = str(date)[:10]
                else:
                    date_str = 'N/A'

                sym = event.get('ticker', 'N/A')
                company = event.get('companyshortname', 'N/A')[:25]
                eps = event.get('epsestimate', 'N/A')
                eps_str = f"${eps:.2f}" if isinstance(eps, (int, float)) else 'N/A'
                lines.append(f"| {date_str} | {sym} | {company} | {eps_str} |")

            return "\n".join(lines)

        except Exception as e:
            return f"Error fetching earnings calendar: {str(e)}"

    def get_global_indexes(self) -> str:
        """Get current prices for major global stock market indexes.

        Use this tool to get an overview of how major world markets are performing.

        Returns:
            Global index prices as markdown table
        """
        try:
            indexes = self.client.get_global_indexes()

            lines = ["# Global Market Indexes", ""]
            lines.append("| Index | Country | Price | Change | Change % |")
            lines.append("|-------|---------|-------|--------|----------|")

            for idx in indexes:
                price = f"{idx.last_price:,.2f}" if idx.last_price else "N/A"
                change = f"{idx.change:+,.2f}" if idx.change else "N/A"
                change_pct = f"{idx.change_percent:+.2f}%" if idx.change_percent else "N/A"
                lines.append(f"| {idx.name[:25]} | {idx.country} | {price} | {change} | {change_pct} |")

            return "\n".join(lines)

        except Exception as e:
            return f"Error fetching global indexes: {str(e)}"

    # ==================== SEARCH & LOOKUP ====================

    def search_tickers(self, query: str, max_results: int = 10) -> str:
        """Search for stock tickers by company name or keyword.

        Use this tool to find ticker symbols when you know the company name
        but not the exact ticker symbol.

        Args:
            query: Search query (company name or keyword)
            max_results: Maximum number of results

        Returns:
            Search results as markdown
        """
        try:
            results = self.client.search(query, max_results=max_results)

            if not results.quotes:
                return f"No results found for '{query}'"

            lines = [f"# Search Results for '{query}'", ""]
            lines.append("| Symbol | Name | Type | Exchange |")
            lines.append("|--------|------|------|----------|")

            for q in results.quotes:
                sym = q.get('symbol', 'N/A')
                name = q.get('shortname', q.get('longname', 'N/A'))[:30]
                qtype = q.get('quoteType', q.get('typeDisp', 'N/A'))
                exchange = q.get('exchange', 'N/A')
                lines.append(f"| {sym} | {name} | {qtype} | {exchange} |")

            return "\n".join(lines)

        except Exception as e:
            return f"Error searching for '{query}': {str(e)}"

    def lookup_symbol(self, query: str, security_type: str = "all") -> str:
        """Lookup symbols by type (stocks, ETFs, mutual funds, etc.).

        Use this tool for more targeted symbol lookup when you know what
        type of security you're looking for.

        Args:
            query: Lookup query
            security_type: Type of security - "all", "stocks", "etfs", "mutual_funds", "indices", "crypto", "currencies"

        Returns:
            Lookup results as markdown
        """
        try:
            results = self.client.lookup(query, count=10)
            lines = [f"# Lookup Results for '{query}'", ""]

            type_map = {
                "all": "all",
                "stocks": "stocks",
                "etfs": "etfs",
                "mutual_funds": "mutual_funds",
                "indices": "indices",
                "crypto": "cryptocurrencies",
                "currencies": "currencies",
            }

            attr = type_map.get(security_type, "all")
            items = getattr(results, attr, [])

            if not items:
                return f"No {security_type} found for '{query}'"

            lines.append(f"## {security_type.title().replace('_', ' ')}")
            lines.append("| Symbol | Name |")
            lines.append("|--------|------|")

            for item in items[:15]:
                sym = item.get('symbol', 'N/A')
                name = item.get('shortName', item.get('name', 'N/A'))[:35]
                lines.append(f"| {sym} | {name} |")

            return "\n".join(lines)

        except Exception as e:
            return f"Error looking up '{query}': {str(e)}"

    # ==================== SECTOR & INDUSTRY ====================

    def get_sector_info(self, sector_key: str) -> str:
        """Get information about a market sector including top companies.

        Use this tool to explore a market sector and see its top performing companies.

        Args:
            sector_key: Sector identifier - technology, healthcare, financial-services,
                       consumer-cyclical, industrials, energy, utilities, real-estate,
                       basic-materials, communication-services, consumer-defensive

        Returns:
            Sector information as markdown
        """
        try:
            sector = self.client.get_sector(sector_key)
            lines = [f"# {sector.name or sector_key} Sector", ""]

            if sector.overview:
                lines.append("## Overview")
                for key, value in list(sector.overview.items())[:8]:
                    lines.append(f"**{key}:** {value}")
                lines.append("")

            if sector.top_companies:
                lines.append("## Top Companies")
                lines.append("| Symbol | Name | Market Cap |")
                lines.append("|--------|------|------------|")
                for c in sector.top_companies[:15]:
                    sym = c.get('symbol', 'N/A')
                    name = c.get('shortName', c.get('name', 'N/A'))[:25]
                    mcap = self._format_number(c.get('marketCap'))
                    lines.append(f"| {sym} | {name} | {mcap} |")
                lines.append("")

            if sector.industries:
                lines.append("## Industries in this Sector")
                for ind in sector.industries[:15]:
                    key = ind.get('key', ind.get('industryKey', 'N/A'))
                    name = ind.get('name', ind.get('industryName', key))
                    lines.append(f"- {name} ({key})")

            return "\n".join(lines)

        except Exception as e:
            return f"Error fetching sector {sector_key}: {str(e)}"

    def get_industry_info(self, industry_key: str) -> str:
        """Get information about an industry including top companies.

        Use this tool to explore an industry and see its top performers.

        Args:
            industry_key: Industry identifier (e.g., "software-infrastructure", "semiconductors")

        Returns:
            Industry information as markdown
        """
        try:
            industry = self.client.get_industry(industry_key)
            lines = [f"# {industry.name or industry_key} Industry", ""]

            if industry.sector_name:
                lines.append(f"**Sector:** {industry.sector_name}")
                lines.append("")

            if industry.overview:
                lines.append("## Overview")
                for key, value in list(industry.overview.items())[:8]:
                    lines.append(f"**{key}:** {value}")
                lines.append("")

            if industry.top_companies:
                lines.append("## Top Companies")
                lines.append("| Symbol | Name | Price |")
                lines.append("|--------|------|-------|")
                for c in industry.top_companies[:15]:
                    sym = c.get('symbol', 'N/A')
                    name = c.get('shortName', c.get('name', 'N/A'))[:25]
                    price = c.get('regularMarketPrice', 'N/A')
                    price_str = f"${price:.2f}" if isinstance(price, (int, float)) else 'N/A'
                    lines.append(f"| {sym} | {name} | {price_str} |")
                lines.append("")

            if industry.top_growth_companies:
                lines.append("## Top Growth Companies")
                for c in industry.top_growth_companies[:5]:
                    sym = c.get('symbol', 'N/A')
                    name = c.get('shortName', 'N/A')[:25]
                    lines.append(f"- {sym}: {name}")

            return "\n".join(lines)

        except Exception as e:
            return f"Error fetching industry {industry_key}: {str(e)}"

    # ==================== SCREENER ====================

    def screen_stocks(self, screen_type: str = "day_gainers", limit: int = 20) -> str:
        """Screen stocks using predefined filters.

        Use this tool to find stocks matching specific criteria like day gainers,
        most active, undervalued stocks, etc.

        Args:
            screen_type: Predefined screen type:
                - day_gainers: Top gaining stocks today
                - day_losers: Top losing stocks today
                - most_actives: Most actively traded
                - undervalued_large_caps: Undervalued large cap stocks
                - undervalued_growth_stocks: Undervalued growth stocks
                - growth_technology_stocks: Growth tech stocks
                - aggressive_small_caps: Aggressive small cap stocks
                - small_cap_gainers: Small cap gainers
                - most_shorted_stocks: Most shorted stocks
            limit: Maximum number of results

        Returns:
            Screener results as markdown table
        """
        try:
            results = self.client.screen(screen_type, count=limit)

            if not results.results:
                return f"No results found for screen '{screen_type}'"

            lines = [f"# Stock Screen: {screen_type.replace('_', ' ').title()}", ""]
            lines.append(f"Total matches: {results.total}")
            lines.append("")
            lines.append("| Symbol | Name | Price | Change | Volume |")
            lines.append("|--------|------|-------|--------|--------|")

            for s in results.results[:limit]:
                sym = s.get('symbol', 'N/A')
                name = s.get('shortName', s.get('longName', 'N/A'))[:20]
                price = s.get('regularMarketPrice', 0)
                change = s.get('regularMarketChangePercent', 0)
                volume = s.get('regularMarketVolume', 0)

                price_str = f"${price:.2f}" if price else "N/A"
                change_str = f"{change:+.2f}%" if isinstance(change, (int, float)) else "N/A"
                vol_str = self._format_number(volume)

                lines.append(f"| {sym} | {name} | {price_str} | {change_str} | {vol_str} |")

            return "\n".join(lines)

        except Exception as e:
            return f"Error running screen '{screen_type}': {str(e)}"

    # ==================== BULK OPERATIONS ====================

    def download_multiple(
        self,
        symbols: str,
        period: str = "1mo",
        interval: str = "1d"
    ) -> str:
        """Download historical data for multiple tickers at once.

        Use this tool when you need to compare prices across multiple stocks.

        Args:
            symbols: Comma-separated list of ticker symbols (e.g., "AAPL,MSFT,GOOGL")
            period: Data period - 1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max
            interval: Data interval - 1d, 1wk, 1mo

        Returns:
            Latest prices comparison as markdown
        """
        try:
            symbol_list = [s.strip() for s in symbols.split(",")]
            result = self.client.download(symbol_list, period=period, interval=interval)

            if not result.data:
                return f"No data downloaded for {symbols}"

            lines = [f"# Multi-Stock Data ({period}, {interval})", ""]
            lines.append(f"**Symbols:** {', '.join(result.symbols)}")
            lines.append(f"**Data points:** {len(result.data)}")
            lines.append("")

            # Show latest prices
            if result.data:
                last_row = result.data[-1]
                lines.append("## Latest Prices")
                lines.append("| Symbol | Close |")
                lines.append("|--------|-------|")

                for sym in symbol_list:
                    close_col = f"{sym}_Close"
                    close = last_row.get(close_col)
                    if close:
                        lines.append(f"| {sym} | ${close:.2f} |")
                    else:
                        lines.append(f"| {sym} | N/A |")

            return "\n".join(lines)

        except Exception as e:
            return f"Error downloading data: {str(e)}"

    # ==================== FUNDS DATA ====================

    def get_fund_data(self, symbol: str) -> str:
        """Get ETF or Mutual Fund specific data including holdings and allocations.

        Use this tool to analyze ETFs or mutual funds, seeing their top holdings,
        sector weightings, and fund operations.

        Args:
            symbol: ETF or Mutual Fund symbol (e.g., "SPY", "QQQ", "VFIAX")

        Returns:
            Fund data as markdown
        """
        try:
            symbol = self._normalize_symbol(symbol)
            fd = self.client.get_funds_data(symbol)
            lines = [f"# {symbol} Fund Data", ""]

            if fd.description:
                lines.append("## Description")
                desc = fd.description[:300] + "..." if len(fd.description) > 300 else fd.description
                lines.append(desc)
                lines.append("")

            if fd.top_holdings:
                lines.append("## Top Holdings")
                lines.append("| Symbol | Name | Weight |")
                lines.append("|--------|------|--------|")
                for h in fd.top_holdings[:15]:
                    sym = h.get('symbol', 'N/A')
                    name = h.get('holdingName', 'N/A')[:25]
                    weight = h.get('holdingPercent', 0)
                    weight_str = f"{weight:.2%}" if weight else "N/A"
                    lines.append(f"| {sym} | {name} | {weight_str} |")
                lines.append("")

            if fd.sector_weightings:
                lines.append("## Sector Weightings")
                if isinstance(fd.sector_weightings, dict):
                    for sector, weight in fd.sector_weightings.items():
                        if isinstance(weight, (int, float)):
                            lines.append(f"- **{sector}:** {weight:.2%}")
                lines.append("")

            if fd.fund_operations:
                lines.append("## Fund Operations")
                for key, value in list(fd.fund_operations.items())[:5]:
                    if 'ratio' in key.lower() or 'fee' in key.lower():
                        if isinstance(value, (int, float)):
                            lines.append(f"**{key}:** {value:.4%}")
                        else:
                            lines.append(f"**{key}:** {value}")
                    else:
                        lines.append(f"**{key}:** {value}")

            if len(lines) <= 2:
                return f"No fund data available for {symbol}. This may not be an ETF or mutual fund."

            return "\n".join(lines)

        except Exception as e:
            return self._format_error(symbol, e)

    # ==================== HELPERS ====================

    def _format_number(self, value) -> str:
        """Format large numbers with appropriate suffixes."""
        if value is None:
            return "N/A"
        try:
            num = float(value)
            if num >= 1e12:
                return f"${num/1e12:.2f}T"
            elif num >= 1e9:
                return f"${num/1e9:.2f}B"
            elif num >= 1e6:
                return f"${num/1e6:.2f}M"
            elif num >= 1000:
                return f"{num:,.0f}"
            else:
                return f"{num:.2f}"
        except (ValueError, TypeError):
            return str(value) if value else "N/A"

    def _format_pct(self, value) -> str:
        """Format percentage values."""
        if value is None:
            return "N/A"
        try:
            return f"{float(value):.2%}"
        except (ValueError, TypeError):
            return str(value) if value else "N/A"

    def _format_financial_table(self, data: list) -> list:
        """Format financial data as markdown table rows."""
        if not data:
            return ["No data available."]

        lines = []
        # Get column headers (dates)
        if data:
            cols = [k for k in data[0].keys() if k != 'Date'][:4]
            header = "| Item |" + " | ".join(str(c)[:10] for c in cols) + " |"
            separator = "|------|" + "|".join("-" * 12 for _ in cols) + "|"
            lines.append(header)
            lines.append(separator)

            for row in data[:20]:  # Limit rows
                item = row.get('Date', 'N/A')
                if isinstance(item, str) and len(item) > 30:
                    item = item[:27] + "..."
                values = [self._format_number(row.get(c)) for c in cols]
                lines.append(f"| {item} | " + " | ".join(values) + " |")

        return lines
