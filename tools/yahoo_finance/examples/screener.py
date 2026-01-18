"""Examples for stock screening from Yahoo Finance.

This script demonstrates how to:
- Use predefined screener queries (day gainers, losers, most active, etc.)
- Create custom screener filters
- Screen for specific criteria (market cap, P/E ratio, etc.)
- Find undervalued stocks, growth stocks, etc.
"""

from tools.yahoo_finance import YFinanceClient


def screen_day_gainers():
    """Screen for today's top gaining stocks."""
    print("=" * 60)
    print("Day Gainers - Top Performing Stocks Today")
    print("=" * 60)

    client = YFinanceClient()
    results = client.screen("day_gainers")

    print(f"\nQuery: {results.query_name}")
    print(f"Total results: {results.total}")

    if not results.results:
        print("No results found")
        return

    print("\n| Symbol | Name | Price | Change |")
    print("|--------|------|-------|--------|")

    for stock in results.results[:15]:
        symbol = stock.get('symbol', 'N/A')
        name = stock.get('shortName', stock.get('longName', 'N/A'))
        if name and len(name) > 25:
            name = name[:22] + "..."
        price = stock.get('regularMarketPrice', 0)
        change = stock.get('regularMarketChangePercent', 0)

        print(f"| {symbol:<6} | {name:<25} | ${price:>8.2f} | {change:>+7.2f}% |")


def screen_day_losers():
    """Screen for today's top losing stocks."""
    print("\n" + "=" * 60)
    print("Day Losers - Worst Performing Stocks Today")
    print("=" * 60)

    client = YFinanceClient()
    results = client.screen("day_losers")

    print(f"\nTotal results: {results.total}")

    if not results.results:
        print("No results found")
        return

    print("\n| Symbol | Name | Price | Change |")
    print("|--------|------|-------|--------|")

    for stock in results.results[:15]:
        symbol = stock.get('symbol', 'N/A')
        name = stock.get('shortName', 'N/A')
        if name and len(name) > 25:
            name = name[:22] + "..."
        price = stock.get('regularMarketPrice', 0)
        change = stock.get('regularMarketChangePercent', 0)

        print(f"| {symbol:<6} | {name:<25} | ${price:>8.2f} | {change:>+7.2f}% |")


def screen_most_active():
    """Screen for most actively traded stocks."""
    print("\n" + "=" * 60)
    print("Most Active - Highest Trading Volume")
    print("=" * 60)

    client = YFinanceClient()
    results = client.screen("most_actives")

    print(f"\nTotal results: {results.total}")

    if not results.results:
        print("No results found")
        return

    print("\n| Symbol | Name | Price | Volume |")
    print("|--------|------|-------|--------|")

    for stock in results.results[:15]:
        symbol = stock.get('symbol', 'N/A')
        name = stock.get('shortName', 'N/A')
        if name and len(name) > 25:
            name = name[:22] + "..."
        price = stock.get('regularMarketPrice', 0)
        volume = stock.get('regularMarketVolume', 0)
        vol_str = f"{volume/1e6:.1f}M" if volume else "N/A"

        print(f"| {symbol:<6} | {name:<25} | ${price:>8.2f} | {vol_str:>8} |")


def screen_undervalued_large_caps():
    """Screen for undervalued large cap stocks."""
    print("\n" + "=" * 60)
    print("Undervalued Large Caps")
    print("=" * 60)

    client = YFinanceClient()
    results = client.screen("undervalued_large_caps")

    print(f"\nTotal results: {results.total}")

    if not results.results:
        print("No results found")
        return

    print("\n| Symbol | Name | Price | P/E | Market Cap |")
    print("|--------|------|-------|-----|------------|")

    for stock in results.results[:15]:
        symbol = stock.get('symbol', 'N/A')
        name = stock.get('shortName', 'N/A')
        if name and len(name) > 20:
            name = name[:17] + "..."
        price = stock.get('regularMarketPrice', 0)
        pe = stock.get('trailingPE', stock.get('forwardPE', 'N/A'))
        pe_str = f"{pe:.1f}" if isinstance(pe, (int, float)) else 'N/A'
        mcap = stock.get('marketCap', 0)
        if mcap >= 1e12:
            mcap_str = f"${mcap/1e12:.1f}T"
        elif mcap >= 1e9:
            mcap_str = f"${mcap/1e9:.0f}B"
        else:
            mcap_str = "N/A"

        print(f"| {symbol:<6} | {name:<20} | ${price:>7.2f} | {pe_str:>5} | {mcap_str:>10} |")


def screen_undervalued_growth():
    """Screen for undervalued growth stocks."""
    print("\n" + "=" * 60)
    print("Undervalued Growth Stocks")
    print("=" * 60)

    client = YFinanceClient()
    results = client.screen("undervalued_growth_stocks")

    print(f"\nTotal results: {results.total}")

    if not results.results:
        print("No results found")
        return

    print("\n| Symbol | Name | Price | Change |")
    print("|--------|------|-------|--------|")

    for stock in results.results[:15]:
        symbol = stock.get('symbol', 'N/A')
        name = stock.get('shortName', 'N/A')
        if name and len(name) > 25:
            name = name[:22] + "..."
        price = stock.get('regularMarketPrice', 0)
        change = stock.get('regularMarketChangePercent', 0)

        print(f"| {symbol:<6} | {name:<25} | ${price:>8.2f} | {change:>+7.2f}% |")


def screen_growth_tech():
    """Screen for growth technology stocks."""
    print("\n" + "=" * 60)
    print("Growth Technology Stocks")
    print("=" * 60)

    client = YFinanceClient()
    results = client.screen("growth_technology_stocks")

    print(f"\nTotal results: {results.total}")

    if not results.results:
        print("No results found")
        return

    print("\n| Symbol | Name | Price | Change |")
    print("|--------|------|-------|--------|")

    for stock in results.results[:15]:
        symbol = stock.get('symbol', 'N/A')
        name = stock.get('shortName', 'N/A')
        if name and len(name) > 25:
            name = name[:22] + "..."
        price = stock.get('regularMarketPrice', 0)
        change = stock.get('regularMarketChangePercent', 0)

        print(f"| {symbol:<6} | {name:<25} | ${price:>8.2f} | {change:>+7.2f}% |")


def screen_aggressive_small_caps():
    """Screen for aggressive small cap stocks."""
    print("\n" + "=" * 60)
    print("Aggressive Small Caps")
    print("=" * 60)

    client = YFinanceClient()
    results = client.screen("aggressive_small_caps")

    print(f"\nTotal results: {results.total}")

    if not results.results:
        print("No results found")
        return

    print("\n| Symbol | Name | Price | Change |")
    print("|--------|------|-------|--------|")

    for stock in results.results[:15]:
        symbol = stock.get('symbol', 'N/A')
        name = stock.get('shortName', 'N/A')
        if name and len(name) > 25:
            name = name[:22] + "..."
        price = stock.get('regularMarketPrice', 0)
        change = stock.get('regularMarketChangePercent', 0)

        print(f"| {symbol:<6} | {name:<25} | ${price:>8.2f} | {change:>+7.2f}% |")


def screen_small_cap_gainers():
    """Screen for small cap gainers."""
    print("\n" + "=" * 60)
    print("Small Cap Gainers")
    print("=" * 60)

    client = YFinanceClient()
    results = client.screen("small_cap_gainers")

    print(f"\nTotal results: {results.total}")

    if not results.results:
        print("No results found")
        return

    print("\n| Symbol | Name | Price | Change | Market Cap |")
    print("|--------|------|-------|--------|------------|")

    for stock in results.results[:15]:
        symbol = stock.get('symbol', 'N/A')
        name = stock.get('shortName', 'N/A')
        if name and len(name) > 20:
            name = name[:17] + "..."
        price = stock.get('regularMarketPrice', 0)
        change = stock.get('regularMarketChangePercent', 0)
        mcap = stock.get('marketCap', 0)
        mcap_str = f"${mcap/1e6:.0f}M" if mcap else "N/A"

        print(f"| {symbol:<6} | {name:<20} | ${price:>7.2f} | {change:>+7.2f}% | {mcap_str:>10} |")


def screen_most_shorted():
    """Screen for most shorted stocks."""
    print("\n" + "=" * 60)
    print("Most Shorted Stocks")
    print("=" * 60)

    client = YFinanceClient()
    results = client.screen("most_shorted_stocks")

    print(f"\nTotal results: {results.total}")

    if not results.results:
        print("No results found")
        return

    print("\n| Symbol | Name | Price | Change |")
    print("|--------|------|-------|--------|")

    for stock in results.results[:15]:
        symbol = stock.get('symbol', 'N/A')
        name = stock.get('shortName', 'N/A')
        if name and len(name) > 25:
            name = name[:22] + "..."
        price = stock.get('regularMarketPrice', 0)
        change = stock.get('regularMarketChangePercent', 0)

        print(f"| {symbol:<6} | {name:<25} | ${price:>8.2f} | {change:>+7.2f}% |")


def screen_custom_high_gainers():
    """Custom screen for stocks with >5% gain."""
    print("\n" + "=" * 60)
    print("Custom Screen: Stocks with >5% Gain Today")
    print("=" * 60)

    client = YFinanceClient()

    filters = [
        {"operator": "gt", "field": "percentchange", "values": [5]}
    ]

    results = client.screen_custom(filters=filters)

    print(f"\nTotal results: {results.total}")

    if not results.results:
        print("No results found")
        return

    print("\n| Symbol | Name | Price | Change |")
    print("|--------|------|-------|--------|")

    for stock in results.results[:15]:
        symbol = stock.get('symbol', 'N/A')
        name = stock.get('shortName', 'N/A')
        if name and len(name) > 25:
            name = name[:22] + "..."
        price = stock.get('regularMarketPrice', 0)
        change = stock.get('regularMarketChangePercent', 0)

        print(f"| {symbol:<6} | {name:<25} | ${price:>8.2f} | {change:>+7.2f}% |")


def screen_custom_large_cap_tech():
    """Custom screen for large cap tech stocks."""
    print("\n" + "=" * 60)
    print("Custom Screen: Large Cap Technology")
    print("=" * 60)

    client = YFinanceClient()

    filters = [
        {"operator": "eq", "field": "sector", "values": ["Technology"]},
        {"operator": "gt", "field": "intradaymarketcap", "values": [10000000000]},  # >$10B
    ]

    results = client.screen_custom(filters=filters)

    print(f"\nTotal results: {results.total}")

    if not results.results:
        print("No results found")
        return

    print("\n| Symbol | Name | Price | Market Cap |")
    print("|--------|------|-------|------------|")

    for stock in results.results[:15]:
        symbol = stock.get('symbol', 'N/A')
        name = stock.get('shortName', 'N/A')
        if name and len(name) > 25:
            name = name[:22] + "..."
        price = stock.get('regularMarketPrice', 0)
        mcap = stock.get('marketCap', 0)
        if mcap >= 1e12:
            mcap_str = f"${mcap/1e12:.1f}T"
        elif mcap >= 1e9:
            mcap_str = f"${mcap/1e9:.0f}B"
        else:
            mcap_str = "N/A"

        print(f"| {symbol:<6} | {name:<25} | ${price:>8.2f} | {mcap_str:>10} |")


def screen_custom_dividend_stocks():
    """Custom screen for dividend paying stocks."""
    print("\n" + "=" * 60)
    print("Custom Screen: Dividend Stocks (Yield > 3%)")
    print("=" * 60)

    client = YFinanceClient()

    filters = [
        {"operator": "gt", "field": "dividendyield", "values": [3]},
        {"operator": "gt", "field": "intradaymarketcap", "values": [1000000000]},  # >$1B
    ]

    results = client.screen_custom(filters=filters)

    print(f"\nTotal results: {results.total}")

    if not results.results:
        print("No results found")
        return

    print("\n| Symbol | Name | Price | Div Yield |")
    print("|--------|------|-------|-----------|")

    for stock in results.results[:15]:
        symbol = stock.get('symbol', 'N/A')
        name = stock.get('shortName', 'N/A')
        if name and len(name) > 25:
            name = name[:22] + "..."
        price = stock.get('regularMarketPrice', 0)
        div_yield = stock.get('dividendYield', 0)
        yield_str = f"{div_yield:.2f}%" if div_yield else "N/A"

        print(f"| {symbol:<6} | {name:<25} | ${price:>8.2f} | {yield_str:>9} |")


def list_predefined_screeners():
    """List all available predefined screener queries."""
    print("\n" + "=" * 60)
    print("Available Predefined Screeners")
    print("=" * 60)

    screeners = [
        ("day_gainers", "Top gaining stocks today"),
        ("day_losers", "Top losing stocks today"),
        ("most_actives", "Most actively traded stocks"),
        ("undervalued_large_caps", "Large caps trading below intrinsic value"),
        ("undervalued_growth_stocks", "Growth stocks trading at a discount"),
        ("growth_technology_stocks", "Tech stocks with strong growth"),
        ("aggressive_small_caps", "High growth potential small caps"),
        ("small_cap_gainers", "Small cap stocks with gains"),
        ("most_shorted_stocks", "Stocks with highest short interest"),
        ("conservative_foreign_funds", "Conservative international funds"),
        ("high_yield_bond", "High yield bond funds"),
        ("portfolio_anchors", "Stable, reliable funds"),
        ("solid_large_growth_funds", "Large cap growth funds"),
        ("solid_midcap_growth_funds", "Mid cap growth funds"),
        ("top_mutual_funds", "Top performing mutual funds"),
    ]

    print("\n| Query Name | Description |")
    print("|------------|-------------|")

    for name, desc in screeners:
        print(f"| {name:<28} | {desc:<35} |")


if __name__ == "__main__":
    list_predefined_screeners()
    screen_day_gainers()
    screen_day_losers()
    screen_most_active()
    screen_undervalued_large_caps()
    screen_undervalued_growth()
    screen_growth_tech()
    screen_aggressive_small_caps()
    screen_small_cap_gainers()
    screen_most_shorted()
    screen_custom_high_gainers()
    screen_custom_large_cap_tech()
    screen_custom_dividend_stocks()
