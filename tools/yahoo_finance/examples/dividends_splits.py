"""Examples for dividends, splits, and corporate actions from Yahoo Finance.

This script demonstrates how to:
- Fetch dividend history for stocks
- Get stock split history
- Analyze corporate actions (dividends + splits combined)
- Track capital gains for ETFs
- View shares outstanding history
"""

from tools.yahoo_finance import YFinanceClient


def fetch_dividend_history(symbol: str = "AAPL"):
    """Fetch dividend history for a ticker."""
    print("=" * 60)
    print(f"Dividend History for {symbol}")
    print("=" * 60)

    client = YFinanceClient()
    divs = client.get_dividends(symbol)

    print(f"\nTotal dividend payments: {len(divs.dividends)}")

    if not divs.dividends:
        print("No dividend history available")
        return

    # Calculate annual totals
    annual_totals = {}
    for d in divs.dividends:
        year = d.date.year
        annual_totals[year] = annual_totals.get(year, 0) + d.dividend

    print("\n--- Annual Dividend Totals ---")
    print("| Year | Total Dividend |")
    print("|------|----------------|")
    for year in sorted(annual_totals.keys(), reverse=True)[:10]:
        print(f"| {year} | ${annual_totals[year]:.4f} |")

    print("\n--- Recent Dividends ---")
    print("| Date | Dividend |")
    print("|------|----------|")
    for d in divs.dividends[-10:]:
        print(f"| {d.date.strftime('%Y-%m-%d')} | ${d.dividend:.4f} |")


def fetch_split_history(symbol: str = "AAPL"):
    """Fetch stock split history for a ticker."""
    print("\n" + "=" * 60)
    print(f"Stock Split History for {symbol}")
    print("=" * 60)

    client = YFinanceClient()
    splits = client.get_splits(symbol)

    print(f"\nTotal splits: {len(splits.splits)}")

    if not splits.splits:
        print("No split history available")
        return

    print("\n| Date | Split Ratio |")
    print("|------|-------------|")
    for s in splits.splits:
        # Format ratio nicely
        ratio = s.split_ratio
        if ratio >= 1:
            ratio_str = f"{int(ratio)}:1"
        else:
            ratio_str = f"1:{int(1/ratio)}"
        print(f"| {s.date.strftime('%Y-%m-%d')} | {ratio_str} |")


def fetch_corporate_actions(symbol: str = "AAPL"):
    """Fetch combined corporate actions (dividends + splits)."""
    print("\n" + "=" * 60)
    print(f"Corporate Actions for {symbol}")
    print("=" * 60)

    client = YFinanceClient()
    actions = client.get_actions(symbol)

    print(f"\nTotal actions: {len(actions.actions)}")

    if not actions.actions:
        print("No corporate actions available")
        return

    # Filter to show only non-zero actions
    significant_actions = [
        a for a in actions.actions
        if a.dividends > 0 or a.stock_splits > 0
    ]

    print(f"Significant actions: {len(significant_actions)}")

    print("\n--- Recent Actions ---")
    print("| Date | Dividend | Stock Split |")
    print("|------|----------|-------------|")
    for a in significant_actions[-15:]:
        div_str = f"${a.dividends:.4f}" if a.dividends > 0 else "-"
        split_str = f"{a.stock_splits:.0f}:1" if a.stock_splits > 0 else "-"
        print(f"| {a.date.strftime('%Y-%m-%d')} | {div_str:>8} | {split_str:>11} |")


def fetch_capital_gains(symbol: str = "SPY"):
    """Fetch capital gains distributions for ETFs."""
    print("\n" + "=" * 60)
    print(f"Capital Gains for {symbol} (ETF)")
    print("=" * 60)

    client = YFinanceClient()
    cg = client.get_capital_gains(symbol)

    print(f"\nTotal capital gain distributions: {len(cg.capital_gains)}")

    if not cg.capital_gains:
        print("No capital gains distributions (common for many ETFs)")
        return

    print("\n| Date | Capital Gain |")
    print("|------|--------------|")
    for c in cg.capital_gains[-10:]:
        print(f"| {c.date.strftime('%Y-%m-%d')} | ${c.capital_gain:.4f} |")


def fetch_shares_history(symbol: str = "AAPL"):
    """Fetch shares outstanding history."""
    print("\n" + "=" * 60)
    print(f"Shares Outstanding History for {symbol}")
    print("=" * 60)

    client = YFinanceClient()
    shares = client.get_shares_full(symbol)

    print(f"\nTotal data points: {len(shares.shares)}")

    if not shares.shares:
        print("No shares history available")
        return

    # Get recent history
    recent = shares.shares[-20:]

    print("\n--- Recent Shares Outstanding ---")
    print("| Date | Shares Outstanding |")
    print("|------|--------------------|")
    for s in recent:
        shares_b = s.shares / 1e9
        print(f"| {s.date.strftime('%Y-%m-%d')} | {shares_b:.2f}B |")


def compare_dividend_yields():
    """Compare dividend yields across dividend aristocrats."""
    print("\n" + "=" * 60)
    print("Dividend Aristocrats Comparison")
    print("=" * 60)

    client = YFinanceClient()

    # Sample of dividend aristocrats
    symbols = ["JNJ", "PG", "KO", "PEP", "MMM", "ABT", "T", "VZ"]

    print("\n| Symbol | Dividend Yield | Recent Dividend | Annual Total |")
    print("|--------|----------------|-----------------|--------------|")

    for symbol in symbols:
        try:
            info = client.get_ticker_info(symbol)
            divs = client.get_dividends(symbol)

            div_yield = info.info.get('dividendYield', 0)
            yield_str = f"{div_yield:.2%}" if div_yield else "N/A"

            if divs.dividends:
                recent = divs.dividends[-1].dividend
                recent_str = f"${recent:.4f}"

                # Calculate annual total (last 4 quarters)
                last_4 = [d.dividend for d in divs.dividends[-4:]]
                annual = sum(last_4)
                annual_str = f"${annual:.2f}"
            else:
                recent_str = "N/A"
                annual_str = "N/A"

            print(f"| {symbol:<6} | {yield_str:>14} | {recent_str:>15} | {annual_str:>12} |")
        except Exception as e:
            print(f"| {symbol:<6} | Error: {str(e)[:30]} |")


def analyze_dividend_growth(symbol: str = "JNJ"):
    """Analyze dividend growth over time."""
    print("\n" + "=" * 60)
    print(f"Dividend Growth Analysis for {symbol}")
    print("=" * 60)

    client = YFinanceClient()
    divs = client.get_dividends(symbol)

    if not divs.dividends:
        print("No dividend history available")
        return

    # Calculate annual totals
    annual_totals = {}
    for d in divs.dividends:
        year = d.date.year
        annual_totals[year] = annual_totals.get(year, 0) + d.dividend

    # Calculate growth rates
    years = sorted(annual_totals.keys())
    if len(years) < 2:
        print("Not enough history for growth analysis")
        return

    print("\n| Year | Annual Dividend | YoY Growth |")
    print("|------|-----------------|------------|")

    prev_total = None
    for year in years[-15:]:
        total = annual_totals[year]
        if prev_total and prev_total > 0:
            growth = ((total - prev_total) / prev_total) * 100
            growth_str = f"{growth:+.1f}%"
        else:
            growth_str = "N/A"

        print(f"| {year} | ${total:.4f} | {growth_str:>10} |")
        prev_total = total

    # Calculate CAGR if we have enough history
    if len(years) >= 5:
        first_year = years[-5]
        last_year = years[-1]
        first_val = annual_totals[first_year]
        last_val = annual_totals[last_year]
        if first_val > 0:
            cagr = ((last_val / first_val) ** (1 / 4) - 1) * 100
            print(f"\n5-Year CAGR: {cagr:.2f}%")


def fetch_indian_dividends():
    """Fetch dividend history for Indian stocks."""
    print("\n" + "=" * 60)
    print("Indian Stocks Dividend History")
    print("=" * 60)

    client = YFinanceClient()

    symbols = [
        ("RELIANCE.NS", "Reliance"),
        ("TCS.NS", "TCS"),
        ("INFY.NS", "Infosys"),
        ("ITC.NS", "ITC"),
        ("HDFCBANK.NS", "HDFC Bank"),
    ]

    print("\n| Stock | Recent Dividend | Annual Total |")
    print("|-------|-----------------|--------------|")

    for symbol, name in symbols:
        divs = client.get_dividends(symbol)

        if divs.dividends:
            recent = divs.dividends[-1].dividend
            recent_str = f"₹{recent:.2f}"

            # Sum last year's dividends
            from datetime import datetime, timedelta
            one_year_ago = datetime.now() - timedelta(days=365)
            annual = sum(
                d.dividend for d in divs.dividends
                if d.date.replace(tzinfo=None) > one_year_ago
            )
            annual_str = f"₹{annual:.2f}"
        else:
            recent_str = "N/A"
            annual_str = "N/A"

        print(f"| {name:<12} | {recent_str:>15} | {annual_str:>12} |")


if __name__ == "__main__":
    fetch_dividend_history("AAPL")
    fetch_split_history("AAPL")
    fetch_corporate_actions("AAPL")
    fetch_capital_gains("SPY")
    fetch_shares_history("AAPL")
    compare_dividend_yields()
    analyze_dividend_growth("JNJ")
    fetch_indian_dividends()
