"""Examples for fetching financial results comparison from NSE India.

This script demonstrates how to:
- Fetch quarterly financial results comparison
- Analyze revenue and profit trends
- Compare QoQ and YoY growth
- Access detailed expense breakdowns
"""

from tools.nse_india import NSEIndiaClient


def fetch_financial_comparison(symbol: str = "RELIANCE"):
    """Fetch financial results comparison for a company."""
    print("=" * 60)
    print(f"Financial Results Comparison for {symbol}")
    print("=" * 60)

    client = NSEIndiaClient()

    comparison = client.get_financial_results_comparison(symbol=symbol)

    print(f"Symbol: {comparison.symbol}")
    print(f"Banking/NBFC: {'Yes' if comparison.is_banking else 'No'}")
    print(f"Quarters available: {len(comparison.periods)}")
    print()

    if comparison.latest:
        latest = comparison.latest
        print("--- Latest Quarter ---")
        print(f"Period: {latest.quarter} (ended {latest.period_label})")
        print(f"Audited: {'Yes' if latest.is_audited else 'No'}")
        print(f"Revenue: ₹{latest.net_sales:,.0f} Lakhs" if latest.net_sales else "Revenue: N/A")
        print(f"Net Profit: ₹{latest.net_profit:,.0f} Lakhs" if latest.net_profit else "Net Profit: N/A")
        
        eps = latest.basic_eps_continuing or latest.basic_eps
        if eps:
            print(f"EPS: ₹{eps:.2f}")
        
        if latest.net_profit_margin:
            print(f"Net Profit Margin: {latest.net_profit_margin:.1f}%")
        
        if latest.ebitda:
            print(f"EBITDA: ₹{latest.ebitda:,.0f} Lakhs")
        print()

    client.close()
    return comparison


def analyze_growth_trends(symbol: str = "RELIANCE"):
    """Analyze QoQ and YoY growth trends."""
    print("\n" + "=" * 60)
    print(f"Growth Analysis for {symbol}")
    print("=" * 60)

    client = NSEIndiaClient()

    comparison = client.get_financial_results_comparison(symbol=symbol)

    print("\n--- Growth Analysis ---")
    
    # QoQ Growth
    if comparison.revenue_growth_qoq is not None:
        print(f"Revenue Growth (QoQ): {comparison.revenue_growth_qoq:+.1f}%")
    if comparison.profit_growth_qoq is not None:
        print(f"Profit Growth (QoQ): {comparison.profit_growth_qoq:+.1f}%")
    
    # YoY Growth
    if comparison.revenue_growth_yoy is not None:
        print(f"Revenue Growth (YoY): {comparison.revenue_growth_yoy:+.1f}%")
    if comparison.profit_growth_yoy is not None:
        print(f"Profit Growth (YoY): {comparison.profit_growth_yoy:+.1f}%")

    client.close()


def show_quarterly_trend(symbol: str = "RELIANCE"):
    """Show quarterly trend for key metrics."""
    print("\n" + "=" * 60)
    print(f"Quarterly Trend for {symbol}")
    print("=" * 60)

    client = NSEIndiaClient()

    trends = client.get_results_comparison_trend(symbol=symbol, num_quarters=6)

    print("\n--- Revenue Trend (₹ Lakhs) ---")
    for period, value in trends["revenue"]:
        if value:
            print(f"  {period}: ₹{value:,.0f}")

    print("\n--- Net Profit Trend (₹ Lakhs) ---")
    for period, value in trends["profit"]:
        if value:
            print(f"  {period}: ₹{value:,.0f}")

    print("\n--- EPS Trend ---")
    for period, value in trends["eps"]:
        if value:
            print(f"  {period}: ₹{value:.2f}")

    print("\n--- Net Profit Margin Trend ---")
    for period, value in trends["margin"]:
        if value:
            print(f"  {period}: {value:.1f}%")

    client.close()


def show_expense_breakdown(symbol: str = "RELIANCE"):
    """Show expense breakdown for latest quarter."""
    print("\n" + "=" * 60)
    print(f"Expense Breakdown for {symbol}")
    print("=" * 60)

    client = NSEIndiaClient()

    comparison = client.get_financial_results_comparison(symbol=symbol)
    latest = comparison.latest

    if not latest:
        print("No data available")
        client.close()
        return

    print(f"\nQuarter: {latest.quarter} (ended {latest.period_label})")
    print("\n--- Expenses (₹ Lakhs) ---")

    def pct(v):
        if v and latest.net_sales:
            return f"({v / latest.net_sales * 100:.1f}% of revenue)"
        return ""

    if latest.raw_material_consumed:
        print(f"  Raw Materials: ₹{latest.raw_material_consumed:,.0f} {pct(latest.raw_material_consumed)}")
    if latest.purchase_traded_goods:
        print(f"  Traded Goods: ₹{latest.purchase_traded_goods:,.0f} {pct(latest.purchase_traded_goods)}")
    if latest.staff_cost:
        print(f"  Employee Cost: ₹{latest.staff_cost:,.0f} {pct(latest.staff_cost)}")
    if latest.depreciation:
        print(f"  Depreciation: ₹{latest.depreciation:,.0f} {pct(latest.depreciation)}")
    if latest.interest_expense:
        print(f"  Interest: ₹{latest.interest_expense:,.0f} {pct(latest.interest_expense)}")
    if latest.other_expenses:
        print(f"  Other Expenses: ₹{latest.other_expenses:,.0f} {pct(latest.other_expenses)}")
    if latest.total_expenses:
        print(f"  Total Expenses: ₹{latest.total_expenses:,.0f} {pct(latest.total_expenses)}")

    client.close()


def compare_companies():
    """Compare financial metrics across multiple companies."""
    print("\n" + "=" * 60)
    print("Financial Comparison Across Companies")
    print("=" * 60)

    symbols = ["RELIANCE", "TCS", "INFY", "HDFCBANK", "ICICIBANK"]

    client = NSEIndiaClient()

    print(f"\n{'Company':<12} {'Revenue (Cr)':<15} {'Profit (Cr)':<15} {'NPM %':<10} {'EPS':<8}")
    print("-" * 60)

    for symbol in symbols:
        try:
            comparison = client.get_financial_results_comparison(symbol=symbol)
            latest = comparison.latest
            
            if latest:
                revenue = f"₹{latest.net_sales / 100:,.0f}" if latest.net_sales else "-"
                profit = f"₹{latest.net_profit / 100:,.0f}" if latest.net_profit else "-"
                npm = f"{latest.net_profit_margin:.1f}%" if latest.net_profit_margin else "-"
                eps = latest.basic_eps_continuing or latest.basic_eps
                eps_str = f"₹{eps:.2f}" if eps else "-"
                
                print(f"{symbol:<12} {revenue:<15} {profit:<15} {npm:<10} {eps_str:<8}")
            else:
                print(f"{symbol:<12} No data available")
        except Exception as e:
            print(f"{symbol:<12} Error: {str(e)[:30]}")

    client.close()


def get_latest_quarter_summary(symbol: str = "RELIANCE"):
    """Get a quick summary of the latest quarter."""
    print("\n" + "=" * 60)
    print(f"Latest Quarter Summary for {symbol}")
    print("=" * 60)

    client = NSEIndiaClient()

    summary = client.get_latest_quarter_comparison(symbol=symbol)

    for key, value in summary.items():
        if value is not None:
            if "growth" in key and isinstance(value, (int, float)):
                print(f"  {key}: {value:+.1f}%")
            elif "lakhs" in key and isinstance(value, (int, float)):
                print(f"  {key}: ₹{value:,.0f}")
            elif "margin" in key and isinstance(value, (int, float)):
                print(f"  {key}: {value:.1f}%")
            else:
                print(f"  {key}: {value}")

    client.close()


def use_toolkit_method(symbol: str = "TCS"):
    """Demonstrate using the toolkit method for formatted output."""
    print("\n" + "=" * 60)
    print(f"Toolkit Output for {symbol}")
    print("=" * 60)

    from tools.nse_india import NSEIndiaToolkit

    toolkit = NSEIndiaToolkit()
    result = toolkit.get_financial_results_comparison(symbol)
    print(result)


if __name__ == "__main__":
    fetch_financial_comparison("RELIANCE")
    analyze_growth_trends("RELIANCE")
    show_quarterly_trend("TCS")
    show_expense_breakdown("INFY")
    compare_companies()
    get_latest_quarter_summary("HDFCBANK")
    # use_toolkit_method("TCS")  # Uncomment to see formatted markdown output
