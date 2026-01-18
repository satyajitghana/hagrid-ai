"""Examples for fetching financial statements from Yahoo Finance.

This script demonstrates how to:
- Fetch income statements (annual and quarterly)
- Fetch balance sheets
- Fetch cash flow statements
- Analyze financial trends
- Compare financials across companies
"""

from tools.yahoo_finance import YFinanceClient


def format_number(value, prefix="$"):
    """Format large numbers for display."""
    if value is None or value != value:  # NaN check
        return "N/A"
    try:
        value = float(value)
        if abs(value) >= 1e12:
            return f"{prefix}{value/1e12:.2f}T"
        elif abs(value) >= 1e9:
            return f"{prefix}{value/1e9:.2f}B"
        elif abs(value) >= 1e6:
            return f"{prefix}{value/1e6:.2f}M"
        elif abs(value) >= 1e3:
            return f"{prefix}{value/1e3:.2f}K"
        else:
            return f"{prefix}{value:.2f}"
    except (ValueError, TypeError):
        return "N/A"


def fetch_income_statement(symbol: str = "AAPL"):
    """Fetch and display income statement."""
    print("=" * 60)
    print(f"Income Statement for {symbol}")
    print("=" * 60)

    client = YFinanceClient()
    financials = client.get_financials(symbol)

    print(f"\nAnnual Income Statement (Most Recent Periods)")
    print("-" * 60)

    if not financials.income_statement:
        print("No income statement data available")
        return

    # Get periods (dates)
    periods = financials.income_statement[:4]  # Last 4 periods
    if not periods:
        print("No data available")
        return

    # Key metrics to display
    key_metrics = [
        "Total Revenue",
        "Cost Of Revenue",
        "Gross Profit",
        "Operating Expense",
        "Operating Income",
        "EBITDA",
        "Interest Expense",
        "Pretax Income",
        "Tax Provision",
        "Net Income",
        "Basic EPS",
        "Diluted EPS"
    ]

    # Print header
    dates = [p.get('Date', 'N/A')[:10] for p in periods]
    print(f"\n| Metric                    | {' | '.join(f'{d:>12}' for d in dates)} |")
    print("|---------------------------|" + "|".join(["-" * 14 for _ in dates]) + "|")

    for metric in key_metrics:
        values = []
        for p in periods:
            val = p.get(metric)
            values.append(format_number(val))
        print(f"| {metric:<25} | {' | '.join(f'{v:>12}' for v in values)} |")


def fetch_quarterly_income_statement(symbol: str = "MSFT"):
    """Fetch and display quarterly income statement."""
    print("\n" + "=" * 60)
    print(f"Quarterly Income Statement for {symbol}")
    print("=" * 60)

    client = YFinanceClient()
    financials = client.get_financials(symbol)

    if not financials.quarterly_income_statement:
        print("No quarterly income statement data available")
        return

    periods = financials.quarterly_income_statement[:4]

    key_metrics = [
        "Total Revenue",
        "Gross Profit",
        "Operating Income",
        "Net Income",
        "Diluted EPS"
    ]

    dates = [p.get('Date', 'N/A')[:10] for p in periods]
    print(f"\n| Metric                    | {' | '.join(f'{d:>12}' for d in dates)} |")
    print("|---------------------------|" + "|".join(["-" * 14 for _ in dates]) + "|")

    for metric in key_metrics:
        values = []
        for p in periods:
            val = p.get(metric)
            values.append(format_number(val))
        print(f"| {metric:<25} | {' | '.join(f'{v:>12}' for v in values)} |")


def fetch_balance_sheet(symbol: str = "GOOGL"):
    """Fetch and display balance sheet."""
    print("\n" + "=" * 60)
    print(f"Balance Sheet for {symbol}")
    print("=" * 60)

    client = YFinanceClient()
    financials = client.get_financials(symbol)

    if not financials.balance_sheet:
        print("No balance sheet data available")
        return

    periods = financials.balance_sheet[:4]

    print("\n--- Assets ---")
    asset_metrics = [
        "Total Assets",
        "Current Assets",
        "Cash And Cash Equivalents",
        "Accounts Receivable",
        "Inventory",
        "Net PPE",
        "Goodwill",
        "Intangible Assets"
    ]

    dates = [p.get('Date', 'N/A')[:10] for p in periods]
    print(f"\n| Metric                    | {' | '.join(f'{d:>12}' for d in dates)} |")
    print("|---------------------------|" + "|".join(["-" * 14 for _ in dates]) + "|")

    for metric in asset_metrics:
        values = []
        for p in periods:
            val = p.get(metric)
            values.append(format_number(val))
        print(f"| {metric:<25} | {' | '.join(f'{v:>12}' for v in values)} |")

    print("\n--- Liabilities & Equity ---")
    liability_metrics = [
        "Total Liabilities Net Minority Interest",
        "Current Liabilities",
        "Accounts Payable",
        "Long Term Debt",
        "Total Debt",
        "Stockholders Equity",
        "Retained Earnings",
        "Common Stock"
    ]

    print(f"\n| Metric                                  | {' | '.join(f'{d:>12}' for d in dates)} |")
    print("|-----------------------------------------|" + "|".join(["-" * 14 for _ in dates]) + "|")

    for metric in liability_metrics:
        values = []
        for p in periods:
            val = p.get(metric)
            values.append(format_number(val))
        print(f"| {metric:<39} | {' | '.join(f'{v:>12}' for v in values)} |")


def fetch_cash_flow(symbol: str = "AMZN"):
    """Fetch and display cash flow statement."""
    print("\n" + "=" * 60)
    print(f"Cash Flow Statement for {symbol}")
    print("=" * 60)

    client = YFinanceClient()
    financials = client.get_financials(symbol)

    if not financials.cash_flow:
        print("No cash flow data available")
        return

    periods = financials.cash_flow[:4]

    print("\n--- Operating Cash Flow ---")
    operating_metrics = [
        "Operating Cash Flow",
        "Net Income From Continuing Operations",
        "Depreciation And Amortization",
        "Change In Working Capital",
        "Stock Based Compensation"
    ]

    dates = [p.get('Date', 'N/A')[:10] for p in periods]
    print(f"\n| Metric                                  | {' | '.join(f'{d:>12}' for d in dates)} |")
    print("|-----------------------------------------|" + "|".join(["-" * 14 for _ in dates]) + "|")

    for metric in operating_metrics:
        values = []
        for p in periods:
            val = p.get(metric)
            values.append(format_number(val))
        print(f"| {metric:<39} | {' | '.join(f'{v:>12}' for v in values)} |")

    print("\n--- Investing Cash Flow ---")
    investing_metrics = [
        "Investing Cash Flow",
        "Capital Expenditure",
        "Purchase Of Investment",
        "Sale Of Investment"
    ]

    print(f"\n| Metric                                  | {' | '.join(f'{d:>12}' for d in dates)} |")
    print("|-----------------------------------------|" + "|".join(["-" * 14 for _ in dates]) + "|")

    for metric in investing_metrics:
        values = []
        for p in periods:
            val = p.get(metric)
            values.append(format_number(val))
        print(f"| {metric:<39} | {' | '.join(f'{v:>12}' for v in values)} |")

    print("\n--- Financing Cash Flow ---")
    financing_metrics = [
        "Financing Cash Flow",
        "Repurchase Of Capital Stock",
        "Cash Dividends Paid",
        "Repayment Of Debt",
        "Issuance Of Debt"
    ]

    print(f"\n| Metric                                  | {' | '.join(f'{d:>12}' for d in dates)} |")
    print("|-----------------------------------------|" + "|".join(["-" * 14 for _ in dates]) + "|")

    for metric in financing_metrics:
        values = []
        for p in periods:
            val = p.get(metric)
            values.append(format_number(val))
        print(f"| {metric:<39} | {' | '.join(f'{v:>12}' for v in values)} |")


def analyze_profitability_trends(symbol: str = "NVDA"):
    """Analyze profitability trends from income statement."""
    print("\n" + "=" * 60)
    print(f"Profitability Analysis for {symbol}")
    print("=" * 60)

    client = YFinanceClient()
    financials = client.get_financials(symbol)

    if not financials.income_statement:
        print("No income statement data available")
        return

    periods = financials.income_statement[:4]

    print("\n--- Margin Analysis ---")
    print(f"| Period     | Gross Margin | Operating Margin | Net Margin |")
    print("|------------|--------------|------------------|------------|")

    for p in periods:
        date = p.get('Date', 'N/A')[:10]
        revenue = p.get('Total Revenue', 0) or 0
        gross_profit = p.get('Gross Profit', 0) or 0
        operating_income = p.get('Operating Income', 0) or 0
        net_income = p.get('Net Income', 0) or 0

        if revenue and revenue > 0:
            gross_margin = (gross_profit / revenue) * 100
            operating_margin = (operating_income / revenue) * 100
            net_margin = (net_income / revenue) * 100
            print(f"| {date} | {gross_margin:>11.1f}% | {operating_margin:>15.1f}% | {net_margin:>9.1f}% |")
        else:
            print(f"| {date} | N/A          | N/A              | N/A        |")


def analyze_growth_rates(symbol: str = "META"):
    """Analyze year-over-year growth rates."""
    print("\n" + "=" * 60)
    print(f"Growth Analysis for {symbol}")
    print("=" * 60)

    client = YFinanceClient()
    financials = client.get_financials(symbol)

    if not financials.income_statement or len(financials.income_statement) < 2:
        print("Insufficient data for growth analysis")
        return

    periods = financials.income_statement[:4]

    print("\n--- Year-over-Year Growth ---")
    print(f"| Period     | Revenue Growth | Profit Growth | EPS Growth |")
    print("|------------|----------------|---------------|------------|")

    for i in range(len(periods) - 1):
        current = periods[i]
        previous = periods[i + 1]

        date = current.get('Date', 'N/A')[:10]

        curr_rev = current.get('Total Revenue', 0) or 0
        prev_rev = previous.get('Total Revenue', 0) or 0

        curr_ni = current.get('Net Income', 0) or 0
        prev_ni = previous.get('Net Income', 0) or 0

        curr_eps = current.get('Diluted EPS', 0) or 0
        prev_eps = previous.get('Diluted EPS', 0) or 0

        rev_growth = ((curr_rev - prev_rev) / prev_rev * 100) if prev_rev else 0
        ni_growth = ((curr_ni - prev_ni) / prev_ni * 100) if prev_ni else 0
        eps_growth = ((curr_eps - prev_eps) / prev_eps * 100) if prev_eps else 0

        print(f"| {date} | {rev_growth:>+13.1f}% | {ni_growth:>+12.1f}% | {eps_growth:>+9.1f}% |")


def compare_financials_across_companies():
    """Compare key financial metrics across companies."""
    print("\n" + "=" * 60)
    print("Financial Comparison Across Tech Giants")
    print("=" * 60)

    symbols = ["AAPL", "MSFT", "GOOGL", "AMZN", "META"]
    client = YFinanceClient()

    print("\n| Company | Revenue     | Net Income  | Gross Margin | Net Margin |")
    print("|---------|-------------|-------------|--------------|------------|")

    for symbol in symbols:
        try:
            financials = client.get_financials(symbol)

            if not financials.income_statement:
                print(f"| {symbol:<7} | No data available |")
                continue

            latest = financials.income_statement[0]
            revenue = latest.get('Total Revenue', 0) or 0
            net_income = latest.get('Net Income', 0) or 0
            gross_profit = latest.get('Gross Profit', 0) or 0

            gross_margin = (gross_profit / revenue * 100) if revenue else 0
            net_margin = (net_income / revenue * 100) if revenue else 0

            print(f"| {symbol:<7} | {format_number(revenue):>11} | {format_number(net_income):>11} | {gross_margin:>11.1f}% | {net_margin:>9.1f}% |")
        except Exception as e:
            print(f"| {symbol:<7} | Error: {str(e)[:30]} |")


def fetch_indian_company_financials(symbol: str = "RELIANCE.NS"):
    """Fetch financials for Indian companies."""
    print("\n" + "=" * 60)
    print(f"Financials for {symbol.replace('.NS', '')} (NSE)")
    print("=" * 60)

    client = YFinanceClient()
    financials = client.get_financials(symbol)

    if not financials.income_statement:
        print("No income statement data available")
        return

    periods = financials.income_statement[:4]

    key_metrics = [
        "Total Revenue",
        "Gross Profit",
        "Operating Income",
        "Net Income",
        "Diluted EPS"
    ]

    dates = [p.get('Date', 'N/A')[:10] for p in periods]
    print(f"\n| Metric                    | {' | '.join(f'{d:>12}' for d in dates)} |")
    print("|---------------------------|" + "|".join(["-" * 14 for _ in dates]) + "|")

    for metric in key_metrics:
        values = []
        for p in periods:
            val = p.get(metric)
            # For Indian stocks, format in INR
            values.append(format_number(val, prefix=""))
        print(f"| {metric:<25} | {' | '.join(f'{v:>12}' for v in values)} |")


def analyze_cash_generation(symbol: str = "JNJ"):
    """Analyze cash generation and usage."""
    print("\n" + "=" * 60)
    print(f"Cash Generation Analysis for {symbol}")
    print("=" * 60)

    client = YFinanceClient()
    financials = client.get_financials(symbol)

    if not financials.cash_flow or not financials.income_statement:
        print("Insufficient data for analysis")
        return

    print("\n--- Cash Flow vs Net Income ---")
    print(f"| Period     | Net Income  | Operating CF | FCF         | CF/NI Ratio |")
    print("|------------|-------------|--------------|-------------|-------------|")

    cf_periods = financials.cash_flow[:4]
    is_periods = financials.income_statement[:4]

    for i, cf in enumerate(cf_periods):
        date = cf.get('Date', 'N/A')[:10]
        ocf = cf.get('Operating Cash Flow', 0) or 0
        capex = cf.get('Capital Expenditure', 0) or 0
        fcf = ocf + capex  # capex is negative

        ni = 0
        if i < len(is_periods):
            ni = is_periods[i].get('Net Income', 0) or 0

        cf_ni_ratio = (ocf / ni) if ni and ni != 0 else 0

        print(f"| {date} | {format_number(ni):>11} | {format_number(ocf):>12} | {format_number(fcf):>11} | {cf_ni_ratio:>10.2f}x |")


def show_quarterly_balance_sheet(symbol: str = "TSLA"):
    """Show quarterly balance sheet data."""
    print("\n" + "=" * 60)
    print(f"Quarterly Balance Sheet for {symbol}")
    print("=" * 60)

    client = YFinanceClient()
    financials = client.get_financials(symbol)

    if not financials.quarterly_balance_sheet:
        print("No quarterly balance sheet data available")
        return

    periods = financials.quarterly_balance_sheet[:4]

    key_metrics = [
        "Total Assets",
        "Total Liabilities Net Minority Interest",
        "Stockholders Equity",
        "Cash And Cash Equivalents",
        "Total Debt",
        "Current Assets",
        "Current Liabilities"
    ]

    dates = [p.get('Date', 'N/A')[:10] for p in periods]
    print(f"\n| Metric                                  | {' | '.join(f'{d:>12}' for d in dates)} |")
    print("|-----------------------------------------|" + "|".join(["-" * 14 for _ in dates]) + "|")

    for metric in key_metrics:
        values = []
        for p in periods:
            val = p.get(metric)
            values.append(format_number(val))
        print(f"| {metric:<39} | {' | '.join(f'{v:>12}' for v in values)} |")


if __name__ == "__main__":
    # Run all examples
    fetch_income_statement("AAPL")
    fetch_quarterly_income_statement("MSFT")
    fetch_balance_sheet("GOOGL")
    fetch_cash_flow("AMZN")
    analyze_profitability_trends("NVDA")
    analyze_growth_rates("META")
    compare_financials_across_companies()
    fetch_indian_company_financials("RELIANCE.NS")
    analyze_cash_generation("JNJ")
    show_quarterly_balance_sheet("TSLA")
