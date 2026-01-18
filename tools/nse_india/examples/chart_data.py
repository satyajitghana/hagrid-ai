"""Examples for fetching chart/historical data from NSE India.

This script demonstrates how to:
- Search for chart symbols (equity, futures, options)
- Fetch daily OHLCV data
- Fetch intraday OHLCV data
- Get index chart data
- Get futures chart data
- Analyze price trends and patterns
"""

from datetime import datetime

from tools.nse_india import NSEIndiaClient


def search_symbols(query: str = "RELIANCE"):
    """Search for chart symbols by name."""
    print("=" * 60)
    print(f"Symbol Search: '{query}'")
    print("=" * 60)

    client = NSEIndiaClient()

    response = client.search_chart_symbols(query)

    print(f"\nFound {response.total_count} symbols")
    print(f"\n{'Symbol':<25} {'Scripcode':<12} {'Type':<10} {'Description':<30}")
    print("-" * 80)

    for sym in response.symbols[:15]:
        print(f"{sym.symbol:<25} {sym.scripcode:<12} {sym.symbol_type:<10} {sym.description[:28]:<30}")

    if response.total_count > 15:
        print(f"\n... and {response.total_count - 15} more")

    # Show breakdown by type
    equity = response.get_equity_symbols()
    futures = response.get_futures_symbols()
    options = response.get_options_symbols()

    print(f"\n--- Breakdown by Type ---")
    print(f"  Equity: {len(equity)}")
    print(f"  Futures: {len(futures)}")
    print(f"  Options: {len(options)}")

    client.close()
    return response


def get_daily_chart_data(symbol: str = "RELIANCE", days: int = 30):
    """Get daily OHLCV chart data."""
    print("\n" + "=" * 60)
    print(f"Daily Chart: {symbol} (Last {days} days)")
    print("=" * 60)

    client = NSEIndiaClient()

    response = client.get_daily_chart(symbol, days=days)

    if not response.candles:
        print(f"No data found for {symbol}")
        client.close()
        return None

    print(f"\nSymbol: {response.symbol}")
    print(f"Total Candles: {response.total_candles}")
    print(f"Period: {response.start_time.strftime('%Y-%m-%d')} to {response.end_time.strftime('%Y-%m-%d')}")
    print(f"Period High: {response.period_high:.2f}")
    print(f"Period Low: {response.period_low:.2f}")
    print(f"Period Change: {response.period_change:.2f} ({response.period_change_percent:.2f}%)")
    print(f"Total Volume: {response.total_volume:,}")

    # Show last 10 candles
    print(f"\n--- Last 10 Candles ---")
    print(f"{'Date':<12} {'Open':<10} {'High':<10} {'Low':<10} {'Close':<10} {'Volume':<12} {'Change':<8}")
    print("-" * 75)

    for candle in response.get_latest_candles(10):
        change_str = f"{candle.change_percent:+.2f}%"
        print(
            f"{candle.time.strftime('%Y-%m-%d'):<12} "
            f"{candle.open:<10.2f} "
            f"{candle.high:<10.2f} "
            f"{candle.low:<10.2f} "
            f"{candle.close:<10.2f} "
            f"{candle.volume:<12,} "
            f"{change_str:<8}"
        )

    client.close()
    return response


def get_intraday_data(symbol: str = "RELIANCE", interval: int = 5):
    """Get intraday OHLCV chart data."""
    print("\n" + "=" * 60)
    print(f"Intraday Chart: {symbol} ({interval}-min candles)")
    print("=" * 60)

    client = NSEIndiaClient()

    response = client.get_intraday_chart(symbol, interval=interval, days=1)

    if not response.candles:
        print(f"No intraday data found for {symbol}")
        client.close()
        return None

    print(f"\nSymbol: {response.symbol}")
    print(f"Interval: {response.interval} minutes")
    print(f"Total Candles: {response.total_candles}")

    if response.start_time and response.end_time:
        print(f"Time Range: {response.start_time.strftime('%H:%M')} to {response.end_time.strftime('%H:%M')}")

    print(f"Day High: {response.period_high:.2f}")
    print(f"Day Low: {response.period_low:.2f}")

    # Calculate VWAP
    vwap = response.get_vwap()
    if vwap:
        print(f"VWAP: {vwap:.2f}")

    # Show last 15 candles
    print(f"\n--- Last 15 Candles ---")
    print(f"{'Time':<10} {'Open':<10} {'High':<10} {'Low':<10} {'Close':<10} {'Volume':<10}")
    print("-" * 65)

    for candle in response.get_latest_candles(15):
        print(
            f"{candle.time.strftime('%H:%M'):<10} "
            f"{candle.open:<10.2f} "
            f"{candle.high:<10.2f} "
            f"{candle.low:<10.2f} "
            f"{candle.close:<10.2f} "
            f"{candle.volume:<10,}"
        )

    client.close()
    return response


def get_index_daily_chart(index_name: str = "NIFTY 50", days: int = 30):
    """Get daily chart data for an index."""
    print("\n" + "=" * 60)
    print(f"Index Chart: {index_name} (Last {days} days)")
    print("=" * 60)

    client = NSEIndiaClient()

    response = client.get_index_chart(index_name, chart_type="D", days=days)

    if not response.candles:
        print(f"No data found for index {index_name}")
        client.close()
        return None

    print(f"\nSymbol: {response.symbol}")
    print(f"Total Candles: {response.total_candles}")
    print(f"Period High: {response.period_high:.2f}")
    print(f"Period Low: {response.period_low:.2f}")
    print(f"Period Change: {response.period_change:.2f} ({response.period_change_percent:.2f}%)")

    # Trend analysis
    bullish = len(response.get_bullish_candles())
    bearish = len(response.get_bearish_candles())
    total = response.total_candles

    print(f"\n--- Trend Analysis ---")
    print(f"  Bullish Days: {bullish} ({bullish/total*100:.1f}%)")
    print(f"  Bearish Days: {bearish} ({bearish/total*100:.1f}%)")

    # Show last 10 candles
    print(f"\n--- Last 10 Trading Days ---")
    print(f"{'Date':<12} {'Open':<10} {'High':<10} {'Low':<10} {'Close':<10} {'Change':<10}")
    print("-" * 65)

    for candle in response.get_latest_candles(10):
        trend = "↑" if candle.is_bullish else "↓"
        print(
            f"{candle.time.strftime('%Y-%m-%d'):<12} "
            f"{candle.open:<10.2f} "
            f"{candle.high:<10.2f} "
            f"{candle.low:<10.2f} "
            f"{candle.close:<10.2f} "
            f"{trend} {candle.change_percent:+.2f}%"
        )

    client.close()
    return response


def get_futures_data(symbol: str = "NIFTY", days: int = 30):
    """Get chart data for futures contracts."""
    print("\n" + "=" * 60)
    print(f"Futures Chart: {symbol} (Last {days} days)")
    print("=" * 60)

    client = NSEIndiaClient()

    response = client.get_futures_chart(symbol, chart_type="D", days=days)

    if not response.candles:
        print(f"No futures data found for {symbol}")
        client.close()
        return None

    print(f"\nSymbol: {response.symbol}")
    print(f"Type: {response.symbol_type}")
    print(f"Total Candles: {response.total_candles}")
    print(f"Period High: {response.period_high:.2f}")
    print(f"Period Low: {response.period_low:.2f}")

    # Show last 10 candles
    print(f"\n--- Last 10 Sessions ---")
    print(f"{'Date':<12} {'Open':<10} {'High':<10} {'Low':<10} {'Close':<10} {'Volume':<12}")
    print("-" * 70)

    for candle in response.get_latest_candles(10):
        print(
            f"{candle.time.strftime('%Y-%m-%d'):<12} "
            f"{candle.open:<10.2f} "
            f"{candle.high:<10.2f} "
            f"{candle.low:<10.2f} "
            f"{candle.close:<10.2f} "
            f"{candle.volume:<12,}"
        )

    client.close()
    return response


def analyze_candle_patterns(symbol: str = "RELIANCE", days: int = 60):
    """Analyze basic candle patterns."""
    print("\n" + "=" * 60)
    print(f"Candle Pattern Analysis: {symbol}")
    print("=" * 60)

    client = NSEIndiaClient()

    response = client.get_daily_chart(symbol, days=days)

    if not response.candles:
        print(f"No data found for {symbol}")
        client.close()
        return

    print(f"\nAnalyzing {response.total_candles} candles")

    # Basic statistics
    bullish = response.get_bullish_candles()
    bearish = response.get_bearish_candles()

    print(f"\n--- Candle Statistics ---")
    print(f"  Bullish Candles: {len(bullish)} ({len(bullish)/len(response.candles)*100:.1f}%)")
    print(f"  Bearish Candles: {len(bearish)} ({len(bearish)/len(response.candles)*100:.1f}%)")

    # Average body size
    avg_body = sum(c.body_size for c in response.candles) / len(response.candles)
    avg_range = sum(c.range for c in response.candles) / len(response.candles)

    print(f"\n--- Average Measurements ---")
    print(f"  Average Body Size: {avg_body:.2f}")
    print(f"  Average Range (H-L): {avg_range:.2f}")

    # Find largest moves
    candles_sorted_by_change = sorted(response.candles, key=lambda c: abs(c.change_percent), reverse=True)

    print(f"\n--- Largest Daily Moves ---")
    print(f"{'Date':<12} {'Change %':<10} {'Type':<10} {'Close':<10}")
    print("-" * 45)

    for candle in candles_sorted_by_change[:5]:
        trend = "Bullish" if candle.is_bullish else "Bearish"
        print(
            f"{candle.time.strftime('%Y-%m-%d'):<12} "
            f"{candle.change_percent:+.2f}%{'':<4} "
            f"{trend:<10} "
            f"{candle.close:<10.2f}"
        )

    # Volume analysis
    avg_volume = response.average_volume
    high_volume_days = [c for c in response.candles if c.volume > avg_volume * 1.5]

    print(f"\n--- Volume Analysis ---")
    print(f"  Average Volume: {avg_volume:,.0f}")
    print(f"  High Volume Days (>1.5x avg): {len(high_volume_days)}")

    client.close()


def compare_multiple_symbols(symbols: list[str] | None = None, days: int = 30):
    """Compare chart data for multiple symbols."""
    if symbols is None:
        symbols = ["RELIANCE", "TCS", "INFY", "HDFCBANK"]

    print("\n" + "=" * 60)
    print(f"Multi-Symbol Comparison (Last {days} days)")
    print("=" * 60)

    client = NSEIndiaClient()

    results = []
    for symbol in symbols:
        response = client.get_daily_chart(symbol, days=days)
        if response.candles:
            results.append({
                "symbol": symbol,
                "response": response,
                "change": response.period_change_percent,
                "high": response.period_high,
                "low": response.period_low,
                "volume": response.total_volume,
            })

    if not results:
        print("No data found for any symbols")
        client.close()
        return

    # Sort by performance
    results.sort(key=lambda x: x["change"], reverse=True)

    print(f"\n{'Symbol':<12} {'Change %':<12} {'High':<12} {'Low':<12} {'Volume':<15}")
    print("-" * 65)

    for r in results:
        print(
            f"{r['symbol']:<12} "
            f"{r['change']:+.2f}%{'':<6} "
            f"{r['high']:<12.2f} "
            f"{r['low']:<12.2f} "
            f"{r['volume']:,}"
        )

    # Best and worst performers
    print(f"\n--- Performance Summary ---")
    print(f"  Best Performer: {results[0]['symbol']} ({results[0]['change']:+.2f}%)")
    print(f"  Worst Performer: {results[-1]['symbol']} ({results[-1]['change']:+.2f}%)")

    client.close()


if __name__ == "__main__":
    search_symbols("RELIANCE")
    get_daily_chart_data("RELIANCE", days=30)
    get_intraday_data("RELIANCE", interval=5)
    get_index_daily_chart("NIFTY 50", days=30)
    # get_futures_data("NIFTY", days=30)  # Uncomment to test futures
    analyze_candle_patterns("TCS", days=60)
    compare_multiple_symbols(["RELIANCE", "TCS", "INFY", "HDFCBANK"], days=30)
