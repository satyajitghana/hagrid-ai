"""Examples for fetching historical price data from Yahoo Finance.

This script demonstrates how to:
- Fetch historical data with different periods (1d, 1mo, 1y, max)
- Use different intervals (1m, 5m, 1h, 1d, 1wk, 1mo)
- Fetch data for specific date ranges
- Calculate basic price statistics
- Compare performance across multiple stocks
"""

from datetime import datetime, timedelta
from tools.yahoo_finance import YFinanceClient


def fetch_recent_history(symbol: str = "AAPL"):
    """Fetch last 5 days of price data."""
    print("=" * 60)
    print(f"Recent Price History for {symbol} (Last 5 Days)")
    print("=" * 60)

    client = YFinanceClient()
    history = client.get_historical_data(symbol, period="5d", interval="1d")

    print(f"\nSymbol: {history.symbol}")
    print(f"Period: {history.period}")
    print(f"Interval: {history.interval}")
    print(f"Data points: {len(history.history)}")
    print()

    print("| Date       | Open     | High     | Low      | Close    | Volume       |")
    print("|------------|----------|----------|----------|----------|--------------|")

    for h in history.history:
        date_str = h.date.strftime('%Y-%m-%d')
        print(f"| {date_str} | {h.open:>8.2f} | {h.high:>8.2f} | {h.low:>8.2f} | {h.close:>8.2f} | {h.volume:>12,} |")


def fetch_intraday_data(symbol: str = "AAPL"):
    """Fetch intraday data with 1-hour intervals."""
    print("\n" + "=" * 60)
    print(f"Intraday Data for {symbol} (1-Hour Intervals)")
    print("=" * 60)

    client = YFinanceClient()
    history = client.get_historical_data(symbol, period="1d", interval="1h")

    print(f"\nData points: {len(history.history)}")
    print()

    print("| Time            | Open     | High     | Low      | Close    | Volume     |")
    print("|-----------------|----------|----------|----------|----------|------------|")

    for h in history.history:
        time_str = h.date.strftime('%Y-%m-%d %H:%M')
        print(f"| {time_str} | {h.open:>8.2f} | {h.high:>8.2f} | {h.low:>8.2f} | {h.close:>8.2f} | {h.volume:>10,} |")


def fetch_monthly_data(symbol: str = "MSFT"):
    """Fetch 1 year of monthly data."""
    print("\n" + "=" * 60)
    print(f"Monthly Price Data for {symbol} (1 Year)")
    print("=" * 60)

    client = YFinanceClient()
    history = client.get_historical_data(symbol, period="1y", interval="1mo")

    print(f"\nData points: {len(history.history)}")
    print()

    print("| Month      | Open     | High     | Low      | Close    | Change % |")
    print("|------------|----------|----------|----------|----------|----------|")

    prev_close = None
    for h in history.history:
        month_str = h.date.strftime('%Y-%m')
        change_pct = ((h.close - prev_close) / prev_close * 100) if prev_close else 0
        change_str = f"{change_pct:>+7.2f}%" if prev_close else "    -   "
        print(f"| {month_str}    | {h.open:>8.2f} | {h.high:>8.2f} | {h.low:>8.2f} | {h.close:>8.2f} | {change_str} |")
        prev_close = h.close


def fetch_custom_date_range(symbol: str = "GOOGL"):
    """Fetch data for a specific date range."""
    print("\n" + "=" * 60)
    print(f"Custom Date Range for {symbol}")
    print("=" * 60)

    client = YFinanceClient()

    # Last 30 days
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)

    history = client.get_historical_data(
        symbol,
        start=start_date.strftime('%Y-%m-%d'),
        end=end_date.strftime('%Y-%m-%d'),
        interval="1d"
    )

    print(f"\nDate Range: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
    print(f"Data points: {len(history.history)}")
    print()

    if history.history:
        first = history.history[0]
        last = history.history[-1]
        print(f"First Date: {first.date.strftime('%Y-%m-%d')}")
        print(f"Last Date: {last.date.strftime('%Y-%m-%d')}")
        print(f"Opening Price: ${first.open:.2f}")
        print(f"Closing Price: ${last.close:.2f}")
        change = ((last.close - first.open) / first.open) * 100
        print(f"Period Return: {change:+.2f}%")


def calculate_price_statistics(symbol: str = "NVDA"):
    """Calculate basic price statistics from historical data."""
    print("\n" + "=" * 60)
    print(f"Price Statistics for {symbol} (1 Month)")
    print("=" * 60)

    client = YFinanceClient()
    history = client.get_historical_data(symbol, period="1mo", interval="1d")

    if not history.history:
        print("No data available")
        return

    closes = [h.close for h in history.history]
    highs = [h.high for h in history.history]
    lows = [h.low for h in history.history]
    volumes = [h.volume for h in history.history]

    print(f"\n--- Price Statistics ---")
    print(f"Data Points: {len(closes)}")
    print(f"Current Price: ${closes[-1]:.2f}")
    print(f"Average Close: ${sum(closes)/len(closes):.2f}")
    print(f"Highest Price: ${max(highs):.2f}")
    print(f"Lowest Price: ${min(lows):.2f}")
    print(f"Price Range: ${max(highs) - min(lows):.2f}")

    # Volatility (simple standard deviation)
    avg = sum(closes) / len(closes)
    variance = sum((x - avg) ** 2 for x in closes) / len(closes)
    std_dev = variance ** 0.5
    print(f"Price Std Dev: ${std_dev:.2f}")
    print(f"Coefficient of Variation: {(std_dev/avg)*100:.2f}%")

    print(f"\n--- Volume Statistics ---")
    print(f"Average Volume: {int(sum(volumes)/len(volumes)):,}")
    print(f"Max Volume: {max(volumes):,}")
    print(f"Min Volume: {min(volumes):,}")

    print(f"\n--- Return Statistics ---")
    first_price = history.history[0].open
    last_price = closes[-1]
    total_return = ((last_price - first_price) / first_price) * 100
    print(f"Period Return: {total_return:+.2f}%")

    # Daily returns
    daily_returns = []
    for i in range(1, len(closes)):
        daily_ret = ((closes[i] - closes[i-1]) / closes[i-1]) * 100
        daily_returns.append(daily_ret)

    if daily_returns:
        avg_daily = sum(daily_returns) / len(daily_returns)
        max_daily = max(daily_returns)
        min_daily = min(daily_returns)
        print(f"Avg Daily Return: {avg_daily:+.3f}%")
        print(f"Best Day: {max_daily:+.2f}%")
        print(f"Worst Day: {min_daily:+.2f}%")


def compare_stock_performance(symbols: list[str] | None = None):
    """Compare performance across multiple stocks."""
    print("\n" + "=" * 60)
    print("Stock Performance Comparison (1 Month)")
    print("=" * 60)

    if symbols is None:
        symbols = ["AAPL", "MSFT", "GOOGL", "AMZN", "NVDA"]

    client = YFinanceClient()

    print("\n| Symbol | Start     | End       | Return % | High      | Low       | Volatility |")
    print("|--------|-----------|-----------|----------|-----------|-----------|------------|")

    for symbol in symbols:
        try:
            history = client.get_historical_data(symbol, period="1mo", interval="1d")

            if not history.history:
                print(f"| {symbol:<6} | No data available |")
                continue

            closes = [h.close for h in history.history]
            highs = [h.high for h in history.history]
            lows = [h.low for h in history.history]

            start_price = history.history[0].open
            end_price = closes[-1]
            ret = ((end_price - start_price) / start_price) * 100

            high = max(highs)
            low = min(lows)

            # Simple volatility
            avg = sum(closes) / len(closes)
            variance = sum((x - avg) ** 2 for x in closes) / len(closes)
            volatility = (variance ** 0.5 / avg) * 100

            print(f"| {symbol:<6} | ${start_price:>8.2f} | ${end_price:>8.2f} | {ret:>+7.2f}% | ${high:>8.2f} | ${low:>8.2f} | {volatility:>9.2f}% |")
        except Exception as e:
            print(f"| {symbol:<6} | Error: {str(e)[:40]} |")


def fetch_dividend_history(symbol: str = "JNJ"):
    """Fetch historical data including dividends."""
    print("\n" + "=" * 60)
    print(f"Dividend History for {symbol} (1 Year)")
    print("=" * 60)

    client = YFinanceClient()
    history = client.get_historical_data(symbol, period="1y", interval="1d")

    dividends = [(h.date, h.dividends) for h in history.history if h.dividends and h.dividends > 0]

    print(f"\nTotal data points: {len(history.history)}")
    print(f"Dividend payments found: {len(dividends)}")
    print()

    if dividends:
        print("| Ex-Dividend Date | Dividend Amount |")
        print("|------------------|-----------------|")
        for date, amount in dividends:
            print(f"| {date.strftime('%Y-%m-%d')}       | ${amount:>14.4f} |")

        total_div = sum(d[1] for d in dividends)
        print(f"\nTotal Dividends (1Y): ${total_div:.4f}")
    else:
        print("No dividends found in the period.")


def fetch_stock_splits(symbol: str = "TSLA"):
    """Fetch historical data including stock splits."""
    print("\n" + "=" * 60)
    print(f"Stock Split History for {symbol} (Max)")
    print("=" * 60)

    client = YFinanceClient()
    history = client.get_historical_data(symbol, period="max", interval="1d")

    splits = [(h.date, h.stock_splits) for h in history.history if h.stock_splits and h.stock_splits > 0]

    print(f"\nTotal data points: {len(history.history)}")
    print(f"Stock splits found: {len(splits)}")
    print()

    if splits:
        print("| Split Date  | Split Ratio |")
        print("|-------------|-------------|")
        for date, ratio in splits:
            print(f"| {date.strftime('%Y-%m-%d')} | {ratio:>11.2f} |")
    else:
        print("No stock splits found.")


def compare_indian_stocks_performance():
    """Compare performance of Indian stocks."""
    print("\n" + "=" * 60)
    print("Indian Stocks Performance (1 Month)")
    print("=" * 60)

    symbols = ["RELIANCE.NS", "TCS.NS", "INFY.NS", "HDFCBANK.NS", "TATAMOTORS.NS"]
    client = YFinanceClient()

    print("\n| Symbol        | Start (INR) | End (INR)   | Return % |")
    print("|---------------|-------------|-------------|----------|")

    for symbol in symbols:
        try:
            history = client.get_historical_data(symbol, period="1mo", interval="1d")

            if not history.history:
                print(f"| {symbol:<13} | No data available |")
                continue

            start_price = history.history[0].open
            end_price = history.history[-1].close
            ret = ((end_price - start_price) / start_price) * 100

            short_symbol = symbol.replace(".NS", "")
            print(f"| {short_symbol:<13} | {start_price:>11,.2f} | {end_price:>11,.2f} | {ret:>+7.2f}% |")
        except Exception as e:
            print(f"| {symbol:<13} | Error: {str(e)[:30]} |")


def fetch_weekly_data(symbol: str = "SPY"):
    """Fetch weekly candlestick data."""
    print("\n" + "=" * 60)
    print(f"Weekly Data for {symbol} (6 Months)")
    print("=" * 60)

    client = YFinanceClient()
    history = client.get_historical_data(symbol, period="6mo", interval="1wk")

    print(f"\nData points: {len(history.history)}")
    print()

    print("| Week Ending | Open     | High     | Low      | Close    | Change % |")
    print("|-------------|----------|----------|----------|----------|----------|")

    prev_close = None
    for h in history.history[-12:]:  # Show last 12 weeks
        date_str = h.date.strftime('%Y-%m-%d')
        change_pct = ((h.close - prev_close) / prev_close * 100) if prev_close else 0
        change_str = f"{change_pct:>+7.2f}%" if prev_close else "    -   "
        print(f"| {date_str}  | {h.open:>8.2f} | {h.high:>8.2f} | {h.low:>8.2f} | {h.close:>8.2f} | {change_str} |")
        prev_close = h.close


if __name__ == "__main__":
    # Run all examples
    fetch_recent_history("AAPL")
    fetch_intraday_data("AAPL")
    fetch_monthly_data("MSFT")
    fetch_custom_date_range("GOOGL")
    calculate_price_statistics("NVDA")
    compare_stock_performance()
    fetch_dividend_history("JNJ")
    fetch_stock_splits("TSLA")
    compare_indian_stocks_performance()
    fetch_weekly_data("SPY")
