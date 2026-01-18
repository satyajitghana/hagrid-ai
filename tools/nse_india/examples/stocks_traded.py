"""Examples for fetching stocks traded data from NSE India live analysis.

This script demonstrates how to:
- Fetch all stocks traded with market breadth
- Get top traded stocks by value and volume
- Analyze market turnover and activity
- Filter by market cap categories (large, mid, small cap)
"""

from tools.nse_india import NSEIndiaClient


def fetch_market_overview():
    """Fetch market overview with breadth statistics."""
    print("=" * 60)
    print("Market Overview - Stocks Traded")
    print("=" * 60)

    client = NSEIndiaClient()

    response = client.get_stocks_traded()

    print(f"\n--- Market Breadth ---")
    print(f"Advances: {response.count.advances}")
    print(f"Declines: {response.count.declines}")
    print(f"Unchanged: {response.count.unchanged}")
    print(f"Total Stocks: {response.count.total}")
    print(f"A/D Ratio: {response.count.advance_decline_ratio:.2f}" if response.count.advance_decline_ratio else "A/D Ratio: N/A")
    print(f"Breadth %: {response.count.breadth_percentage:.1f}%")

    print(f"\n--- Market Turnover ---")
    print(f"Total Traded Value: Rs. {response.total_traded_value_cr:,.2f} Cr")
    print(f"Total Market Cap: Rs. {response.total_market_cap_cr:,.2f} Cr")

    client.close()
    return response


def show_top_traded_by_value():
    """Show top traded stocks by value."""
    print("\n" + "=" * 60)
    print("Top Traded Stocks by Value")
    print("=" * 60)

    client = NSEIndiaClient()

    top_by_value = client.get_top_traded_by_value(limit=20)

    print(f"\n{'Symbol':<12} {'Last':>10} {'Change':>10} {'%Chg':>8} {'Value (Cr)':>12} {'MCap (Cr)':>14}")
    print("-" * 70)

    for stock in top_by_value:
        print(
            f"{stock.symbol:<12} {stock.last_price:>10.2f} {stock.change:>+10.2f} "
            f"{stock.pchange:>+7.2f}% {stock.total_traded_value:>12.2f} {stock.total_market_cap:>14,.0f}"
        )

    client.close()


def show_top_traded_by_volume():
    """Show top traded stocks by volume."""
    print("\n" + "=" * 60)
    print("Top Traded Stocks by Volume")
    print("=" * 60)

    client = NSEIndiaClient()

    top_by_volume = client.get_top_traded_by_volume(limit=20)

    print(f"\n{'Symbol':<12} {'Last':>10} {'%Chg':>8} {'Vol (Lakh)':>12} {'Value (Cr)':>12}")
    print("-" * 60)

    for stock in top_by_volume:
        print(
            f"{stock.symbol:<12} {stock.last_price:>10.2f} {stock.pchange:>+7.2f}% "
            f"{stock.total_traded_volume:>12.2f} {stock.total_traded_value:>12.2f}"
        )

    client.close()


def show_market_turnover():
    """Show market turnover statistics."""
    print("\n" + "=" * 60)
    print("Market Turnover Statistics")
    print("=" * 60)

    client = NSEIndiaClient()

    turnover = client.get_market_turnover()

    print(f"\n--- Breadth ---")
    print(f"Advances: {turnover['advances']}")
    print(f"Declines: {turnover['declines']}")
    print(f"Unchanged: {turnover['unchanged']}")
    print(f"Total: {turnover['total_stocks']}")

    print(f"\n--- Ratios ---")
    if turnover['advance_decline_ratio']:
        print(f"A/D Ratio: {turnover['advance_decline_ratio']:.2f}")
    print(f"Breadth %: {turnover['breadth_percentage']:.1f}%")

    print(f"\n--- Values ---")
    print(f"Total Traded Value: Rs. {turnover['total_traded_value_cr']:,.2f} Cr")
    print(f"Total Market Cap: Rs. {turnover['total_market_cap_cr']:,.2f} Cr")

    client.close()


def show_activity_by_cap():
    """Show trading activity by market cap category."""
    print("\n" + "=" * 60)
    print("Trading Activity by Market Cap")
    print("=" * 60)

    client = NSEIndiaClient()

    print("\n--- Large Caps (MCap > Rs. 50,000 Cr) ---")
    large_caps = client.get_large_cap_activity(limit=10)
    print(f"{'Symbol':<12} {'Last':>10} {'%Chg':>8} {'Value (Cr)':>12} {'MCap (Cr)':>14}")
    print("-" * 60)
    for stock in large_caps:
        print(
            f"{stock.symbol:<12} {stock.last_price:>10.2f} {stock.pchange:>+7.2f}% "
            f"{stock.total_traded_value:>12.2f} {stock.total_market_cap:>14,.0f}"
        )

    print("\n--- Mid Caps (MCap Rs. 10,000-50,000 Cr) ---")
    mid_caps = client.get_mid_cap_activity(limit=10)
    print(f"{'Symbol':<12} {'Last':>10} {'%Chg':>8} {'Value (Cr)':>12} {'MCap (Cr)':>14}")
    print("-" * 60)
    for stock in mid_caps:
        print(
            f"{stock.symbol:<12} {stock.last_price:>10.2f} {stock.pchange:>+7.2f}% "
            f"{stock.total_traded_value:>12.2f} {stock.total_market_cap:>14,.0f}"
        )

    print("\n--- Small Caps (MCap < Rs. 10,000 Cr) ---")
    small_caps = client.get_small_cap_activity(limit=10)
    print(f"{'Symbol':<12} {'Last':>10} {'%Chg':>8} {'Value (Cr)':>12} {'MCap (Cr)':>14}")
    print("-" * 60)
    for stock in small_caps:
        print(
            f"{stock.symbol:<12} {stock.last_price:>10.2f} {stock.pchange:>+7.2f}% "
            f"{stock.total_traded_value:>12.2f} {stock.total_market_cap:>14,.0f}"
        )

    client.close()


def get_specific_stock(symbol: str = "RELIANCE"):
    """Get trading data for a specific stock."""
    print("\n" + "=" * 60)
    print(f"Stock Data: {symbol}")
    print("=" * 60)

    client = NSEIndiaClient()

    stock = client.get_stock_traded_data(symbol)

    if stock:
        print(f"\nSymbol: {stock.symbol}")
        print(f"Last Price: Rs. {stock.last_price:.2f}")
        print(f"Previous Close: Rs. {stock.previous_close:.2f}")
        print(f"Change: Rs. {stock.change:+.2f} ({stock.pchange:+.2f}%)")
        print(f"Volume: {stock.total_traded_volume:.2f} Lakhs")
        print(f"Traded Value: Rs. {stock.total_traded_value:.2f} Cr")
        print(f"Market Cap: Rs. {stock.total_market_cap:,.0f} Cr")
        print(f"Status: {'Gainer' if stock.is_gainer else 'Loser' if stock.is_loser else 'Unchanged'}")
    else:
        print(f"Stock {symbol} not found in traded stocks")

    client.close()


def analyze_gainers_losers():
    """Analyze top gainers and losers."""
    print("\n" + "=" * 60)
    print("Top Gainers and Losers")
    print("=" * 60)

    client = NSEIndiaClient()

    response = client.get_stocks_traded()

    print("\n--- Top 10 Gainers ---")
    gainers = response.get_top_gainers(10)
    print(f"{'Symbol':<12} {'Last':>10} {'Change':>10} {'%Chg':>8} {'Value (Cr)':>12}")
    print("-" * 56)
    for stock in gainers:
        print(
            f"{stock.symbol:<12} {stock.last_price:>10.2f} {stock.change:>+10.2f} "
            f"{stock.pchange:>+7.2f}% {stock.total_traded_value:>12.2f}"
        )

    print("\n--- Top 10 Losers ---")
    losers = response.get_top_losers(10)
    print(f"{'Symbol':<12} {'Last':>10} {'Change':>10} {'%Chg':>8} {'Value (Cr)':>12}")
    print("-" * 56)
    for stock in losers:
        print(
            f"{stock.symbol:<12} {stock.last_price:>10.2f} {stock.change:>+10.2f} "
            f"{stock.pchange:>+7.2f}% {stock.total_traded_value:>12.2f}"
        )

    client.close()


def summary_statistics():
    """Calculate summary statistics from stocks traded data."""
    print("\n" + "=" * 60)
    print("Summary Statistics")
    print("=" * 60)

    client = NSEIndiaClient()

    response = client.get_stocks_traded()

    # Calculate statistics
    total_stocks = len(response.data)
    gainers = len(response.advances)
    losers = len(response.declines)
    unchanged = len(response.unchanged)

    # Average metrics
    if total_stocks > 0:
        avg_pchange = sum(s.pchange for s in response.data) / total_stocks
        avg_volume = sum(s.total_traded_volume for s in response.data) / total_stocks
        avg_value = sum(s.total_traded_value for s in response.data) / total_stocks

        # Weighted average change (by market cap)
        total_mcap = sum(s.total_market_cap for s in response.data)
        if total_mcap > 0:
            weighted_avg_change = sum(
                s.pchange * s.total_market_cap for s in response.data
            ) / total_mcap
        else:
            weighted_avg_change = 0

        print(f"\n--- Stock Counts ---")
        print(f"Total Stocks: {total_stocks}")
        print(f"Gainers: {gainers} ({gainers/total_stocks*100:.1f}%)")
        print(f"Losers: {losers} ({losers/total_stocks*100:.1f}%)")
        print(f"Unchanged: {unchanged} ({unchanged/total_stocks*100:.1f}%)")

        print(f"\n--- Averages ---")
        print(f"Avg % Change: {avg_pchange:+.2f}%")
        print(f"Weighted Avg % Change (by MCap): {weighted_avg_change:+.2f}%")
        print(f"Avg Volume: {avg_volume:.2f} Lakhs")
        print(f"Avg Traded Value: Rs. {avg_value:.2f} Cr")

        print(f"\n--- Market Totals ---")
        print(f"Total Traded Value: Rs. {response.total_traded_value_cr:,.2f} Cr")
        print(f"Total Market Cap: Rs. {response.total_market_cap_cr:,.2f} Cr")

    client.close()


if __name__ == "__main__":
    fetch_market_overview()
    show_top_traded_by_value()
    show_top_traded_by_volume()
    show_market_turnover()
    show_activity_by_cap()
    # get_specific_stock("RELIANCE")  # Uncomment to test
    analyze_gainers_losers()
    summary_statistics()
