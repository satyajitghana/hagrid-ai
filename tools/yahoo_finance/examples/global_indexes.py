"""Examples for fetching global index data from Yahoo Finance.

This script demonstrates how to:
- Fetch major global indexes
- Get historical data for indexes
- Compare index performance
- Analyze regional markets
"""

from tools.yahoo_finance import YFinanceClient


def fetch_global_indexes():
    """Fetch current data for major global indexes."""
    print("=" * 60)
    print("Major Global Indexes")
    print("=" * 60)

    client = YFinanceClient()
    indexes = client.get_global_indexes()

    print(f"\n| {'Index':<30} | {'Country':<12} | {'Price':>12} | {'Change':>10} | {'% Change':>10} |")
    print("|" + "-" * 32 + "|" + "-" * 14 + "|" + "-" * 14 + "|" + "-" * 12 + "|" + "-" * 12 + "|")

    for idx in indexes:
        name = idx.name[:30] if idx.name else idx.symbol
        country = idx.country or "N/A"
        price = f"{idx.last_price:,.2f}" if idx.last_price else "N/A"
        change = f"{idx.change:+,.2f}" if idx.change else "N/A"
        change_pct = f"{idx.change_percent:+.2f}%" if idx.change_percent else "N/A"

        print(f"| {name:<30} | {country:<12} | {price:>12} | {change:>10} | {change_pct:>10} |")


def fetch_us_indexes():
    """Fetch detailed data for major US indexes."""
    print("\n" + "=" * 60)
    print("US Market Indexes")
    print("=" * 60)

    client = YFinanceClient()

    us_indexes = [
        ("^GSPC", "S&P 500"),
        ("^DJI", "Dow Jones Industrial Average"),
        ("^IXIC", "NASDAQ Composite"),
        ("^RUT", "Russell 2000"),
        ("^VIX", "CBOE Volatility Index"),
    ]

    print()
    for symbol, name in us_indexes:
        try:
            info = client.get_ticker_info(symbol)
            i = info.info

            current = i.get('regularMarketPrice', i.get('previousClose', 0))
            prev_close = i.get('previousClose', 0)
            day_high = i.get('dayHigh', 0)
            day_low = i.get('dayLow', 0)

            change = current - prev_close if current and prev_close else 0
            change_pct = (change / prev_close * 100) if prev_close else 0

            print(f"--- {name} ({symbol}) ---")
            print(f"  Current: {current:,.2f}" if current else "  Current: N/A")
            print(f"  Change: {change:+,.2f} ({change_pct:+.2f}%)" if change else "  Change: N/A")
            print(f"  Day Range: {day_low:,.2f} - {day_high:,.2f}" if day_low and day_high else "  Day Range: N/A")
            print()
        except Exception as e:
            print(f"--- {name} ({symbol}) ---")
            print(f"  Error: {str(e)}")
            print()


def fetch_asian_indexes():
    """Fetch data for major Asian indexes."""
    print("\n" + "=" * 60)
    print("Asian Market Indexes")
    print("=" * 60)

    client = YFinanceClient()

    asian_indexes = [
        ("^N225", "Nikkei 225", "Japan"),
        ("^HSI", "Hang Seng Index", "Hong Kong"),
        ("000001.SS", "SSE Composite", "China"),
        ("^BSESN", "S&P BSE SENSEX", "India"),
        ("^NSEI", "NIFTY 50", "India"),
        ("^KS11", "KOSPI", "South Korea"),
        ("^STI", "Straits Times Index", "Singapore"),
    ]

    print(f"\n| {'Index':<25} | {'Country':<12} | {'Price':>12} | {'Change %':>10} |")
    print("|" + "-" * 27 + "|" + "-" * 14 + "|" + "-" * 14 + "|" + "-" * 12 + "|")

    for symbol, name, country in asian_indexes:
        try:
            info = client.get_ticker_info(symbol)
            i = info.info

            current = i.get('regularMarketPrice', i.get('previousClose', 0))
            prev_close = i.get('previousClose', 0)
            change_pct = ((current - prev_close) / prev_close * 100) if current and prev_close else 0

            price_str = f"{current:,.2f}" if current else "N/A"
            change_str = f"{change_pct:+.2f}%" if change_pct else "N/A"

            print(f"| {name:<25} | {country:<12} | {price_str:>12} | {change_str:>10} |")
        except Exception as e:
            print(f"| {name:<25} | {country:<12} | Error: {str(e)[:20]} |")


def fetch_european_indexes():
    """Fetch data for major European indexes."""
    print("\n" + "=" * 60)
    print("European Market Indexes")
    print("=" * 60)

    client = YFinanceClient()

    european_indexes = [
        ("^FTSE", "FTSE 100", "UK"),
        ("^GDAXI", "DAX", "Germany"),
        ("^FCHI", "CAC 40", "France"),
        ("^STOXX50E", "Euro Stoxx 50", "Eurozone"),
        ("^IBEX", "IBEX 35", "Spain"),
        ("FTSEMIB.MI", "FTSE MIB", "Italy"),
    ]

    print(f"\n| {'Index':<20} | {'Country':<12} | {'Price':>12} | {'Change %':>10} |")
    print("|" + "-" * 22 + "|" + "-" * 14 + "|" + "-" * 14 + "|" + "-" * 12 + "|")

    for symbol, name, country in european_indexes:
        try:
            info = client.get_ticker_info(symbol)
            i = info.info

            current = i.get('regularMarketPrice', i.get('previousClose', 0))
            prev_close = i.get('previousClose', 0)
            change_pct = ((current - prev_close) / prev_close * 100) if current and prev_close else 0

            price_str = f"{current:,.2f}" if current else "N/A"
            change_str = f"{change_pct:+.2f}%" if change_pct else "N/A"

            print(f"| {name:<20} | {country:<12} | {price_str:>12} | {change_str:>10} |")
        except Exception as e:
            print(f"| {name:<20} | {country:<12} | Error: {str(e)[:20]} |")


def compare_index_ytd_performance():
    """Compare year-to-date performance of major indexes."""
    print("\n" + "=" * 60)
    print("Year-to-Date Index Performance")
    print("=" * 60)

    client = YFinanceClient()

    indexes = [
        ("^GSPC", "S&P 500"),
        ("^DJI", "Dow Jones"),
        ("^IXIC", "NASDAQ"),
        ("^FTSE", "FTSE 100"),
        ("^GDAXI", "DAX"),
        ("^N225", "Nikkei 225"),
        ("^NSEI", "NIFTY 50"),
    ]

    print(f"\n| {'Index':<15} | {'YTD Start':>12} | {'Current':>12} | {'YTD Return':>12} |")
    print("|" + "-" * 17 + "|" + "-" * 14 + "|" + "-" * 14 + "|" + "-" * 14 + "|")

    for symbol, name in indexes:
        try:
            # Get YTD data
            history = client.get_historical_data(symbol, period="ytd", interval="1d")

            if history.history:
                ytd_start = history.history[0].open
                current = history.history[-1].close
                ytd_return = ((current - ytd_start) / ytd_start) * 100

                print(f"| {name:<15} | {ytd_start:>12,.2f} | {current:>12,.2f} | {ytd_return:>+11.2f}% |")
            else:
                print(f"| {name:<15} | No data available |")
        except Exception as e:
            print(f"| {name:<15} | Error: {str(e)[:30]} |")


def fetch_index_historical_data(symbol: str = "^GSPC", name: str = "S&P 500"):
    """Fetch historical data for an index."""
    print("\n" + "=" * 60)
    print(f"Historical Data for {name} ({symbol})")
    print("=" * 60)

    client = YFinanceClient()

    # Get 1 year of weekly data
    history = client.get_historical_data(symbol, period="1y", interval="1wk")

    if not history.history:
        print("\nNo historical data available")
        return

    print(f"\nData points: {len(history.history)}")
    print()

    # Show last 12 weeks
    print("| Week Ending | Open       | High       | Low        | Close      | Change % |")
    print("|-------------|------------|------------|------------|------------|----------|")

    prev_close = None
    for h in history.history[-12:]:
        date_str = h.date.strftime('%Y-%m-%d')
        change_pct = ((h.close - prev_close) / prev_close * 100) if prev_close else 0
        change_str = f"{change_pct:>+7.2f}%" if prev_close else "    -   "

        print(f"| {date_str}  | {h.open:>10,.2f} | {h.high:>10,.2f} | {h.low:>10,.2f} | {h.close:>10,.2f} | {change_str} |")
        prev_close = h.close


def analyze_index_volatility():
    """Analyze volatility across major indexes."""
    print("\n" + "=" * 60)
    print("Index Volatility Analysis (30-Day)")
    print("=" * 60)

    client = YFinanceClient()

    indexes = [
        ("^GSPC", "S&P 500"),
        ("^IXIC", "NASDAQ"),
        ("^DJI", "Dow Jones"),
        ("^N225", "Nikkei 225"),
        ("^NSEI", "NIFTY 50"),
    ]

    print(f"\n| {'Index':<15} | {'Avg Daily Move':>15} | {'Max Up':>10} | {'Max Down':>10} | {'Volatility':>12} |")
    print("|" + "-" * 17 + "|" + "-" * 17 + "|" + "-" * 12 + "|" + "-" * 12 + "|" + "-" * 14 + "|")

    for symbol, name in indexes:
        try:
            history = client.get_historical_data(symbol, period="1mo", interval="1d")

            if not history.history or len(history.history) < 2:
                print(f"| {name:<15} | Insufficient data |")
                continue

            closes = [h.close for h in history.history]

            # Calculate daily returns
            daily_returns = []
            for i in range(1, len(closes)):
                ret = ((closes[i] - closes[i-1]) / closes[i-1]) * 100
                daily_returns.append(ret)

            avg_move = sum(abs(r) for r in daily_returns) / len(daily_returns)
            max_up = max(daily_returns)
            max_down = min(daily_returns)

            # Volatility (std dev of returns)
            avg_ret = sum(daily_returns) / len(daily_returns)
            variance = sum((r - avg_ret) ** 2 for r in daily_returns) / len(daily_returns)
            volatility = variance ** 0.5

            print(f"| {name:<15} | {avg_move:>14.2f}% | {max_up:>+9.2f}% | {max_down:>+9.2f}% | {volatility:>11.2f}% |")
        except Exception as e:
            print(f"| {name:<15} | Error: {str(e)[:30]} |")


def fetch_commodity_indexes():
    """Fetch data for commodity-related indexes and futures."""
    print("\n" + "=" * 60)
    print("Commodity Indexes and Futures")
    print("=" * 60)

    client = YFinanceClient()

    commodities = [
        ("GC=F", "Gold Futures"),
        ("SI=F", "Silver Futures"),
        ("CL=F", "Crude Oil (WTI)"),
        ("BZ=F", "Brent Crude"),
        ("NG=F", "Natural Gas"),
        ("^SPGSCI", "S&P GSCI"),
    ]

    print(f"\n| {'Commodity':<20} | {'Price':>12} | {'Change':>10} | {'Change %':>10} |")
    print("|" + "-" * 22 + "|" + "-" * 14 + "|" + "-" * 12 + "|" + "-" * 12 + "|")

    for symbol, name in commodities:
        try:
            info = client.get_ticker_info(symbol)
            i = info.info

            current = i.get('regularMarketPrice', i.get('previousClose', 0))
            prev_close = i.get('previousClose', 0)
            change = current - prev_close if current and prev_close else 0
            change_pct = (change / prev_close * 100) if prev_close else 0

            price_str = f"{current:,.2f}" if current else "N/A"
            change_str = f"{change:+,.2f}" if change else "N/A"
            pct_str = f"{change_pct:+.2f}%" if change_pct else "N/A"

            print(f"| {name:<20} | {price_str:>12} | {change_str:>10} | {pct_str:>10} |")
        except Exception as e:
            print(f"| {name:<20} | Error: {str(e)[:25]} |")


def fetch_currency_pairs():
    """Fetch major currency pairs."""
    print("\n" + "=" * 60)
    print("Major Currency Pairs")
    print("=" * 60)

    client = YFinanceClient()

    pairs = [
        ("EURUSD=X", "EUR/USD"),
        ("GBPUSD=X", "GBP/USD"),
        ("USDJPY=X", "USD/JPY"),
        ("USDCAD=X", "USD/CAD"),
        ("AUDUSD=X", "AUD/USD"),
        ("USDINR=X", "USD/INR"),
        ("USDCNY=X", "USD/CNY"),
    ]

    print(f"\n| {'Pair':<12} | {'Rate':>12} | {'Change':>10} | {'Change %':>10} |")
    print("|" + "-" * 14 + "|" + "-" * 14 + "|" + "-" * 12 + "|" + "-" * 12 + "|")

    for symbol, name in pairs:
        try:
            info = client.get_ticker_info(symbol)
            i = info.info

            current = i.get('regularMarketPrice', i.get('previousClose', 0))
            prev_close = i.get('previousClose', 0)
            change = current - prev_close if current and prev_close else 0
            change_pct = (change / prev_close * 100) if prev_close else 0

            rate_str = f"{current:.4f}" if current else "N/A"
            change_str = f"{change:+.4f}" if change else "N/A"
            pct_str = f"{change_pct:+.2f}%" if change_pct else "N/A"

            print(f"| {name:<12} | {rate_str:>12} | {change_str:>10} | {pct_str:>10} |")
        except Exception as e:
            print(f"| {name:<12} | Error: {str(e)[:25]} |")


def compare_us_sector_etfs():
    """Compare US sector ETFs."""
    print("\n" + "=" * 60)
    print("US Sector ETF Performance")
    print("=" * 60)

    client = YFinanceClient()

    sector_etfs = [
        ("XLK", "Technology"),
        ("XLF", "Financials"),
        ("XLV", "Healthcare"),
        ("XLE", "Energy"),
        ("XLI", "Industrials"),
        ("XLY", "Consumer Discretionary"),
        ("XLP", "Consumer Staples"),
        ("XLU", "Utilities"),
        ("XLB", "Materials"),
        ("XLRE", "Real Estate"),
    ]

    print(f"\n| {'Sector':<25} | {'Price':>10} | {'Day %':>10} | {'YTD %':>10} |")
    print("|" + "-" * 27 + "|" + "-" * 12 + "|" + "-" * 12 + "|" + "-" * 12 + "|")

    for symbol, sector in sector_etfs:
        try:
            info = client.get_ticker_info(symbol)
            i = info.info

            current = i.get('regularMarketPrice', i.get('previousClose', 0))
            prev_close = i.get('previousClose', 0)
            day_change = ((current - prev_close) / prev_close * 100) if current and prev_close else 0

            # YTD calculation
            ytd_change = i.get('ytdReturn', 0)
            if not ytd_change:
                history = client.get_historical_data(symbol, period="ytd", interval="1d")
                if history.history:
                    ytd_start = history.history[0].open
                    ytd_change = ((current - ytd_start) / ytd_start) * 100 if ytd_start else 0

            price_str = f"${current:.2f}" if current else "N/A"
            day_str = f"{day_change:+.2f}%" if day_change else "N/A"
            ytd_str = f"{ytd_change:+.2f}%" if ytd_change else "N/A"

            print(f"| {sector:<25} | {price_str:>10} | {day_str:>10} | {ytd_str:>10} |")
        except Exception as e:
            print(f"| {sector:<25} | Error: {str(e)[:25]} |")


if __name__ == "__main__":
    # Run all examples
    fetch_global_indexes()
    fetch_us_indexes()
    fetch_asian_indexes()
    fetch_european_indexes()
    compare_index_ytd_performance()
    fetch_index_historical_data("^GSPC", "S&P 500")
    analyze_index_volatility()
    fetch_commodity_indexes()
    fetch_currency_pairs()
    compare_us_sector_etfs()
