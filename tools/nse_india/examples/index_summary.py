"""Examples for using the Index Summary / Index Tracker APIs.

This script demonstrates how to:
- Get comprehensive index summary (price, returns, breadth, contributors)
- Fetch index price and valuation data (PE, PB, dividend yield)
- Get multi-period returns (1W, 1M, 3M, 6M, 1Y, 2Y, 3Y, 5Y)
- Analyze market breadth with advance/decline data
- Find top point contributors to index movement
- Get index heatmap data
- Fetch corporate announcements and board meetings for index constituents
- Get index intraday chart data
"""

from tools.nse_india.client import NSEIndiaClient


def get_index_price_data():
    """Get index price and valuation data."""
    print("=" * 60)
    print("Index Price & Valuation Data")
    print("=" * 60)

    client = NSEIndiaClient()

    indices = ["NIFTY 50", "NIFTY BANK", "NIFTY IT"]

    for index_name in indices:
        data = client.get_index_price_data(index_name)
        if data:
            print(f"\n{data.index_name}")
            print("-" * 40)
            print(f"Last: {data.last:,.2f} ({data.perc_change:+.2f}%)")
            print(f"Day Range: {data.low:,.2f} - {data.high:,.2f}")
            print(f"52W Range: {data.year_low:,.2f} - {data.year_high:,.2f}")
            print(f"P/E Ratio: {data.pe_ratio:.2f}")
            print(f"P/B Ratio: {data.pb_ratio:.2f}")
            print(f"Div Yield: {data.dividend_yield:.2f}%")
            print(f"Volume: {data.volume:,.2f} Cr")
            print(f"Value: Rs.{data.value:,.2f} Cr")

    client.close()


def get_index_returns():
    """Get multi-period index returns."""
    print("\n" + "=" * 60)
    print("Index Returns (Multi-Period)")
    print("=" * 60)

    client = NSEIndiaClient()

    returns = client.get_index_returns("NIFTY 50")
    if returns:
        print("\nNIFTY 50 Returns:")
        print("-" * 40)
        print(f"Yesterday: {returns.yesterday:+.2f}%")
        print(f"1 Week:    {returns.one_week:+.2f}%")
        print(f"1 Month:   {returns.one_month:+.2f}%")
        print(f"3 Month:   {returns.three_month:+.2f}%")
        print(f"6 Month:   {returns.six_month:+.2f}%")
        print(f"1 Year:    {returns.one_year:+.2f}%")
        print(f"2 Year:    {returns.two_year:+.2f}%")
        print(f"3 Year:    {returns.three_year:+.2f}%")
        print(f"5 Year:    {returns.five_year:+.2f}%")
        print(f"\nTrend: {returns.trend}")

    client.close()


def get_index_facts():
    """Get index description and methodology."""
    print("\n" + "=" * 60)
    print("Index Facts & Methodology")
    print("=" * 60)

    client = NSEIndiaClient()

    facts = client.get_index_facts("NIFTY 50")
    if facts:
        print(f"\n{facts.long_name}")
        print("-" * 40)
        if facts.description:
            # Print first 500 chars of description
            desc = facts.description[:500] + "..." if len(facts.description) > 500 else facts.description
            print(f"\nDescription:\n{desc}")
        if facts.methodology_pdf:
            print(f"\nMethodology: {facts.methodology_pdf}")
        if facts.factsheet_pdf:
            print(f"Factsheet: {facts.factsheet_pdf}")
        if facts.constituents_csv:
            print(f"Constituents: {facts.constituents_csv}")

    client.close()


def get_advance_decline():
    """Get market breadth data."""
    print("\n" + "=" * 60)
    print("Market Breadth - Advance/Decline")
    print("=" * 60)

    client = NSEIndiaClient()

    indices = ["NIFTY 50", "NIFTY BANK", "NIFTY IT", "NIFTY PHARMA"]

    print(f"\n{'Index':20} {'Adv':>6} {'Dec':>6} {'Unch':>6} {'A/D Ratio':>10} {'Sentiment':>15}")
    print("-" * 75)

    for index_name in indices:
        ad = client.get_index_advance_decline_data(index_name)
        if ad:
            print(
                f"{ad.index_name:20} {ad.advances:>6} {ad.declines:>6} "
                f"{ad.unchanged:>6} {ad.advance_decline_ratio:>10.2f} "
                f"{ad.market_sentiment:>15}"
            )

    client.close()


def get_point_contributors():
    """Get stocks contributing to index movement."""
    print("\n" + "=" * 60)
    print("Index Point Contributors")
    print("=" * 60)

    client = NSEIndiaClient()

    print("\nTop Positive Contributors (NIFTY 50):")
    print("-" * 60)
    print(f"{'Symbol':12} {'Company':25} {'Points':>10} {'Change%':>8}")
    print("-" * 60)

    for c in client.get_index_top_contributors("NIFTY 50", limit=5):
        print(f"{c.symbol:12} {c.company_name[:24]:25} {c.change_points:>+10.2f} {c.change_pct:>+7.2f}%")

    print("\nTop Negative Contributors (NIFTY 50):")
    print("-" * 60)
    print(f"{'Symbol':12} {'Company':25} {'Points':>10} {'Change%':>8}")
    print("-" * 60)

    for c in client.get_index_bottom_contributors("NIFTY 50", limit=5):
        print(f"{c.symbol:12} {c.company_name[:24]:25} {c.change_points:>+10.2f} {c.change_pct:>+7.2f}%")

    client.close()


def get_heatmap_data():
    """Get index heatmap data."""
    print("\n" + "=" * 60)
    print("Index Heatmap Data")
    print("=" * 60)

    client = NSEIndiaClient()

    heatmap = client.get_index_heatmap("NIFTY BANK")

    print("\nNIFTY BANK Heatmap (sorted by % change):")
    print("-" * 80)
    print(f"{'Symbol':12} {'LTP':>10} {'Change':>10} {'%Change':>8} {'Volume':>12} {'Value (Cr)':>12}")
    print("-" * 80)

    # Sort by percentage change
    for stock in sorted(heatmap, key=lambda x: x.pchange, reverse=True):
        value_cr = stock.traded_value / 1e7  # Convert to crores
        print(
            f"{stock.symbol:12} {stock.last_price:>10,.2f} {stock.change:>+10.2f} "
            f"{stock.pchange:>+7.2f}% {stock.traded_volume:>12,} {value_cr:>12,.2f}"
        )

    client.close()


def get_top_movers():
    """Get top gainers and losers from index tracker."""
    print("\n" + "=" * 60)
    print("Index Top Movers (Gainers & Losers)")
    print("=" * 60)

    client = NSEIndiaClient()

    print("\nTop 5 Gainers (NIFTY 50):")
    print("-" * 70)
    print(f"{'Symbol':12} {'LTP':>10} {'Change':>10} {'%Change':>8} {'Volume':>12}")
    print("-" * 70)

    for g in client.get_index_top_gainers_tracker("NIFTY 50", limit=5):
        print(
            f"{g.symbol:12} {g.last_price:>10,.2f} {g.change:>+10.2f} "
            f"{g.pchange:>+7.2f}% {g.total_traded_volume:>12,}"
        )
        if g.ca_purpose:
            print(f"    Corporate Action: {g.ca_purpose} (Ex: {g.ca_ex_date})")

    print("\nTop 5 Losers (NIFTY 50):")
    print("-" * 70)
    print(f"{'Symbol':12} {'LTP':>10} {'Change':>10} {'%Change':>8} {'Volume':>12}")
    print("-" * 70)

    for l in client.get_index_top_losers_tracker("NIFTY 50", limit=5):
        print(
            f"{l.symbol:12} {l.last_price:>10,.2f} {l.change:>+10.2f} "
            f"{l.pchange:>+7.2f}% {l.total_traded_volume:>12,}"
        )

    client.close()


def get_corporate_events():
    """Get announcements and board meetings for index constituents."""
    print("\n" + "=" * 60)
    print("Corporate Events for Index Constituents")
    print("=" * 60)

    client = NSEIndiaClient()

    print("\nRecent Announcements (NIFTY 50):")
    print("-" * 80)
    for ann in client.get_index_announcements("NIFTY 50", limit=5):
        print(f"{ann.symbol:12} | {ann.broadcast_date}")
        print(f"  Subject: {ann.subject}")
        print(f"  Details: {ann.details[:60]}..." if len(ann.details) > 60 else f"  Details: {ann.details}")
        print()

    print("\nUpcoming Board Meetings (NIFTY 50):")
    print("-" * 80)
    print(f"{'Symbol':15} {'Date':>12} {'Purpose':40}")
    print("-" * 80)
    for bm in client.get_index_board_meetings("NIFTY 50", limit=5):
        print(f"{bm.symbol:15} {bm.meeting_date:>12} {bm.purpose:40}")

    client.close()


def get_index_chart():
    """Get index intraday chart data."""
    print("\n" + "=" * 60)
    print("Index Chart Data")
    print("=" * 60)

    client = NSEIndiaClient()

    chart = client.get_index_intraday_chart("NIFTY 50", period="1D")

    print(f"\nNIFTY 50 Intraday Chart")
    print(f"Total Data Points: {len(chart.data_points)}")

    if chart.data_points:
        # Show first and last few points
        print("\nFirst 5 points:")
        for point in chart.data_points[:5]:
            from datetime import datetime
            ts = datetime.fromtimestamp(point.timestamp / 1000)
            print(f"  {ts.strftime('%H:%M:%S')} | {point.value:,.2f} | Phase: {point.market_phase}")

        print("\nLast 5 points:")
        for point in chart.data_points[-5:]:
            from datetime import datetime
            ts = datetime.fromtimestamp(point.timestamp / 1000)
            print(f"  {ts.strftime('%H:%M:%S')} | {point.value:,.2f} | Phase: {point.market_phase}")

    client.close()


def get_full_summary():
    """Get comprehensive index summary."""
    print("\n" + "=" * 60)
    print("Comprehensive Index Summary")
    print("=" * 60)

    client = NSEIndiaClient()

    # Get full summary and print formatted markdown
    summary = client.get_index_summary("NIFTY 50")

    # Print using the format_summary method
    print(summary.format_summary())

    # Or get it directly as markdown string
    # markdown = client.get_index_summary_markdown("NIFTY 50")
    # print(markdown)

    client.close()


def compare_multiple_indices():
    """Compare multiple indices side by side."""
    print("\n" + "=" * 60)
    print("Multi-Index Comparison")
    print("=" * 60)

    client = NSEIndiaClient()

    indices = ["NIFTY 50", "NIFTY BANK", "NIFTY IT", "NIFTY PHARMA", "NIFTY AUTO"]

    print(f"\n{'Index':20} {'Last':>12} {'Change%':>8} {'P/E':>8} {'1W%':>8} {'1M%':>8} {'1Y%':>8}")
    print("-" * 85)

    for index_name in indices:
        price = client.get_index_price_data(index_name)
        returns = client.get_index_returns(index_name)

        if price and returns:
            print(
                f"{price.index_name:20} {price.last:>12,.2f} "
                f"{price.perc_change:>+7.2f}% {price.pe_ratio:>8.2f} "
                f"{returns.one_week:>+7.2f}% {returns.one_month:>+7.2f}% "
                f"{returns.one_year:>+7.2f}%"
            )

    client.close()


def convenience_methods():
    """Demonstrate convenience methods for common indices."""
    print("\n" + "=" * 60)
    print("Convenience Methods for Common Indices")
    print("=" * 60)

    client = NSEIndiaClient()

    # Quick summaries for common indices
    print("\nNIFTY 50 Quick Summary:")
    nifty50 = client.get_nifty50_summary()
    if nifty50.price_data:
        pd = nifty50.price_data
        print(f"  Last: {pd.last:,.2f} ({pd.perc_change:+.2f}%)")
        print(f"  P/E: {pd.pe_ratio:.2f} | P/B: {pd.pb_ratio:.2f}")

    print("\nBank NIFTY Quick Summary:")
    banknifty = client.get_banknifty_summary()
    if banknifty.price_data:
        pd = banknifty.price_data
        print(f"  Last: {pd.last:,.2f} ({pd.perc_change:+.2f}%)")
        print(f"  P/E: {pd.pe_ratio:.2f} | P/B: {pd.pb_ratio:.2f}")

    print("\nNIFTY IT Quick Summary:")
    niftyit = client.get_niftyit_summary()
    if niftyit.price_data:
        pd = niftyit.price_data
        print(f"  Last: {pd.last:,.2f} ({pd.perc_change:+.2f}%)")
        print(f"  P/E: {pd.pe_ratio:.2f} | P/B: {pd.pb_ratio:.2f}")

    client.close()


if __name__ == "__main__":
    # Run all examples
    get_index_price_data()
    get_index_returns()
    get_index_facts()
    get_advance_decline()
    get_point_contributors()
    get_heatmap_data()
    get_top_movers()
    get_corporate_events()
    get_index_chart()
    get_full_summary()
    compare_multiple_indices()
    convenience_methods()
