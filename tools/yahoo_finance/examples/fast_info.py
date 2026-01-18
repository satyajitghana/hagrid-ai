"""Examples for fast_info - lightweight price data from Yahoo Finance.

This script demonstrates how to:
- Fetch fast/lightweight price data for quick lookups
- Compare fast_info vs full info performance
- Get real-time price snapshots for multiple stocks
"""

from tools.yahoo_finance import YFinanceClient


def fetch_fast_info(symbol: str = "AAPL"):
    """Fetch fast info for a ticker - lightweight price data."""
    print("=" * 60)
    print(f"Fast Info for {symbol}")
    print("=" * 60)

    client = YFinanceClient()
    fi = client.get_fast_info(symbol)

    print(f"\nSymbol: {fi.symbol}")
    print(f"Currency: {fi.currency}")
    print(f"Exchange: {fi.exchange}")
    print(f"Quote Type: {fi.quote_type}")
    print(f"Timezone: {fi.timezone}")
    print()

    print("--- Price Data ---")
    print(f"Last Price: {fi.last_price}")
    print(f"Previous Close: {fi.previous_close}")
    print(f"Open: {fi.open}")
    print(f"Day High: {fi.day_high}")
    print(f"Day Low: {fi.day_low}")
    print()

    print("--- Volume ---")
    print(f"Last Volume: {fi.last_volume:,}" if fi.last_volume else "Last Volume: N/A")
    print(f"10-Day Avg Volume: {fi.ten_day_average_volume:,}" if fi.ten_day_average_volume else "10-Day Avg: N/A")
    print(f"3-Month Avg Volume: {fi.three_month_average_volume:,}" if fi.three_month_average_volume else "3-Month Avg: N/A")
    print()

    print("--- Moving Averages ---")
    print(f"50-Day Average: {fi.fifty_day_average}")
    print(f"200-Day Average: {fi.two_hundred_day_average}")
    print()

    print("--- Year Performance ---")
    print(f"Year High: {fi.year_high}")
    print(f"Year Low: {fi.year_low}")
    print(f"Year Change: {fi.year_change:.2%}" if fi.year_change else "Year Change: N/A")
    print()

    print("--- Market Cap ---")
    if fi.market_cap:
        if fi.market_cap >= 1e12:
            print(f"Market Cap: ${fi.market_cap/1e12:.2f}T")
        elif fi.market_cap >= 1e9:
            print(f"Market Cap: ${fi.market_cap/1e9:.2f}B")
        else:
            print(f"Market Cap: ${fi.market_cap/1e6:.2f}M")
    print(f"Shares Outstanding: {fi.shares:,}" if fi.shares else "Shares: N/A")


def compare_fast_info_multiple_stocks():
    """Compare fast info across multiple stocks."""
    print("\n" + "=" * 60)
    print("Fast Info Comparison - Tech Giants")
    print("=" * 60)

    client = YFinanceClient()
    symbols = ["AAPL", "MSFT", "GOOGL", "AMZN", "META", "NVDA"]

    print("\n| Symbol | Last Price | Day Change | Volume | Market Cap |")
    print("|--------|------------|------------|--------|------------|")

    for symbol in symbols:
        fi = client.get_fast_info(symbol)

        if fi.last_price and fi.previous_close:
            change = fi.last_price - fi.previous_close
            change_pct = (change / fi.previous_close) * 100
            change_str = f"{change_pct:+.2f}%"
        else:
            change_str = "N/A"

        vol_str = f"{fi.last_volume/1e6:.1f}M" if fi.last_volume else "N/A"

        if fi.market_cap:
            if fi.market_cap >= 1e12:
                mcap_str = f"${fi.market_cap/1e12:.2f}T"
            else:
                mcap_str = f"${fi.market_cap/1e9:.0f}B"
        else:
            mcap_str = "N/A"

        print(f"| {symbol:<6} | ${fi.last_price:>9.2f} | {change_str:>10} | {vol_str:>6} | {mcap_str:>10} |")


def fetch_indian_stocks_fast_info():
    """Fetch fast info for Indian stocks."""
    print("\n" + "=" * 60)
    print("Fast Info - Indian Stocks")
    print("=" * 60)

    client = YFinanceClient()
    symbols = [
        ("RELIANCE.NS", "Reliance Industries"),
        ("TCS.NS", "Tata Consultancy"),
        ("INFY.NS", "Infosys"),
        ("HDFCBANK.NS", "HDFC Bank"),
        ("ICICIBANK.NS", "ICICI Bank"),
    ]

    print("\n| Stock | Name | Last Price (INR) | Day Change | Market Cap |")
    print("|-------|------|------------------|------------|------------|")

    for symbol, name in symbols:
        fi = client.get_fast_info(symbol)

        if fi.last_price and fi.previous_close:
            change_pct = ((fi.last_price - fi.previous_close) / fi.previous_close) * 100
            change_str = f"{change_pct:+.2f}%"
        else:
            change_str = "N/A"

        if fi.market_cap:
            # Convert to Lakh Crores (Indian notation)
            mcap_lcr = fi.market_cap / 1e12
            mcap_str = f"₹{mcap_lcr:.1f}L Cr"
        else:
            mcap_str = "N/A"

        price_str = f"₹{fi.last_price:,.2f}" if fi.last_price else "N/A"
        print(f"| {symbol:<14} | {name[:15]:<15} | {price_str:>16} | {change_str:>10} | {mcap_str:>10} |")


def fetch_price_snapshot():
    """Fetch a quick price snapshot for portfolio tracking."""
    print("\n" + "=" * 60)
    print("Quick Price Snapshot")
    print("=" * 60)

    client = YFinanceClient()

    # Sample portfolio
    portfolio = {
        "AAPL": 10,
        "MSFT": 5,
        "GOOGL": 3,
        "NVDA": 8,
    }

    print("\n| Symbol | Shares | Price | Value | Day P/L |")
    print("|--------|--------|-------|-------|---------|")

    total_value = 0
    total_pl = 0

    for symbol, shares in portfolio.items():
        fi = client.get_fast_info(symbol)

        if fi.last_price:
            value = fi.last_price * shares
            total_value += value

            if fi.previous_close:
                day_pl = (fi.last_price - fi.previous_close) * shares
                total_pl += day_pl
                pl_str = f"${day_pl:+,.2f}"
            else:
                pl_str = "N/A"

            print(f"| {symbol:<6} | {shares:>6} | ${fi.last_price:>7.2f} | ${value:>9,.2f} | {pl_str:>7} |")

    print("|--------|--------|-------|-------|---------|")
    print(f"| TOTAL  |        |       | ${total_value:>9,.2f} | ${total_pl:+,.2f} |")


def compare_etf_fast_info():
    """Compare fast info for popular ETFs."""
    print("\n" + "=" * 60)
    print("ETF Quick Comparison")
    print("=" * 60)

    client = YFinanceClient()

    etfs = [
        ("SPY", "S&P 500"),
        ("QQQ", "Nasdaq 100"),
        ("DIA", "Dow Jones"),
        ("IWM", "Russell 2000"),
        ("VTI", "Total Market"),
    ]

    print("\n| ETF | Index | Price | YTD Change | Volume |")
    print("|-----|-------|-------|------------|--------|")

    for symbol, name in etfs:
        fi = client.get_fast_info(symbol)

        price_str = f"${fi.last_price:.2f}" if fi.last_price else "N/A"
        ytd_str = f"{fi.year_change:.2%}" if fi.year_change else "N/A"
        vol_str = f"{fi.last_volume/1e6:.1f}M" if fi.last_volume else "N/A"

        print(f"| {symbol:<3} | {name:<13} | {price_str:>7} | {ytd_str:>10} | {vol_str:>6} |")


def fetch_isin():
    """Fetch ISIN numbers for stocks."""
    print("\n" + "=" * 60)
    print("ISIN Numbers")
    print("=" * 60)

    client = YFinanceClient()

    symbols = ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA"]

    print("\n| Symbol | ISIN |")
    print("|--------|------|")

    for symbol in symbols:
        isin = client.get_isin(symbol)
        print(f"| {symbol:<6} | {isin.isin or 'N/A'} |")


if __name__ == "__main__":
    fetch_fast_info("AAPL")
    compare_fast_info_multiple_stocks()
    fetch_indian_stocks_fast_info()
    fetch_price_snapshot()
    compare_etf_fast_info()
    fetch_isin()
