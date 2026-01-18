"""Examples for using the Advances/Declines (Market Breadth) APIs.

This script demonstrates how to:
- Fetch advancing and declining stocks
- Get market breadth statistics
- Calculate advance/decline ratio
- Analyze market sentiment
- Get top gainers and losers
"""

from tools.nse_india.client import NSEIndiaClient


def fetch_advances():
    """Fetch advancing stocks with market breadth data."""
    print("=" * 60)
    print("Advancing Stocks")
    print("=" * 60)

    client = NSEIndiaClient()

    response = client.get_advances()

    print(f"Timestamp: {response.timestamp}")
    print()

    # Market breadth summary
    count = response.count
    print("Market Breadth:")
    print(f"  Advances: {count.advances:,}")
    print(f"  Declines: {count.declines:,}")
    print(f"  Unchanged: {count.unchanged:,}")
    print(f"  Total: {count.total:,}")
    print(f"  A/D Ratio: {count.advance_decline_ratio:.2f}")
    print(f"  Sentiment: {count.market_sentiment}")
    print()

    # Top gainers
    print(f"Top 10 Gainers ({len(response.stocks)} total advancing):")
    print("-" * 60)
    for stock in response.top_gainers[:10]:
        print(f"  {stock.symbol:12} {stock.pchange:>6.2f}%  {stock.last_price:>10.2f}  Vol: {stock.total_traded_volume:>10.2f}L")

    client.close()


def fetch_declines():
    """Fetch declining stocks with market breadth data."""
    print("\n" + "=" * 60)
    print("Declining Stocks")
    print("=" * 60)

    client = NSEIndiaClient()

    response = client.get_declines()

    print(f"Timestamp: {response.timestamp}")
    print()

    # Top losers
    print(f"Top 10 Losers ({len(response.stocks)} total declining):")
    print("-" * 60)
    for stock in response.top_losers[:10]:
        print(f"  {stock.symbol:12} {stock.pchange:>6.2f}%  {stock.last_price:>10.2f}  Vol: {stock.total_traded_volume:>10.2f}L")

    client.close()


def analyze_market_breadth():
    """Analyze overall market breadth."""
    print("\n" + "=" * 60)
    print("Market Breadth Analysis")
    print("=" * 60)

    client = NSEIndiaClient()

    snapshot = client.get_market_breadth_snapshot()

    print(f"Timestamp: {snapshot.timestamp}")
    print()

    count = snapshot.count
    print("Summary:")
    print(f"  Advancing Stocks: {count.advances:,} ({count.advance_percentage:.1f}%)")
    print(f"  Declining Stocks: {count.declines:,} ({count.decline_percentage:.1f}%)")
    print(f"  Unchanged Stocks: {count.unchanged:,}")
    print(f"  Total Stocks: {count.total:,}")
    print()

    print(f"Advance/Decline Ratio: {count.advance_decline_ratio:.2f}")
    print(f"Market Sentiment: {count.market_sentiment}")
    print()

    # Interpretation
    ratio = count.advance_decline_ratio
    if ratio > 2:
        interpretation = "Very strong buying pressure - most stocks are advancing"
    elif ratio > 1.5:
        interpretation = "Strong buying pressure - significantly more advances than declines"
    elif ratio > 1:
        interpretation = "Moderate buying pressure - more advances than declines"
    elif ratio > 0.67:
        interpretation = "Neutral market - balanced advances and declines"
    elif ratio > 0.5:
        interpretation = "Moderate selling pressure - more declines than advances"
    else:
        interpretation = "Strong selling pressure - significantly more declines than advances"

    print(f"Interpretation: {interpretation}")

    client.close()


def get_top_movers():
    """Get top gainers and losers."""
    print("\n" + "=" * 60)
    print("Top Market Movers")
    print("=" * 60)

    client = NSEIndiaClient()

    # Top gainers
    gainers = client.get_top_gainers(limit=15)
    print("\nTop 15 Gainers:")
    print("-" * 60)
    print(f"{'Symbol':12} {'Change%':>8} {'LTP':>10} {'Value (Cr)':>12} {'M.Cap (Cr)':>12}")
    print("-" * 60)
    for stock in gainers:
        print(f"{stock.symbol:12} {stock.pchange:>+7.2f}% {stock.last_price:>10.2f} {stock.total_traded_value:>12.2f} {stock.total_market_cap:>12.0f}")

    # Top losers
    losers = client.get_top_losers(limit=15)
    print("\nTop 15 Losers:")
    print("-" * 60)
    print(f"{'Symbol':12} {'Change%':>8} {'LTP':>10} {'Value (Cr)':>12} {'M.Cap (Cr)':>12}")
    print("-" * 60)
    for stock in losers:
        print(f"{stock.symbol:12} {stock.pchange:>+7.2f}% {stock.last_price:>10.2f} {stock.total_traded_value:>12.2f} {stock.total_market_cap:>12.0f}")

    client.close()


def check_symbol_status(symbols: list[str] | None = None):
    """Check advance/decline status for specific symbols."""
    print("\n" + "=" * 60)
    print("Symbol Status Check")
    print("=" * 60)

    if symbols is None:
        symbols = ["RELIANCE", "TCS", "HDFCBANK", "INFY", "ICICIBANK"]

    client = NSEIndiaClient()

    print(f"\n{'Symbol':12} {'Status':10} {'Change%':>8} {'LTP':>10} {'Volume (L)':>12}")
    print("-" * 60)

    for symbol in symbols:
        stock = client.get_symbol_advance_decline_data(symbol)
        if stock:
            status = "Advancing" if stock.is_advancing else "Declining" if stock.is_declining else "Unchanged"
            print(f"{stock.symbol:12} {status:10} {stock.pchange:>+7.2f}% {stock.last_price:>10.2f} {stock.total_traded_volume:>12.2f}")
        else:
            print(f"{symbol:12} {'N/A':10} {'N/A':>8} {'N/A':>10} {'N/A':>12}")

    client.close()


def get_ad_ratio():
    """Get advance/decline ratio and sentiment."""
    print("\n" + "=" * 60)
    print("Advance/Decline Ratio")
    print("=" * 60)

    client = NSEIndiaClient()

    data = client.get_advance_decline_ratio()

    print(f"\nAdvances: {data['advances']:,}")
    print(f"Declines: {data['declines']:,}")
    print(f"Unchanged: {data['unchanged']:,}")
    print(f"Total: {data['total']:,}")
    print()
    print(f"A/D Ratio: {data['ratio']:.2f}")
    print(f"Advance %: {data['advance_percentage']:.1f}%")
    print(f"Decline %: {data['decline_percentage']:.1f}%")
    print(f"Sentiment: {data['sentiment']}")

    client.close()


def compare_by_value_vs_volume():
    """Compare advances sorted by value vs volume."""
    print("\n" + "=" * 60)
    print("Advances: By Value vs By Volume")
    print("=" * 60)

    client = NSEIndiaClient()

    response = client.get_advances()

    # By Value
    print("\nTop 10 by Traded Value:")
    print("-" * 60)
    for stock in response.top_by_value[:10]:
        print(f"  {stock.symbol:12} Value: Rs.{stock.total_traded_value:>10.2f} Cr  Change: {stock.pchange:>+6.2f}%")

    # By Volume
    print("\nTop 10 by Traded Volume:")
    print("-" * 60)
    for stock in response.top_by_volume[:10]:
        print(f"  {stock.symbol:12} Vol: {stock.total_traded_volume:>10.2f} L  Change: {stock.pchange:>+6.2f}%")

    client.close()


def intraday_breadth_check():
    """Quick market breadth check for intraday analysis."""
    print("\n" + "=" * 60)
    print("Intraday Market Breadth")
    print("=" * 60)

    client = NSEIndiaClient()

    data = client.get_advance_decline_ratio()

    # Visual representation
    advances_pct = data['advance_percentage']
    declines_pct = data['decline_percentage']

    # Create a simple bar
    bar_width = 40
    advance_bar = int(advances_pct / 100 * bar_width)
    decline_bar = int(declines_pct / 100 * bar_width)

    print(f"\nAdvances ({data['advances']:,}): [{'=' * advance_bar}{' ' * (bar_width - advance_bar)}] {advances_pct:.1f}%")
    print(f"Declines ({data['declines']:,}): [{'=' * decline_bar}{' ' * (bar_width - decline_bar)}] {declines_pct:.1f}%")
    print()
    print(f"A/D Ratio: {data['ratio']:.2f}")
    print(f"Signal: {data['sentiment']}")

    # Trading interpretation
    if data['ratio'] > 1.5:
        signal = "BUY - Strong breadth supports bullish view"
    elif data['ratio'] > 1.0:
        signal = "NEUTRAL-BULLISH - Breadth is positive"
    elif data['ratio'] > 0.67:
        signal = "NEUTRAL - Mixed breadth, be cautious"
    elif data['ratio'] > 0.5:
        signal = "NEUTRAL-BEARISH - Breadth is negative"
    else:
        signal = "SELL - Weak breadth supports bearish view"

    print(f"Trading Signal: {signal}")

    client.close()


if __name__ == "__main__":
    # Run all examples
    fetch_advances()
    fetch_declines()
    analyze_market_breadth()
    get_top_movers()
    check_symbol_status()
    get_ad_ratio()
    compare_by_value_vs_volume()
    intraday_breadth_check()
