"""Examples for ETF and Mutual Fund data from Yahoo Finance.

This script demonstrates how to:
- Fetch fund holdings and allocations
- Analyze sector weightings
- Get fund operations and fees
- Compare multiple ETFs
- Note: Works with ETFs and Mutual Funds only
"""

from tools.yahoo_finance import YFinanceClient


def fetch_fund_overview(symbol: str = "SPY"):
    """Fetch overview data for an ETF/Mutual Fund."""
    print("=" * 60)
    print(f"Fund Overview for {symbol}")
    print("=" * 60)

    client = YFinanceClient()
    fd = client.get_funds_data(symbol)

    print(f"\nDescription: {fd.description[:200]}..." if fd.description else "\nNo description available")

    print("\n--- Fund Performance ---")
    perf = fd.fund_performance
    if perf:
        for key, value in list(perf.items())[:10]:
            print(f"{key}: {value}")
    else:
        print("No performance data available")


def fetch_fund_holdings(symbol: str = "SPY"):
    """Fetch top holdings for an ETF/Mutual Fund."""
    print("\n" + "=" * 60)
    print(f"Top Holdings for {symbol}")
    print("=" * 60)

    client = YFinanceClient()
    fd = client.get_funds_data(symbol)

    top_holdings = fd.top_holdings
    if not top_holdings:
        print("No holdings data available")
        return

    print(f"\nTotal top holdings: {len(top_holdings)}")

    print("\n| Symbol | Name | Weight |")
    print("|--------|------|--------|")

    for holding in top_holdings[:15]:
        sym = holding.get('symbol', 'N/A')
        name = holding.get('holdingName', 'N/A')
        if len(name) > 30:
            name = name[:27] + "..."
        weight = holding.get('holdingPercent', 0)
        weight_str = f"{weight:.2%}" if weight else "N/A"
        print(f"| {sym:<6} | {name:<30} | {weight_str:>6} |")


def fetch_sector_weightings(symbol: str = "SPY"):
    """Fetch sector allocation for an ETF."""
    print("\n" + "=" * 60)
    print(f"Sector Weightings for {symbol}")
    print("=" * 60)

    client = YFinanceClient()
    fd = client.get_funds_data(symbol)

    sector_weights = fd.sector_weightings
    if not sector_weights:
        print("No sector weightings available")
        return

    print("\n| Sector | Weight |")
    print("|--------|--------|")

    # sector_weights is a dict
    if isinstance(sector_weights, dict):
        for sector, weight in sector_weights.items():
            weight_val = weight if isinstance(weight, (int, float)) else 0
            print(f"| {sector:<25} | {weight_val:>6.2%} |")
    elif isinstance(sector_weights, list):
        for item in sector_weights:
            if isinstance(item, dict):
                for sector, weight in item.items():
                    weight_val = weight if isinstance(weight, (int, float)) else 0
                    print(f"| {sector:<25} | {weight_val:>6.2%} |")


def fetch_equity_holdings(symbol: str = "SPY"):
    """Fetch equity holdings details for an ETF."""
    print("\n" + "=" * 60)
    print(f"Equity Holdings Details for {symbol}")
    print("=" * 60)

    client = YFinanceClient()
    fd = client.get_funds_data(symbol)

    eq_holdings = fd.equity_holdings
    if not eq_holdings:
        print("No equity holdings data available")
        return

    print("\n--- Equity Statistics ---")
    for key, value in eq_holdings.items():
        if value is not None:
            if isinstance(value, float):
                print(f"{key}: {value:.4f}")
            else:
                print(f"{key}: {value}")


def fetch_bond_holdings(symbol: str = "BND"):
    """Fetch bond holdings details for a bond ETF."""
    print("\n" + "=" * 60)
    print(f"Bond Holdings Details for {symbol}")
    print("=" * 60)

    client = YFinanceClient()
    fd = client.get_funds_data(symbol)

    bond_holdings = fd.bond_holdings
    if not bond_holdings:
        print("No bond holdings data available")
        return

    print("\n--- Bond Statistics ---")
    for key, value in bond_holdings.items():
        if value is not None:
            if isinstance(value, float):
                print(f"{key}: {value:.4f}")
            else:
                print(f"{key}: {value}")

    # Also show bond ratings if available
    bond_ratings = fd.bond_ratings
    if bond_ratings:
        print("\n--- Bond Ratings ---")
        for key, value in bond_ratings.items():
            if value is not None:
                print(f"{key}: {value:.2%}" if isinstance(value, float) else f"{key}: {value}")


def fetch_fund_operations(symbol: str = "SPY"):
    """Fetch fund operations and fees."""
    print("\n" + "=" * 60)
    print(f"Fund Operations for {symbol}")
    print("=" * 60)

    client = YFinanceClient()
    fd = client.get_funds_data(symbol)

    ops = fd.fund_operations
    if not ops:
        print("No operations data available")
        return

    print("\n--- Fee Structure ---")
    for key, value in ops.items():
        if value is not None:
            if 'ratio' in key.lower() or 'fee' in key.lower():
                if isinstance(value, (int, float)):
                    print(f"{key}: {value:.4%}")
                else:
                    print(f"{key}: {value}")
            else:
                print(f"{key}: {value}")


def fetch_asset_classes(symbol: str = "AOA"):
    """Fetch asset class breakdown for a multi-asset ETF."""
    print("\n" + "=" * 60)
    print(f"Asset Class Breakdown for {symbol}")
    print("=" * 60)

    client = YFinanceClient()
    fd = client.get_funds_data(symbol)

    asset_classes = fd.asset_classes
    if not asset_classes:
        print("No asset class data available")
        return

    print("\n| Asset Class | Weight |")
    print("|-------------|--------|")

    if isinstance(asset_classes, dict):
        for asset, weight in asset_classes.items():
            weight_val = weight if isinstance(weight, (int, float)) else 0
            print(f"| {asset:<20} | {weight_val:>6.2%} |")


def compare_etfs():
    """Compare multiple popular ETFs."""
    print("\n" + "=" * 60)
    print("ETF Comparison")
    print("=" * 60)

    client = YFinanceClient()

    etfs = [
        ("SPY", "S&P 500"),
        ("QQQ", "Nasdaq 100"),
        ("DIA", "Dow Jones"),
        ("IWM", "Russell 2000"),
        ("VTI", "Total Stock Market"),
    ]

    print("\n| ETF | Name | Top Holding | Holdings Count |")
    print("|-----|------|-------------|----------------|")

    for symbol, name in etfs:
        fd = client.get_funds_data(symbol)

        if fd.top_holdings:
            top = fd.top_holdings[0]
            top_name = top.get('symbol', 'N/A')
            count = len(fd.top_holdings)
        else:
            top_name = "N/A"
            count = 0

        print(f"| {symbol:<3} | {name:<18} | {top_name:<11} | {count:>14} |")


def compare_sector_etfs():
    """Compare sector ETFs and their top holdings."""
    print("\n" + "=" * 60)
    print("Sector ETFs Comparison")
    print("=" * 60)

    client = YFinanceClient()

    sector_etfs = [
        ("XLK", "Technology"),
        ("XLF", "Financials"),
        ("XLV", "Healthcare"),
        ("XLE", "Energy"),
        ("XLY", "Consumer Disc."),
        ("XLP", "Consumer Staples"),
        ("XLI", "Industrials"),
        ("XLU", "Utilities"),
    ]

    print("\n| ETF | Sector | Top 3 Holdings |")
    print("|-----|--------|----------------|")

    for symbol, sector in sector_etfs:
        fd = client.get_funds_data(symbol)

        if fd.top_holdings:
            top_3 = [h.get('symbol', '?') for h in fd.top_holdings[:3]]
            top_str = ", ".join(top_3)
        else:
            top_str = "N/A"

        print(f"| {symbol:<3} | {sector:<15} | {top_str:<25} |")


def fetch_international_etfs():
    """Fetch data for international ETFs."""
    print("\n" + "=" * 60)
    print("International ETFs")
    print("=" * 60)

    client = YFinanceClient()

    intl_etfs = [
        ("EEM", "Emerging Markets"),
        ("VEA", "Developed Markets ex-US"),
        ("EFA", "EAFE (Europe, Aus, Far East)"),
        ("INDA", "India"),
        ("FXI", "China Large Cap"),
    ]

    print("\n| ETF | Region | Top Holding | Weight |")
    print("|-----|--------|-------------|--------|")

    for symbol, region in intl_etfs:
        fd = client.get_funds_data(symbol)

        if fd.top_holdings:
            top = fd.top_holdings[0]
            top_name = top.get('symbol', 'N/A')
            weight = top.get('holdingPercent', 0)
            weight_str = f"{weight:.2%}" if weight else "N/A"
        else:
            top_name = "N/A"
            weight_str = "N/A"

        print(f"| {symbol:<4} | {region:<25} | {top_name:<11} | {weight_str:>6} |")


def fetch_bond_etfs():
    """Fetch data for bond ETFs."""
    print("\n" + "=" * 60)
    print("Bond ETFs")
    print("=" * 60)

    client = YFinanceClient()

    bond_etfs = [
        ("BND", "Total Bond Market"),
        ("AGG", "Aggregate Bond"),
        ("TLT", "20+ Year Treasury"),
        ("LQD", "Investment Grade Corp"),
        ("HYG", "High Yield Corporate"),
    ]

    print("\n| ETF | Description |")
    print("|-----|-------------|")

    for symbol, desc in bond_etfs:
        fd = client.get_funds_data(symbol)
        print(f"| {symbol:<3} | {desc:<25} |")

        bond_h = fd.bond_holdings
        if bond_h:
            print(f"|     | Avg Maturity: {bond_h.get('maturity', 'N/A')} |")
            print(f"|     | Avg Duration: {bond_h.get('duration', 'N/A')} |")


def fetch_mutual_fund_data(symbol: str = "VFIAX"):
    """Fetch data for a mutual fund."""
    print("\n" + "=" * 60)
    print(f"Mutual Fund Data for {symbol}")
    print("=" * 60)

    client = YFinanceClient()
    fd = client.get_funds_data(symbol)

    print(f"\nDescription: {fd.description[:150]}..." if fd.description else "\nNo description")

    print("\n--- Top Holdings ---")
    if fd.top_holdings:
        for h in fd.top_holdings[:5]:
            name = h.get('holdingName', 'N/A')
            weight = h.get('holdingPercent', 0)
            print(f"  {name[:30]:<30} {weight:.2%}" if weight else f"  {name[:30]}")
    else:
        print("  No holdings data")

    print("\n--- Fund Operations ---")
    ops = fd.fund_operations
    if ops:
        exp_ratio = ops.get('annualReportExpenseRatio')
        if exp_ratio:
            print(f"  Expense Ratio: {exp_ratio:.4%}")
        turnover = ops.get('annualHoldingsTurnover')
        if turnover:
            print(f"  Turnover: {turnover:.2%}")


if __name__ == "__main__":
    fetch_fund_overview("SPY")
    fetch_fund_holdings("SPY")
    fetch_sector_weightings("SPY")
    fetch_equity_holdings("SPY")
    fetch_bond_holdings("BND")
    fetch_fund_operations("SPY")
    fetch_asset_classes("AOA")
    compare_etfs()
    compare_sector_etfs()
    fetch_international_etfs()
    fetch_bond_etfs()
    fetch_mutual_fund_data("VFIAX")
