"""Examples for fetching market indices data from NSE India.

This script demonstrates how to:
- Fetch all market indices
- Get specific index data (NIFTY 50, BANK NIFTY, etc.)
- Filter indices by category (sectoral, broad market, F&O eligible)
- Get top gainers and losers
- Analyze market breadth
- Access valuation metrics (PE, PB, Dividend Yield)
"""

from tools.nse_india import NSEIndiaClient
from tools.nse_india.models.indices import IndexCategory


def fetch_all_indices():
    """Fetch and display all market indices."""
    print("=" * 70)
    print("All NSE Market Indices")
    print("=" * 70)

    client = NSEIndiaClient()
    response = client.get_all_indices()

    print(f"Total indices: {len(response.indices)}")
    print(f"Categories: {response.get_categories()}")
    print()

    # Show first 10 indices
    for idx in response.indices[:10]:
        change_symbol = "+" if idx.is_positive else ""
        print(f"{idx.symbol:25} {idx.last:>12,.2f} {change_symbol}{idx.percent_change:>6.2f}%")

    client.close()
    return response


def get_specific_index(symbol: str = "NIFTY 50"):
    """Get detailed data for a specific index."""
    print("\n" + "=" * 70)
    print(f"Index Details: {symbol}")
    print("=" * 70)

    client = NSEIndiaClient()
    index = client.get_index(symbol)

    if index:
        print(f"Name: {index.index_name}")
        print(f"Symbol: {index.symbol}")
        print(f"Category: {index.category}")
        print()
        print("Price Data:")
        print(f"  Last: {index.last:,.2f}")
        print(f"  Change: {index.variation:+,.2f} ({index.percent_change:+.2f}%)")
        print(f"  Open: {index.open:,.2f}")
        print(f"  High: {index.high:,.2f}")
        print(f"  Low: {index.low:,.2f}")
        print(f"  Prev Close: {index.previous_close:,.2f}")
        print()
        print("52-Week Range:")
        print(f"  High: {index.year_high:,.2f} ({index.distance_from_52w_high:.2f}% below)")
        print(f"  Low: {index.year_low:,.2f} ({index.distance_from_52w_low:.2f}% above)")
        print()
        if index.pe is not None:
            print("Valuation Metrics:")
            print(f"  P/E: {index.pe}")
            print(f"  P/B: {index.pb}")
            print(f"  Dividend Yield: {index.dy}%")
            print()
        if index.advances is not None:
            print("Market Breadth:")
            print(f"  Advances: {index.advances}")
            print(f"  Declines: {index.declines}")
            print(f"  Unchanged: {index.unchanged}")
            if index.market_breadth_ratio:
                print(f"  A/D Ratio: {index.market_breadth_ratio:.2f}")
            print()
        print("Performance:")
        if index.percent_change_30d is not None:
            print(f"  30-Day: {index.percent_change_30d:+.2f}%")
        if index.percent_change_365d is not None:
            print(f"  1-Year: {index.percent_change_365d:+.2f}%")
    else:
        print(f"Index '{symbol}' not found")

    client.close()
    return index


def get_fno_eligible_indices():
    """Get indices eligible for F&O trading."""
    print("\n" + "=" * 70)
    print("F&O Eligible Indices")
    print("=" * 70)

    client = NSEIndiaClient()
    indices = client.get_derivatives_eligible_indices()

    print(f"Found {len(indices)} F&O eligible indices\n")

    for idx in indices:
        change_symbol = "+" if idx.is_positive else ""
        pe_str = f"PE: {idx.pe}" if idx.pe else ""
        print(f"{idx.symbol:25} {idx.last:>12,.2f} {change_symbol}{idx.percent_change:>6.2f}%  {pe_str}")

    client.close()
    return indices


def get_sectoral_performance():
    """Get sectoral indices performance."""
    print("\n" + "=" * 70)
    print("Sectoral Indices Performance")
    print("=" * 70)

    client = NSEIndiaClient()
    indices = client.get_sectoral_indices()

    # Sort by percent change
    sorted_indices = sorted(indices, key=lambda x: x.percent_change, reverse=True)

    print(f"{'Sector':<30} {'Value':>12} {'Change':>10} {'1Y Change':>12}")
    print("-" * 70)

    for idx in sorted_indices:
        change_str = f"{idx.percent_change:+.2f}%"
        yr_change = f"{idx.percent_change_365d:+.2f}%" if idx.percent_change_365d else "N/A"
        print(f"{idx.symbol:<30} {idx.last:>12,.2f} {change_str:>10} {yr_change:>12}")

    client.close()
    return sorted_indices


def get_top_gainers_losers():
    """Get top gaining and losing indices."""
    print("\n" + "=" * 70)
    print("Top Gainers and Losers")
    print("=" * 70)

    client = NSEIndiaClient()

    print("\nTop 5 Gainers:")
    print("-" * 50)
    gainers = client.get_index_gainers(limit=5)
    for idx in gainers:
        print(f"{idx.symbol:<25} {idx.last:>12,.2f} {idx.percent_change:>+7.2f}%")

    print("\nTop 5 Losers:")
    print("-" * 50)
    losers = client.get_index_losers(limit=5)
    for idx in losers:
        print(f"{idx.symbol:<25} {idx.last:>12,.2f} {idx.percent_change:>+7.2f}%")

    client.close()
    return gainers, losers


def analyze_market_breadth():
    """Analyze overall market breadth."""
    print("\n" + "=" * 70)
    print("Market Breadth Analysis")
    print("=" * 70)

    client = NSEIndiaClient()
    breadth = client.get_market_breadth()

    if breadth:
        print(f"\nNIFTY 500 Market Breadth:")
        print(f"  Index Value: {breadth['index_value']:,.2f}")
        print(f"  Index Change: {breadth['percent_change']:+.2f}%")
        print()
        print(f"  Advances: {breadth['advances']}")
        print(f"  Declines: {breadth['declines']}")
        print(f"  Unchanged: {breadth['unchanged']}")
        print()
        if breadth['ratio']:
            ratio = breadth['ratio']
            print(f"  Advance/Decline Ratio: {ratio:.2f}")
            if ratio > 1.5:
                print("  Market Sentiment: Strongly Bullish")
            elif ratio > 1:
                print("  Market Sentiment: Mildly Bullish")
            elif ratio > 0.67:
                print("  Market Sentiment: Mildly Bearish")
            else:
                print("  Market Sentiment: Strongly Bearish")
    else:
        print("Could not fetch market breadth data")

    client.close()
    return breadth


def compare_broad_market_indices():
    """Compare broad market indices performance."""
    print("\n" + "=" * 70)
    print("Broad Market Indices Comparison")
    print("=" * 70)

    client = NSEIndiaClient()
    indices = client.get_broad_market_indices()

    print(f"\n{'Index':<25} {'Value':>12} {'Change':>10} {'PE':>8} {'PB':>8}")
    print("-" * 70)

    for idx in indices:
        change_str = f"{idx.percent_change:+.2f}%"
        pe_str = f"{idx.pe:.1f}" if idx.pe else "N/A"
        pb_str = f"{idx.pb:.2f}" if idx.pb else "N/A"
        print(f"{idx.symbol:<25} {idx.last:>12,.2f} {change_str:>10} {pe_str:>8} {pb_str:>8}")

    client.close()
    return indices


def get_index_by_category():
    """Get indices by specific category."""
    print("\n" + "=" * 70)
    print("Indices by Category")
    print("=" * 70)

    client = NSEIndiaClient()

    # Get all available categories
    response = client.get_all_indices()
    categories = response.get_categories()

    for cat in categories:
        indices = response.get_by_category(cat)
        print(f"\n{cat} ({len(indices)} indices):")
        for idx in indices[:3]:  # Show first 3
            print(f"  - {idx.symbol}: {idx.last:,.2f} ({idx.percent_change:+.2f}%)")
        if len(indices) > 3:
            print(f"  ... and {len(indices) - 3} more")

    client.close()


if __name__ == "__main__":
    fetch_all_indices()
    get_specific_index("NIFTY 50")
    get_specific_index("NIFTY BANK")
    get_fno_eligible_indices()
    get_sectoral_performance()
    get_top_gainers_losers()
    analyze_market_breadth()
    compare_broad_market_indices()
    get_index_by_category()
