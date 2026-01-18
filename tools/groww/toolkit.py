"""Agno Toolkit for Groww market data - for agent integration."""

from typing import Any

from agno.tools import Toolkit

from .client import GrowwClient


class GrowwToolkit(Toolkit):
    """Toolkit for Groww market data.

    Provides tools for agents to fetch market data from Groww including:
    - Stock search
    - Options chain data with greeks
    - Live OHLC prices
    - Company details and fundamentals
    - Market movers (top gainers/losers)
    - Global and Indian indices
    """

    def __init__(self, timeout: float = 30.0, **kwargs):
        """Initialize the Groww toolkit.

        Args:
            timeout: Request timeout in seconds
        """
        self.client = GrowwClient(timeout=timeout)

        tools = [
            self.search_stocks,
            self.get_option_chain,
            self.get_stock_price,
            self.get_stock_details,
            self.get_market_movers,
            self.get_global_indices,
            self.get_indian_indices,
        ]

        instructions = """Use these tools to fetch market data from Groww:
- Search for stocks by name or symbol
- Get options chain data with greeks (IV, delta, gamma, theta, vega) and OI
- Get live OHLC prices for any NSE/BSE listed stock
- Get company details including fundamentals, financials, and shareholding
- Get market movers (top gainers, losers, popular stocks)
- Get global indices (SGX Nifty, Dow, S&P 500, etc.)
- Get Indian indices (NIFTY 50, Bank Nifty, sectoral indices)

For options data, supported indices: NIFTY, BANKNIFTY, FINNIFTY, MIDCPNIFTY
For stocks, use the search_id from search results (e.g., "reliance-industries-ltd")

Symbol format:
- For options: Use index name (NIFTY, BANKNIFTY) or search_id for stocks
- For live price: Use NSE scrip code (RELIANCE, TCS, INFY)
- For company details: Use search_id (reliance-industries-ltd)"""

        super().__init__(name="groww", tools=tools, instructions=instructions, **kwargs)

    def search_stocks(self, query: str, size: int = 6) -> str:
        """Search for stocks by name or symbol.

        Use this tool to find stocks before fetching their details or options data.
        Returns matching stocks with their search_id (needed for other tools).

        Args:
            query: Search query (stock name or symbol, e.g., "reliance", "tcs", "ireda")
            size: Number of results to return (default: 6)

        Returns:
            Markdown formatted search results with search_id, symbol, and NSE code
        """
        try:
            results = self.client.search(query, size=size)

            if not results:
                return f"No results found for '{query}'"

            lines = [f"# Search Results for \"{query}\"", ""]
            lines.append("| Search ID | Name | NSE Code | Type |")
            lines.append("|-----------|------|----------|------|")

            for r in results:
                search_id = r.get("search_id", "-")
                title = r.get("title", "-")
                nse_code = r.get("nse_scrip_code") or "-"
                entity_type = r.get("entity_type", "-")

                # Truncate long names
                if len(title) > 40:
                    title = title[:37] + "..."

                lines.append(f"| {search_id} | {title} | {nse_code} | {entity_type} |")

            lines.append("")
            lines.append("*Use `search_id` for get_stock_details() and get_option_chain()*")
            lines.append("*Use `NSE Code` for get_stock_price()*")

            return "\n".join(lines)

        except Exception as e:
            return f"Error searching for '{query}': {str(e)}"

    def get_option_chain(
        self,
        symbol: str,
        expiry_date: str | None = None,
        strikes_around_atm: int = 10,
    ) -> str:
        """Get options chain data with greeks for a symbol.

        Use this tool to fetch options chain with:
        - Strike prices with CE/PE data
        - Greeks (IV, Delta, Gamma, Theta, Vega)
        - Open Interest and Volume
        - Put-Call Ratio (PCR)
        - Max OI strikes (potential support/resistance)

        Args:
            symbol: Index name (NIFTY, BANKNIFTY, FINNIFTY) or stock search_id
                   (e.g., "reliance-industries-ltd" from search results)
            expiry_date: Expiry date in YYYY-MM-DD format (optional, defaults to nearest)
            strikes_around_atm: Number of strikes to show around ATM (default: 10)

        Returns:
            Markdown formatted options chain with greeks and OI analysis
        """
        try:
            data = self.client.get_option_chain(symbol, expiry_date=expiry_date)

            spot = data.get("spot_price", 0)
            expiry = data.get("expiry_date", "")
            expiries = data.get("available_expiries", [])
            chain = data.get("option_chain", [])

            if not chain:
                return f"No options data found for {symbol}"

            # Find ATM strike
            atm_strike = min(chain, key=lambda x: abs(x["strike_price"] - spot))["strike_price"]

            # Filter strikes around ATM
            atm_index = next(i for i, x in enumerate(chain) if x["strike_price"] == atm_strike)
            filtered_chain = [
                s for i, s in enumerate(chain)
                if abs(i - atm_index) <= strikes_around_atm
            ]

            # Calculate PCR
            total_call_oi = sum(s["ce"]["oi"] if s.get("ce") else 0 for s in chain)
            total_put_oi = sum(s["pe"]["oi"] if s.get("pe") else 0 for s in chain)
            pcr = total_put_oi / total_call_oi if total_call_oi > 0 else 0

            # Find max OI strikes
            max_call_oi_strike = max(chain, key=lambda x: x["ce"]["oi"] if x.get("ce") else 0)
            max_put_oi_strike = max(chain, key=lambda x: x["pe"]["oi"] if x.get("pe") else 0)

            lines = [f"# {symbol.upper()} Options Chain", ""]
            lines.append(f"**Spot:** {spot:,.2f} | **Expiry:** {expiry} | **PCR:** {pcr:.2f}")
            lines.append("")

            # Available expiries
            if expiries:
                lines.append(f"**Available Expiries:** {', '.join(expiries[:5])}")
                lines.append("")

            # Max OI analysis
            lines.append("## Key Levels (Max OI)")
            lines.append("")
            if max_call_oi_strike.get("ce"):
                lines.append(f"**Max Call OI:** {max_call_oi_strike['strike_price']:,.0f} ({max_call_oi_strike['ce']['oi']:,}) - Potential Resistance")
            if max_put_oi_strike.get("pe"):
                lines.append(f"**Max Put OI:** {max_put_oi_strike['strike_price']:,.0f} ({max_put_oi_strike['pe']['oi']:,}) - Potential Support")
            lines.append("")

            # Options chain table with full greeks
            lines.append("## Option Chain (with Greeks)")
            lines.append("")
            lines.append("| CE LTP | CE IV | CE Δ | CE Γ | CE Θ | CE V | CE OI | Strike | PE OI | PE V | PE Θ | PE Γ | PE Δ | PE IV | PE LTP |")
            lines.append("|--------|-------|------|------|------|------|-------|--------|-------|------|------|------|------|-------|--------|")

            for s in filtered_chain:
                strike = s["strike_price"]
                ce = s.get("ce") or {}
                pe = s.get("pe") or {}

                # Format CE data
                ce_ltp = f"{ce.get('ltp', 0):,.2f}" if ce.get('ltp') else "-"
                ce_iv = f"{ce.get('iv', 0):.1f}%" if ce.get('iv') else "-"
                ce_delta = f"{ce.get('delta', 0):.3f}" if ce.get('delta') is not None else "-"
                ce_gamma = f"{ce.get('gamma', 0):.4f}" if ce.get('gamma') is not None else "-"
                ce_theta = f"{ce.get('theta', 0):.2f}" if ce.get('theta') is not None else "-"
                ce_vega = f"{ce.get('vega', 0):.2f}" if ce.get('vega') is not None else "-"
                ce_oi = f"{ce.get('oi', 0):,}" if ce.get('oi') else "-"

                # Format PE data
                pe_ltp = f"{pe.get('ltp', 0):,.2f}" if pe.get('ltp') else "-"
                pe_iv = f"{pe.get('iv', 0):.1f}%" if pe.get('iv') else "-"
                pe_delta = f"{pe.get('delta', 0):.3f}" if pe.get('delta') is not None else "-"
                pe_gamma = f"{pe.get('gamma', 0):.4f}" if pe.get('gamma') is not None else "-"
                pe_theta = f"{pe.get('theta', 0):.2f}" if pe.get('theta') is not None else "-"
                pe_vega = f"{pe.get('vega', 0):.2f}" if pe.get('vega') is not None else "-"
                pe_oi = f"{pe.get('oi', 0):,}" if pe.get('oi') else "-"

                # Highlight ATM strike
                strike_str = f"**{strike:,.0f}**" if strike == atm_strike else f"{strike:,.0f}"

                lines.append(f"| {ce_ltp} | {ce_iv} | {ce_delta} | {ce_gamma} | {ce_theta} | {ce_vega} | {ce_oi} | {strike_str} | {pe_oi} | {pe_vega} | {pe_theta} | {pe_gamma} | {pe_delta} | {pe_iv} | {pe_ltp} |")

            lines.append("")
            lines.append("*Δ=Delta, Γ=Gamma, Θ=Theta, V=Vega*")
            lines.append("")

            return "\n".join(lines)

        except Exception as e:
            return f"Error fetching options chain for {symbol}: {str(e)}"

    def get_stock_price(self, symbol: str, exchange: str = "NSE") -> str:
        """Get live OHLC price for a stock.

        Use this tool to fetch current trading data including:
        - Last traded price (LTP) with day change
        - OHLC prices
        - Volume
        - 52-week high/low

        Args:
            symbol: NSE/BSE scrip code (e.g., "RELIANCE", "TCS", "INFY")
            exchange: Exchange - "NSE" or "BSE" (default: "NSE")

        Returns:
            Markdown formatted live price with OHLC, volume, and 52-week range
        """
        try:
            data = self.client.get_live_price(symbol, exchange=exchange)

            ltp = data.get("ltp", 0)
            day_change = data.get("day_change", 0)
            day_change_perc = data.get("day_change_perc", 0)
            open_price = data.get("open", 0)
            high = data.get("high", 0)
            low = data.get("low", 0)
            close = data.get("close", 0)
            volume = data.get("volume", 0)
            year_high = data.get("year_high", 0)
            year_low = data.get("year_low", 0)

            # Calculate position in 52W range
            range_position = 0
            if year_high and year_low and year_high != year_low:
                range_position = ((ltp - year_low) / (year_high - year_low)) * 100

            change_sign = "+" if day_change >= 0 else ""
            change_emoji = "🟢" if day_change >= 0 else "🔴"

            lines = [f"# {symbol} ({exchange}) - Live Price", ""]
            lines.append(f"**LTP:** ₹{ltp:,.2f} {change_emoji} {change_sign}{day_change:,.2f} ({change_sign}{day_change_perc:.2f}%)")
            lines.append("")

            # OHLC table
            lines.append("| Open | High | Low | Prev Close | Volume |")
            lines.append("|------|------|-----|------------|--------|")
            lines.append(f"| ₹{open_price:,.2f} | ₹{high:,.2f} | ₹{low:,.2f} | ₹{close:,.2f} | {self._format_volume(volume)} |")
            lines.append("")

            # 52-week range
            lines.append(f"**52W Range:** ₹{year_low:,.2f} - ₹{year_high:,.2f}")
            lines.append(f"**Current Position:** {range_position:.1f}% from 52W low")
            lines.append("")

            # Visual range indicator
            filled = int(range_position / 5)
            empty = 20 - filled
            range_bar = "█" * filled + "░" * empty
            lines.append(f"```")
            lines.append(f"52W Low [{range_bar}] 52W High")
            lines.append(f"```")

            return "\n".join(lines)

        except Exception as e:
            return f"Error fetching price for {symbol}: {str(e)}"

    def _format_volume(self, volume: int | None) -> str:
        """Format volume in lakhs/crores."""
        if volume is None:
            return "-"
        if volume >= 10000000:
            return f"{volume / 10000000:.2f}Cr"
        elif volume >= 100000:
            return f"{volume / 100000:.2f}L"
        else:
            return f"{volume:,}"

    def get_stock_details(self, search_id: str) -> str:
        """Get company details and fundamentals.

        Use this tool to fetch comprehensive company information:
        - Basic info (sector, industry, CEO, website)
        - Key metrics (P/E, P/B, ROE, EPS, dividend yield)
        - Live price data
        - Shareholding pattern
        - Financial summary (revenue, profit, margins)

        Args:
            search_id: Groww search ID from search results
                      (e.g., "reliance-industries-ltd", "tcs")

        Returns:
            Markdown formatted company profile with fundamentals
        """
        try:
            data = self.client.get_company_details(search_id)

            basic = data.get("basic", {})
            stats = data.get("stats", {})
            live = data.get("live_data", {})
            holding = data.get("shareholding", {})
            financials = data.get("financials_summary", {})

            name = basic.get("name", search_id)
            nse = basic.get("nse_symbol", "-")
            sector = basic.get("sector", "-")
            industry = basic.get("industry", "-")

            lines = [f"# {name}", ""]
            lines.append(f"**NSE:** {nse} | **Sector:** {sector} | **Industry:** {industry}")
            lines.append("")

            # CEO and other info
            ceo = basic.get("ceo")
            website = basic.get("website")
            if ceo or website:
                if ceo:
                    lines.append(f"**CEO:** {ceo}")
                if website:
                    lines.append(f"**Website:** {website}")
                lines.append("")

            # Live price
            ltp = live.get("ltp", 0)
            day_change = live.get("day_change", 0)
            day_change_perc = live.get("day_change_perc", 0)

            if ltp:
                change_sign = "+" if day_change >= 0 else ""
                change_emoji = "🟢" if day_change >= 0 else "🔴"
                lines.append(f"## Current Price")
                lines.append("")
                lines.append(f"**₹{ltp:,.2f}** {change_emoji} {change_sign}{day_change:,.2f} ({change_sign}{day_change_perc:.2f}%)")
                lines.append("")

                year_high = live.get("year_high", 0)
                year_low = live.get("year_low", 0)
                if year_high and year_low:
                    lines.append(f"**52W Range:** ₹{year_low:,.2f} - ₹{year_high:,.2f}")
                    lines.append("")

            # Key metrics
            lines.append("## Key Metrics")
            lines.append("")
            lines.append("| Metric | Value |")
            lines.append("|--------|-------|")

            market_cap = stats.get("market_cap")
            if market_cap:
                if market_cap >= 100000:
                    cap_str = f"₹{market_cap/100:.0f} Cr"
                else:
                    cap_str = f"₹{market_cap:,.0f} L"
                lines.append(f"| Market Cap | {cap_str} |")

            pe = stats.get("pe_ratio")
            if pe:
                lines.append(f"| P/E Ratio | {pe:.2f} |")

            pb = stats.get("pb_ratio")
            if pb:
                lines.append(f"| P/B Ratio | {pb:.2f} |")

            roe = stats.get("roe")
            if roe:
                lines.append(f"| ROE | {roe:.2f}% |")

            roce = stats.get("roce")
            if roce:
                lines.append(f"| ROCE | {roce:.2f}% |")

            eps = stats.get("eps")
            if eps:
                lines.append(f"| EPS | ₹{eps:.2f} |")

            div_yield = stats.get("dividend_yield")
            if div_yield:
                lines.append(f"| Dividend Yield | {div_yield:.2f}% |")

            debt_equity = stats.get("debt_to_equity")
            if debt_equity:
                lines.append(f"| Debt/Equity | {debt_equity:.2f} |")

            book_value = stats.get("book_value")
            if book_value:
                lines.append(f"| Book Value | ₹{book_value:.2f} |")

            lines.append("")

            # Shareholding
            if holding:
                lines.append("## Shareholding Pattern")
                lines.append("")

                for category, value in holding.items():
                    if value:
                        category_name = category.replace("_", " ").title()
                        lines.append(f"- **{category_name}:** {value:.2f}%")

                lines.append("")

            # Financials summary
            if financials:
                lines.append("## Financial Summary (TTM)")
                lines.append("")

                revenue = financials.get("revenue")
                if revenue:
                    if revenue >= 100000:
                        rev_str = f"₹{revenue/100:.0f} Cr"
                    else:
                        rev_str = f"₹{revenue:,.0f} L"
                    lines.append(f"- **Revenue:** {rev_str}")

                profit = financials.get("net_profit")
                if profit:
                    if abs(profit) >= 100000:
                        profit_str = f"₹{profit/100:.0f} Cr"
                    else:
                        profit_str = f"₹{profit:,.0f} L"
                    lines.append(f"- **Net Profit:** {profit_str}")

                opm = financials.get("operating_profit_margin")
                if opm:
                    lines.append(f"- **OPM:** {opm:.2f}%")

                npm = financials.get("net_profit_margin")
                if npm:
                    lines.append(f"- **NPM:** {npm:.2f}%")

                lines.append("")

            # About
            about = basic.get("about")
            if about:
                lines.append("## About")
                lines.append("")
                lines.append(about)
                lines.append("")

            return "\n".join(lines)

        except Exception as e:
            return f"Error fetching details for {search_id}: {str(e)}"

    def get_market_movers(self, category: str = "all", size: int = 5) -> str:
        """Get market movers - top gainers, losers, and popular stocks.

        Use this tool to find:
        - Stocks with biggest gains today
        - Stocks with biggest losses today
        - Most popular/bought stocks

        Args:
            category: Category to fetch - "all", "gainers", "losers", "popular" (default: "all")
            size: Number of stocks per category (default: 5)

        Returns:
            Markdown formatted tables of market movers
        """
        try:
            categories = []
            if category in ("all", "gainers"):
                categories.append("TOP_GAINERS")
            if category in ("all", "losers"):
                categories.append("TOP_LOSERS")
            if category in ("all", "popular"):
                categories.append("POPULAR_STOCKS_MOST_BOUGHT")

            data = self.client.get_market_movers(categories=categories, size=size)

            lines = ["# Market Movers", ""]

            # Top Gainers
            gainers = data.get("top_gainers", [])
            if gainers:
                lines.append("## Top Gainers")
                lines.append("")
                lines.append("| Stock | LTP | Change |")
                lines.append("|-------|-----|--------|")

                for g in gainers:
                    symbol = g.get("symbol", "-")
                    name = g.get("name", "-")
                    if len(name) > 20:
                        name = name[:17] + "..."
                    ltp = g.get("ltp", 0)
                    change = g.get("day_change_perc", 0)
                    lines.append(f"| {symbol} ({name}) | ₹{ltp:,.2f} | +{change:.2f}% |")

                lines.append("")

            # Top Losers
            losers = data.get("top_losers", [])
            if losers:
                lines.append("## Top Losers")
                lines.append("")
                lines.append("| Stock | LTP | Change |")
                lines.append("|-------|-----|--------|")

                for l in losers:
                    symbol = l.get("symbol", "-")
                    name = l.get("name", "-")
                    if len(name) > 20:
                        name = name[:17] + "..."
                    ltp = l.get("ltp", 0)
                    change = l.get("day_change_perc", 0)
                    lines.append(f"| {symbol} ({name}) | ₹{ltp:,.2f} | {change:.2f}% |")

                lines.append("")

            # Popular Stocks
            popular = data.get("popular_stocks_most_bought", [])
            if popular:
                lines.append("## Most Bought Stocks")
                lines.append("")
                lines.append("| Stock | LTP | Change |")
                lines.append("|-------|-----|--------|")

                for p in popular:
                    symbol = p.get("symbol", "-")
                    name = p.get("name", "-")
                    if len(name) > 20:
                        name = name[:17] + "..."
                    ltp = p.get("ltp", 0)
                    change = p.get("day_change_perc", 0)
                    change_sign = "+" if change >= 0 else ""
                    lines.append(f"| {symbol} ({name}) | ₹{ltp:,.2f} | {change_sign}{change:.2f}% |")

                lines.append("")

            if len(lines) <= 2:
                return "No market mover data available."

            return "\n".join(lines)

        except Exception as e:
            return f"Error fetching market movers: {str(e)}"

    def get_global_indices(self) -> str:
        """Get live prices for global indices.

        Returns live data for major global indices:
        - SGX Nifty (GIFT Nifty) - India
        - Dow Futures, Dow Jones - USA
        - S&P 500 - USA
        - NASDAQ - USA
        - NIKKEI 225 - Japan
        - Hang Seng - Hong Kong
        - DAX - Germany
        - CAC 40 - France
        - FTSE 100 - UK

        Returns:
            Markdown formatted table of global indices with live prices
        """
        try:
            data = self.client.get_global_indices()

            if not data:
                return "No global indices data available."

            lines = ["# Global Indices", ""]

            # Group by continent
            by_continent: dict[str, list] = {}
            for item in data:
                continent = item.get("continent", "OTHER")
                if continent not in by_continent:
                    by_continent[continent] = []
                by_continent[continent].append(item)

            # Order: Asia, US, Europe
            continent_order = ["ASIA", "US", "EUROPE"]

            for continent in continent_order:
                items = by_continent.get(continent, [])
                if not items:
                    continue

                lines.append(f"## {continent}")
                lines.append("")
                lines.append("| Index | Value | Change | Open | High | Low |")
                lines.append("|-------|-------|--------|------|------|-----|")

                for item in items:
                    name = item.get("name", "-")
                    value = item.get("value", 0)
                    change = item.get("day_change", 0)
                    change_perc = item.get("day_change_perc", 0)
                    open_price = item.get("open", 0)
                    high = item.get("high", 0)
                    low = item.get("low", 0)

                    change_sign = "+" if change >= 0 else ""
                    change_emoji = "🟢" if change >= 0 else "🔴"

                    lines.append(
                        f"| {name} | {value:,.2f} | {change_emoji} {change_sign}{change_perc:.2f}% | {open_price:,.2f} | {high:,.2f} | {low:,.2f} |"
                    )

                lines.append("")

            return "\n".join(lines)

        except Exception as e:
            return f"Error fetching global indices: {str(e)}"

    def get_indian_indices(self) -> str:
        """Get Indian market indices data.

        Returns data for major Indian indices including:
        - NIFTY 50, NIFTY Bank
        - BSE Sensex
        - India VIX
        - NIFTY Next 50, NIFTY 100, NIFTY 500
        - NIFTY Midcap, Smallcap indices
        - Sectoral indices (IT, Pharma, Auto, FMCG, etc.)

        Returns:
            Markdown formatted table of Indian indices
        """
        try:
            data = self.client.get_indian_indices()

            if not data:
                return "No Indian indices data available."

            lines = ["# Indian Indices", ""]
            lines.append("| Index | Symbol | F&O | 52W Low | 52W High |")
            lines.append("|-------|--------|-----|---------|----------|")

            # Sort by F&O enabled first, then alphabetically
            sorted_data = sorted(data, key=lambda x: (not x.get("is_fno_enabled", False), x.get("display_name", "")))

            for item in sorted_data:
                name = item.get("display_name", "-")
                symbol = item.get("symbol", "-")
                is_fno = "Yes" if item.get("is_fno_enabled") else "No"
                year_low = item.get("year_low", 0)
                year_high = item.get("year_high", 0)

                year_low_str = f"₹{year_low:,.0f}" if year_low else "-"
                year_high_str = f"₹{year_high:,.0f}" if year_high else "-"

                lines.append(f"| {name} | {symbol} | {is_fno} | {year_low_str} | {year_high_str} |")

            lines.append("")
            lines.append("*F&O = Futures & Options available*")

            return "\n".join(lines)

        except Exception as e:
            return f"Error fetching Indian indices: {str(e)}"

    def close(self) -> None:
        """Close the client connection."""
        self.client.close()
