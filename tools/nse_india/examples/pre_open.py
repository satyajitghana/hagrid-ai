"""Examples for using the Pre-Open Market APIs.

This script demonstrates how to:
- Fetch pre-open market data for NIFTY 50, Bank NIFTY, and F&O securities
- Analyze pre-open sentiment and market breadth
- Identify stocks with significant gaps
- Find stocks with buy/sell pressure based on order imbalance
- Get top gainers and losers in pre-open session

Note: Pre-open session runs from 9:00 AM to 9:15 AM IST.
Outside this window, data may be stale or unavailable.
"""

from tools.nse_india.client import NSEIndiaClient


def fetch_nifty_pre_open():
    """Fetch NIFTY 50 pre-open data."""
    print("=" * 60)
    print("NIFTY 50 Pre-Open Data")
    print("=" * 60)

    client = NSEIndiaClient()

    response = client.get_nifty_pre_open()

    print(f"Total Stocks: {response.total_stocks}")
    print(f"Advances: {response.advances}")
    print(f"Declines: {response.declines}")
    print(f"Unchanged: {response.unchanged}")
    print(f"A/D Ratio: {response.advance_decline_ratio:.2f}")
    print(f"Sentiment: {response.market_sentiment}")
    print()

    # Top gainers
    print("Top 5 Gainers:")
    print("-" * 60)
    print(f"{'Symbol':12} {'IEP':>10} {'Change%':>8} {'Gap%':>8} {'Buy/Sell':>10}")
    print("-" * 60)
    for stock in response.top_gainers[:5]:
        print(
            f"{stock.symbol:12} "
            f"{stock.iep:>10.2f} "
            f"{stock.pchange:>+7.2f}% "
            f"{stock.metadata.gap_percentage:>+7.2f}% "
            f"{stock.buy_sell_ratio:>10.2f}"
        )

    print()

    # Top losers
    print("Top 5 Losers:")
    print("-" * 60)
    for stock in response.top_losers[:5]:
        print(
            f"{stock.symbol:12} "
            f"{stock.iep:>10.2f} "
            f"{stock.pchange:>+7.2f}% "
            f"{stock.metadata.gap_percentage:>+7.2f}% "
            f"{stock.buy_sell_ratio:>10.2f}"
        )

    client.close()


def fetch_bank_nifty_pre_open():
    """Fetch Bank NIFTY pre-open data."""
    print("\n" + "=" * 60)
    print("Bank NIFTY Pre-Open Data")
    print("=" * 60)

    client = NSEIndiaClient()

    response = client.get_bank_nifty_pre_open()

    print(f"Total Stocks: {response.total_stocks}")
    print(f"Advances: {response.advances} | Declines: {response.declines}")
    print(f"Sentiment: {response.market_sentiment}")
    print()

    print("All Stocks:")
    print("-" * 60)
    print(f"{'Symbol':12} {'IEP':>10} {'Change%':>8} {'Prev Close':>12} {'Buy Qty':>10} {'Sell Qty':>10}")
    print("-" * 60)
    for stock in sorted(response.data, key=lambda x: x.pchange, reverse=True):
        print(
            f"{stock.symbol:12} "
            f"{stock.iep:>10.2f} "
            f"{stock.pchange:>+7.2f}% "
            f"{stock.metadata.previous_close:>12.2f} "
            f"{stock.total_buy_quantity:>10,} "
            f"{stock.total_sell_quantity:>10,}"
        )

    client.close()


def analyze_pre_open_sentiment():
    """Analyze pre-open market sentiment."""
    print("\n" + "=" * 60)
    print("Pre-Open Market Sentiment Analysis")
    print("=" * 60)

    client = NSEIndiaClient()

    # Get sentiment for different indices
    for index in ["NIFTY", "BANKNIFTY", "FO"]:
        sentiment = client.get_pre_open_sentiment(index)
        print(f"\n{index}:")
        print(f"  Advances: {sentiment['advances']} ({sentiment['advances']/sentiment['total']*100:.1f}%)")
        print(f"  Declines: {sentiment['declines']} ({sentiment['declines']/sentiment['total']*100:.1f}%)")
        print(f"  A/D Ratio: {sentiment['advance_decline_ratio']:.2f}")
        print(f"  Sentiment: {sentiment['sentiment']}")
        print(f"  Gapping Up: {sentiment['gapping_up_count']}")
        print(f"  Gapping Down: {sentiment['gapping_down_count']}")
        print(f"  Buy Pressure: {sentiment['buy_pressure_count']} stocks")
        print(f"  Sell Pressure: {sentiment['sell_pressure_count']} stocks")

    client.close()


def find_gap_stocks():
    """Find stocks with significant gaps in pre-open."""
    print("\n" + "=" * 60)
    print("Stocks with Significant Gaps (>= 1%)")
    print("=" * 60)

    client = NSEIndiaClient()

    gaps = client.get_pre_open_gaps("NIFTY", min_gap_pct=1.0)

    print("\nGapping UP:")
    print("-" * 60)
    if gaps["gap_up"]:
        print(f"{'Symbol':12} {'IEP':>10} {'Prev Close':>12} {'Gap%':>8}")
        print("-" * 60)
        for stock in gaps["gap_up"]:
            print(
                f"{stock.symbol:12} "
                f"{stock.iep:>10.2f} "
                f"{stock.metadata.previous_close:>12.2f} "
                f"{stock.metadata.gap_percentage:>+7.2f}%"
            )
    else:
        print("  No significant gap-ups found")

    print("\nGapping DOWN:")
    print("-" * 60)
    if gaps["gap_down"]:
        print(f"{'Symbol':12} {'IEP':>10} {'Prev Close':>12} {'Gap%':>8}")
        print("-" * 60)
        for stock in gaps["gap_down"]:
            print(
                f"{stock.symbol:12} "
                f"{stock.iep:>10.2f} "
                f"{stock.metadata.previous_close:>12.2f} "
                f"{stock.metadata.gap_percentage:>+7.2f}%"
            )
    else:
        print("  No significant gap-downs found")

    client.close()


def analyze_order_imbalance():
    """Analyze buy/sell order imbalance in pre-open."""
    print("\n" + "=" * 60)
    print("Order Imbalance Analysis (Buy/Sell Pressure)")
    print("=" * 60)

    client = NSEIndiaClient()

    # Stocks with strong buy pressure
    buy_pressure = client.get_pre_open_buy_pressure("NIFTY", min_ratio=1.5)
    print("\nStrong Buy Pressure (Buy/Sell >= 1.5):")
    print("-" * 60)
    if buy_pressure:
        print(f"{'Symbol':12} {'Buy Qty':>12} {'Sell Qty':>12} {'Ratio':>8} {'IEP':>10}")
        print("-" * 60)
        for stock in buy_pressure[:10]:
            print(
                f"{stock.symbol:12} "
                f"{stock.total_buy_quantity:>12,} "
                f"{stock.total_sell_quantity:>12,} "
                f"{stock.buy_sell_ratio:>8.2f} "
                f"{stock.iep:>10.2f}"
            )
    else:
        print("  No stocks with strong buy pressure found")

    # Stocks with strong sell pressure
    sell_pressure = client.get_pre_open_sell_pressure("NIFTY", max_ratio=0.67)
    print("\nStrong Sell Pressure (Buy/Sell <= 0.67):")
    print("-" * 60)
    if sell_pressure:
        print(f"{'Symbol':12} {'Buy Qty':>12} {'Sell Qty':>12} {'Ratio':>8} {'IEP':>10}")
        print("-" * 60)
        for stock in sell_pressure[:10]:
            print(
                f"{stock.symbol:12} "
                f"{stock.total_buy_quantity:>12,} "
                f"{stock.total_sell_quantity:>12,} "
                f"{stock.buy_sell_ratio:>8.2f} "
                f"{stock.iep:>10.2f}"
            )
    else:
        print("  No stocks with strong sell pressure found")

    client.close()


def check_symbol_pre_open(symbols: list[str] | None = None):
    """Check pre-open data for specific symbols."""
    print("\n" + "=" * 60)
    print("Symbol Pre-Open Data")
    print("=" * 60)

    if symbols is None:
        symbols = ["RELIANCE", "TCS", "HDFCBANK", "INFY", "ICICIBANK"]

    client = NSEIndiaClient()

    print(f"\n{'Symbol':12} {'IEP':>10} {'Change%':>8} {'Gap%':>8} {'Buy Qty':>12} {'Sell Qty':>12} {'Pressure':<15}")
    print("-" * 90)

    for symbol in symbols:
        stock = client.get_symbol_pre_open_data(symbol, "NIFTY")
        if stock:
            pressure = stock.detail.pre_open_market.buy_pressure
            print(
                f"{stock.symbol:12} "
                f"{stock.iep:>10.2f} "
                f"{stock.pchange:>+7.2f}% "
                f"{stock.metadata.gap_percentage:>+7.2f}% "
                f"{stock.total_buy_quantity:>12,} "
                f"{stock.total_sell_quantity:>12,} "
                f"{pressure:<15}"
            )
        else:
            print(f"{symbol:12} Not found in NIFTY pre-open data")

    client.close()


def get_pre_open_order_book(symbol: str = "RELIANCE"):
    """Get detailed order book for a stock in pre-open."""
    print("\n" + "=" * 60)
    print(f"Pre-Open Order Book: {symbol}")
    print("=" * 60)

    client = NSEIndiaClient()

    stock = client.get_symbol_pre_open_data(symbol, "NIFTY")
    if not stock:
        print(f"Symbol {symbol} not found in NIFTY pre-open data")
        client.close()
        return

    print(f"\nSymbol: {stock.symbol}")
    print(f"IEP: {stock.iep:.2f}")
    print(f"Previous Close: {stock.metadata.previous_close:.2f}")
    print(f"Gap: {stock.metadata.gap_percentage:+.2f}%")
    print()

    pre_open = stock.detail.pre_open_market
    print(f"Total Buy Quantity: {pre_open.total_buy_quantity:,}")
    print(f"Total Sell Quantity: {pre_open.total_sell_quantity:,}")
    print(f"Buy/Sell Ratio: {pre_open.buy_sell_ratio:.2f}")
    print(f"Pressure: {pre_open.buy_pressure}")
    print()

    # Order book
    print("Order Book:")
    print("-" * 50)
    print(f"{'Price':>12} {'Buy Qty':>12} {'Sell Qty':>12} {'IEP?':>6}")
    print("-" * 50)
    for order in pre_open.preopen:
        iep_marker = "*" if order.iep else ""
        print(f"{order.price:>12.2f} {order.buy_qty:>12,} {order.sell_qty:>12,} {iep_marker:>6}")

    client.close()


def compare_indices_pre_open():
    """Compare pre-open data across indices."""
    print("\n" + "=" * 60)
    print("Pre-Open Comparison Across Indices")
    print("=" * 60)

    client = NSEIndiaClient()

    snapshot = client.get_pre_open_snapshot()

    print(f"\n{'Index':15} {'Stocks':>8} {'Advances':>10} {'Declines':>10} {'A/D Ratio':>10} {'Sentiment':>15}")
    print("-" * 80)

    if snapshot.nifty_50:
        n = snapshot.nifty_50
        print(f"{'NIFTY 50':15} {n.total_stocks:>8} {n.advances:>10} {n.declines:>10} {n.advance_decline_ratio:>10.2f} {n.market_sentiment:>15}")

    if snapshot.nifty_bank:
        n = snapshot.nifty_bank
        print(f"{'BANK NIFTY':15} {n.total_stocks:>8} {n.advances:>10} {n.declines:>10} {n.advance_decline_ratio:>10.2f} {n.market_sentiment:>15}")

    if snapshot.fo_securities:
        n = snapshot.fo_securities
        print(f"{'F&O Securities':15} {n.total_stocks:>8} {n.advances:>10} {n.declines:>10} {n.advance_decline_ratio:>10.2f} {n.market_sentiment:>15}")

    client.close()


def pre_open_trading_signals():
    """Generate trading signals from pre-open data."""
    print("\n" + "=" * 60)
    print("Pre-Open Trading Signals")
    print("=" * 60)

    client = NSEIndiaClient()

    response = client.get_nifty_pre_open()

    # Overall market signal
    print("\n📊 Market Overview:")
    ratio = response.advance_decline_ratio
    if ratio > 1.5:
        print("  Signal: BULLISH - Strong buying interest in pre-open")
    elif ratio > 1.0:
        print("  Signal: MILDLY BULLISH - More advances than declines")
    elif ratio > 0.67:
        print("  Signal: NEUTRAL - Mixed sentiment")
    elif ratio > 0.5:
        print("  Signal: MILDLY BEARISH - More declines than advances")
    else:
        print("  Signal: BEARISH - Strong selling pressure in pre-open")

    # Gap opportunities
    gaps = client.get_pre_open_gaps("NIFTY", min_gap_pct=2.0)
    if gaps["gap_up"]:
        print("\n📈 Gap Up Opportunities (>2%):")
        for stock in gaps["gap_up"][:3]:
            print(f"  - {stock.symbol}: {stock.metadata.gap_percentage:+.2f}% gap")

    if gaps["gap_down"]:
        print("\n📉 Gap Down Stocks (>2%):")
        for stock in gaps["gap_down"][:3]:
            print(f"  - {stock.symbol}: {stock.metadata.gap_percentage:+.2f}% gap")

    # Order flow signals
    buy_pressure = client.get_pre_open_buy_pressure("NIFTY", min_ratio=2.0)
    if buy_pressure:
        print("\n💪 Strong Buy Pressure (Buy/Sell > 2):")
        for stock in buy_pressure[:3]:
            print(f"  - {stock.symbol}: {stock.buy_sell_ratio:.2f}x buy/sell ratio")

    sell_pressure = client.get_pre_open_sell_pressure("NIFTY", max_ratio=0.5)
    if sell_pressure:
        print("\n⚠️ Strong Sell Pressure (Buy/Sell < 0.5):")
        for stock in sell_pressure[:3]:
            print(f"  - {stock.symbol}: {stock.buy_sell_ratio:.2f}x buy/sell ratio")

    client.close()


if __name__ == "__main__":
    # Run all examples
    fetch_nifty_pre_open()
    fetch_bank_nifty_pre_open()
    analyze_pre_open_sentiment()
    find_gap_stocks()
    analyze_order_imbalance()
    check_symbol_pre_open()
    get_pre_open_order_book("RELIANCE")
    compare_indices_pre_open()
    pre_open_trading_signals()
