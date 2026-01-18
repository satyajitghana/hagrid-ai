"""Examples for using the Index Constituents APIs.

This script demonstrates how to:
- Get master list of all available indices on NSE
- Fetch constituents of any index (NIFTY 50, Bank NIFTY, sectoral indices, etc.)
- Analyze index breadth and sentiment
- Get top gainers/losers within an index
- Find stocks near 52-week highs/lows
- Filter stocks by various criteria
"""

from tools.nse_india.client import NSEIndiaClient


def list_all_indices():
    """List all available indices on NSE."""
    print("=" * 60)
    print("All Available Indices on NSE")
    print("=" * 60)

    client = NSEIndiaClient()

    master = client.get_index_master()

    print(f"\nTotal Indices: {master.total_count}")

    print(f"\n📊 Derivatives Eligible ({len(master.derivatives_eligible)}):")
    for idx in master.derivatives_eligible:
        print(f"  - {idx}")

    print(f"\n📈 Broad Market Indices ({len(master.broad_market)}):")
    for idx in master.broad_market[:10]:  # Show first 10
        print(f"  - {idx}")
    if len(master.broad_market) > 10:
        print(f"  ... and {len(master.broad_market) - 10} more")

    print(f"\n🏭 Sectoral Indices ({len(master.sectoral)}):")
    for idx in master.sectoral[:10]:
        print(f"  - {idx}")
    if len(master.sectoral) > 10:
        print(f"  ... and {len(master.sectoral) - 10} more")

    print(f"\n🎯 Thematic Indices ({len(master.thematic)}):")
    for idx in master.thematic[:10]:
        print(f"  - {idx}")
    if len(master.thematic) > 10:
        print(f"  ... and {len(master.thematic) - 10} more")

    print(f"\n📐 Strategy Indices ({len(master.strategy)}):")
    for idx in master.strategy[:10]:
        print(f"  - {idx}")
    if len(master.strategy) > 10:
        print(f"  ... and {len(master.strategy) - 10} more")

    print(f"\n📋 Others ({len(master.others)}):")
    for idx in master.others:
        print(f"  - {idx}")

    client.close()


def fetch_nifty50_constituents():
    """Fetch NIFTY 50 constituents with detailed data."""
    print("\n" + "=" * 60)
    print("NIFTY 50 Index Constituents")
    print("=" * 60)

    client = NSEIndiaClient()

    response = client.get_nifty50_constituents()

    # Index summary
    idx = response.index_data
    if idx:
        print(f"\nIndex: {response.name}")
        print(f"Timestamp: {response.timestamp}")
        print(f"Last Price: {idx.last_price:,.2f}")
        print(f"Change: {idx.change:+.2f} ({idx.pchange:+.2f}%)")
        print(f"Day Range: {idx.day_low:,.2f} - {idx.day_high:,.2f}")
        print(f"52-Week Range: {idx.year_low:,.2f} - {idx.year_high:,.2f}")

    # Breadth
    adv = response.advance
    print(f"\nMarket Breadth:")
    print(f"  Advances: {adv.advances_int}")
    print(f"  Declines: {adv.declines_int}")
    print(f"  Unchanged: {adv.unchanged_int}")
    print(f"  A/D Ratio: {adv.advance_decline_ratio:.2f}")
    print(f"  Sentiment: {adv.market_sentiment}")

    # Constituents
    print(f"\nTotal Constituents: {response.constituent_count}")

    # Top 10 by price change
    print("\nTop 10 Stocks by Price Change:")
    print("-" * 90)
    print(f"{'Symbol':12} {'Company':25} {'LTP':>10} {'Change%':>8} {'Volume':>12} {'1Y Return':>10}")
    print("-" * 90)

    for stock in response.top_gainers[:10]:
        name = stock.company_name[:24] if stock.company_name else ""
        print(
            f"{stock.symbol:12} {name:25} "
            f"{stock.last_price:>10,.2f} {stock.pchange:>+7.2f}% "
            f"{stock.total_traded_volume:>12,} {stock.per_change_365d:>+9.2f}%"
        )

    client.close()


def fetch_sectoral_index(index_name: str = "NIFTY IT"):
    """Fetch a sectoral index constituents."""
    print("\n" + "=" * 60)
    print(f"{index_name} Index Constituents")
    print("=" * 60)

    client = NSEIndiaClient()

    response = client.get_index_constituents(index_name)

    print(f"\nIndex: {response.name}")
    print(f"Constituents: {response.constituent_count}")
    print(f"Timestamp: {response.timestamp}")

    # All stocks in the index
    print(f"\nAll Stocks in {index_name}:")
    print("-" * 100)
    print(f"{'Symbol':12} {'Company':30} {'Industry':25} {'LTP':>10} {'Change%':>8}")
    print("-" * 100)

    for stock in sorted(response.constituents, key=lambda x: x.pchange, reverse=True):
        name = stock.company_name[:29] if stock.company_name else ""
        industry = stock.industry[:24] if stock.industry else ""
        print(
            f"{stock.symbol:12} {name:30} {industry:25} "
            f"{stock.last_price:>10,.2f} {stock.pchange:>+7.2f}%"
        )

    client.close()


def compare_index_breadth():
    """Compare market breadth across different indices."""
    print("\n" + "=" * 60)
    print("Index Breadth Comparison")
    print("=" * 60)

    client = NSEIndiaClient()

    indices = ["NIFTY 50", "NIFTY BANK", "NIFTY IT", "NIFTY PHARMA", "NIFTY AUTO"]

    print(f"\n{'Index':25} {'Adv':>6} {'Dec':>6} {'A/D Ratio':>10} {'Sentiment':>15}")
    print("-" * 75)

    for index_name in indices:
        breadth = client.get_index_breadth(index_name)
        print(
            f"{breadth['index_name']:25} "
            f"{breadth['advances']:>6} {breadth['declines']:>6} "
            f"{breadth['advance_decline_ratio']:>10.2f} {breadth['sentiment']:>15}"
        )

    client.close()


def find_52_week_extremes():
    """Find stocks near 52-week highs and lows in an index."""
    print("\n" + "=" * 60)
    print("Stocks Near 52-Week Extremes (NIFTY 50)")
    print("=" * 60)

    client = NSEIndiaClient()

    # Near 52-week highs
    highs = client.get_index_near_52_week_highs("NIFTY 50")
    print(f"\n📈 Near 52-Week High ({len(highs)} stocks):")
    print("-" * 70)
    if highs:
        print(f"{'Symbol':12} {'LTP':>10} {'52W High':>10} {'% Away':>8}")
        print("-" * 70)
        for stock in highs:
            print(
                f"{stock.symbol:12} {stock.last_price:>10,.2f} "
                f"{stock.year_high:>10,.2f} {stock.near_wkh:>+7.2f}%"
            )
    else:
        print("  No stocks near 52-week high")

    # Near 52-week lows
    lows = client.get_index_near_52_week_lows("NIFTY 50")
    print(f"\n📉 Near 52-Week Low ({len(lows)} stocks):")
    print("-" * 70)
    if lows:
        print(f"{'Symbol':12} {'LTP':>10} {'52W Low':>10} {'% Away':>8}")
        print("-" * 70)
        for stock in lows:
            print(
                f"{stock.symbol:12} {stock.last_price:>10,.2f} "
                f"{stock.year_low:>10,.2f} {stock.near_wkl:>+7.2f}%"
            )
    else:
        print("  No stocks near 52-week low")

    client.close()


def analyze_yearly_performance():
    """Analyze yearly performance of index constituents."""
    print("\n" + "=" * 60)
    print("Yearly Performance Analysis (NIFTY 50)")
    print("=" * 60)

    client = NSEIndiaClient()

    performers = client.get_index_yearly_performers("NIFTY 50", limit=10)

    print("\n🏆 Top 10 Performers (1-Year Return):")
    print("-" * 60)
    print(f"{'Symbol':12} {'Company':25} {'1Y Return':>10}")
    print("-" * 60)
    for stock in performers["top"]:
        name = stock.company_name[:24] if stock.company_name else ""
        print(f"{stock.symbol:12} {name:25} {stock.per_change_365d:>+9.2f}%")

    print("\n💔 Worst 10 Performers (1-Year Return):")
    print("-" * 60)
    for stock in performers["worst"]:
        name = stock.company_name[:24] if stock.company_name else ""
        print(f"{stock.symbol:12} {name:25} {stock.per_change_365d:>+9.2f}%")

    client.close()


def get_index_symbols_list():
    """Get list of all symbols in an index."""
    print("\n" + "=" * 60)
    print("Index Symbols List")
    print("=" * 60)

    client = NSEIndiaClient()

    indices = ["NIFTY 50", "NIFTY BANK", "NIFTY IT"]

    for index_name in indices:
        symbols = client.get_index_symbols(index_name)
        print(f"\n{index_name} ({len(symbols)} stocks):")
        print(", ".join(symbols))

    client.close()


def check_symbol_membership():
    """Check if symbols are part of various indices."""
    print("\n" + "=" * 60)
    print("Symbol Index Membership Check")
    print("=" * 60)

    client = NSEIndiaClient()

    symbols = ["RELIANCE", "TCS", "HDFCBANK", "INFY", "KOTAKBANK"]
    indices = ["NIFTY 50", "NIFTY 100", "NIFTY BANK", "NIFTY IT"]

    print(f"\n{'Symbol':12}", end="")
    for idx in indices:
        short_name = idx.replace("NIFTY ", "N")[:10]
        print(f"{short_name:>12}", end="")
    print()
    print("-" * 60)

    for symbol in symbols:
        print(f"{symbol:12}", end="")
        for index_name in indices:
            is_member = client.is_symbol_in_index(symbol, index_name)
            status = "✓" if is_member else "-"
            print(f"{status:>12}", end="")
        print()

    client.close()


def top_stocks_by_criteria():
    """Get top stocks by various criteria."""
    print("\n" + "=" * 60)
    print("Top Stocks by Criteria (NIFTY 50)")
    print("=" * 60)

    client = NSEIndiaClient()

    # Top by market cap
    print("\n💰 Top 10 by Market Cap:")
    print("-" * 60)
    print(f"{'Symbol':12} {'Company':25} {'Market Cap (Cr)':>18}")
    print("-" * 60)
    for stock in client.get_index_top_by_market_cap("NIFTY 50", 10):
        name = stock.company_name[:24] if stock.company_name else ""
        mcap = stock.ffmc / 1e7  # Convert to crores
        print(f"{stock.symbol:12} {name:25} {mcap:>18,.0f}")

    # Top by volume
    print("\n📊 Top 10 by Volume:")
    print("-" * 60)
    print(f"{'Symbol':12} {'Company':25} {'Volume':>15}")
    print("-" * 60)
    for stock in client.get_index_top_by_volume("NIFTY 50", 10):
        name = stock.company_name[:24] if stock.company_name else ""
        print(f"{stock.symbol:12} {name:25} {stock.total_traded_volume:>15,}")

    # Top by traded value
    print("\n💵 Top 10 by Traded Value:")
    print("-" * 60)
    print(f"{'Symbol':12} {'Company':25} {'Value (Cr)':>15}")
    print("-" * 60)
    for stock in client.get_index_top_by_value("NIFTY 50", 10):
        name = stock.company_name[:24] if stock.company_name else ""
        value = stock.total_traded_value / 1e7  # Convert to crores
        print(f"{stock.symbol:12} {name:25} {value:>15,.2f}")

    client.close()


def fno_securities():
    """Get all F&O eligible securities."""
    print("\n" + "=" * 60)
    print("F&O Eligible Securities")
    print("=" * 60)

    client = NSEIndiaClient()

    response = client.get_fno_securities()

    print(f"\nTotal F&O Securities: {response.constituent_count}")

    # Group by whether they're advancing or declining
    advancing = response.advancing_stocks
    declining = response.declining_stocks

    print(f"Advancing: {len(advancing)}")
    print(f"Declining: {len(declining)}")

    print("\nTop 10 F&O Gainers:")
    print("-" * 60)
    for stock in response.top_gainers[:10]:
        print(f"  {stock.symbol:15} {stock.pchange:>+7.2f}%  LTP: {stock.last_price:>10,.2f}")

    print("\nTop 10 F&O Losers:")
    print("-" * 60)
    for stock in response.top_losers[:10]:
        print(f"  {stock.symbol:15} {stock.pchange:>+7.2f}%  LTP: {stock.last_price:>10,.2f}")

    client.close()


def filter_by_industry():
    """Filter index constituents by industry."""
    print("\n" + "=" * 60)
    print("Filter by Industry (NIFTY 500)")
    print("=" * 60)

    client = NSEIndiaClient()

    response = client.get_nifty500_constituents()

    # Find all bank stocks
    bank_stocks = response.filter_by_industry("Bank")
    print(f"\nBank Stocks in NIFTY 500 ({len(bank_stocks)} found):")
    print("-" * 70)
    for stock in sorted(bank_stocks, key=lambda x: x.ffmc, reverse=True)[:15]:
        print(f"  {stock.symbol:15} {stock.industry:30} {stock.pchange:>+7.2f}%")

    # Find all IT stocks
    it_stocks = response.filter_by_industry("Software")
    print(f"\nIT/Software Stocks in NIFTY 500 ({len(it_stocks)} found):")
    print("-" * 70)
    for stock in sorted(it_stocks, key=lambda x: x.ffmc, reverse=True)[:15]:
        print(f"  {stock.symbol:15} {stock.industry:30} {stock.pchange:>+7.2f}%")

    client.close()


if __name__ == "__main__":
    # Run all examples
    list_all_indices()
    fetch_nifty50_constituents()
    fetch_sectoral_index("NIFTY IT")
    compare_index_breadth()
    find_52_week_extremes()
    analyze_yearly_performance()
    get_index_symbols_list()
    check_symbol_membership()
    top_stocks_by_criteria()
    fno_securities()
    filter_by_industry()
