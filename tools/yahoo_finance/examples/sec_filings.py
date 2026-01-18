"""Examples for SEC filings from Yahoo Finance.

This script demonstrates how to:
- Fetch SEC filings for US stocks
- Analyze filing types (10-K, 10-Q, 8-K, etc.)
- Track recent filings
- Note: SEC filings are only available for US stocks
"""

from tools.yahoo_finance import YFinanceClient
from collections import Counter


def fetch_sec_filings(symbol: str = "AAPL"):
    """Fetch SEC filings for a US stock."""
    print("=" * 60)
    print(f"SEC Filings for {symbol}")
    print("=" * 60)

    client = YFinanceClient()
    filings = client.get_sec_filings(symbol)

    print(f"\nTotal filings: {len(filings.filings)}")

    if not filings.filings:
        print("No SEC filings available (may not be a US stock)")
        return

    # Count filing types
    types = [f.type for f in filings.filings if f.type]
    type_counts = Counter(types)

    print("\n--- Filing Types ---")
    print("| Type | Count |")
    print("|------|-------|")
    for ftype, count in type_counts.most_common(10):
        print(f"| {ftype:<15} | {count:>5} |")


def fetch_recent_filings(symbol: str = "AAPL", limit: int = 15):
    """Fetch most recent SEC filings."""
    print("\n" + "=" * 60)
    print(f"Recent SEC Filings for {symbol}")
    print("=" * 60)

    client = YFinanceClient()
    filings = client.get_sec_filings(symbol)

    if not filings.filings:
        print("No SEC filings available")
        return

    print("\n| Date | Type | Title |")
    print("|------|------|-------|")

    for f in filings.filings[:limit]:
        date_str = f.date.strftime('%Y-%m-%d') if f.date else "N/A"
        type_str = f.type or "N/A"
        title_str = (f.title[:40] + "...") if f.title and len(f.title) > 40 else (f.title or "N/A")
        print(f"| {date_str} | {type_str:<12} | {title_str} |")


def analyze_annual_reports(symbol: str = "AAPL"):
    """Analyze 10-K annual reports."""
    print("\n" + "=" * 60)
    print(f"Annual Reports (10-K) for {symbol}")
    print("=" * 60)

    client = YFinanceClient()
    filings = client.get_sec_filings(symbol)

    if not filings.filings:
        print("No SEC filings available")
        return

    # Filter for 10-K filings
    annual_reports = [f for f in filings.filings if f.type and '10-K' in f.type]

    print(f"\nTotal 10-K filings: {len(annual_reports)}")

    if not annual_reports:
        print("No 10-K filings found")
        return

    print("\n| Date | Title | Exhibits |")
    print("|------|-------|----------|")

    for f in annual_reports[:10]:
        date_str = f.date.strftime('%Y-%m-%d') if f.date else "N/A"
        title_str = (f.title[:35] + "...") if f.title and len(f.title) > 35 else (f.title or "N/A")
        exhibits_count = len(f.exhibits) if f.exhibits else 0
        print(f"| {date_str} | {title_str:<40} | {exhibits_count:>8} |")


def analyze_quarterly_reports(symbol: str = "AAPL"):
    """Analyze 10-Q quarterly reports."""
    print("\n" + "=" * 60)
    print(f"Quarterly Reports (10-Q) for {symbol}")
    print("=" * 60)

    client = YFinanceClient()
    filings = client.get_sec_filings(symbol)

    if not filings.filings:
        print("No SEC filings available")
        return

    # Filter for 10-Q filings
    quarterly_reports = [f for f in filings.filings if f.type and '10-Q' in f.type]

    print(f"\nTotal 10-Q filings: {len(quarterly_reports)}")

    if not quarterly_reports:
        print("No 10-Q filings found")
        return

    print("\n| Date | Title |")
    print("|------|-------|")

    for f in quarterly_reports[:12]:
        date_str = f.date.strftime('%Y-%m-%d') if f.date else "N/A"
        title_str = (f.title[:50] + "...") if f.title and len(f.title) > 50 else (f.title or "N/A")
        print(f"| {date_str} | {title_str} |")


def analyze_current_reports(symbol: str = "AAPL"):
    """Analyze 8-K current reports (material events)."""
    print("\n" + "=" * 60)
    print(f"Current Reports (8-K) for {symbol}")
    print("=" * 60)

    client = YFinanceClient()
    filings = client.get_sec_filings(symbol)

    if not filings.filings:
        print("No SEC filings available")
        return

    # Filter for 8-K filings
    current_reports = [f for f in filings.filings if f.type and '8-K' in f.type]

    print(f"\nTotal 8-K filings: {len(current_reports)}")
    print("(8-K filings report material events like earnings, acquisitions, etc.)")

    if not current_reports:
        print("No 8-K filings found")
        return

    print("\n| Date | Title |")
    print("|------|-------|")

    for f in current_reports[:15]:
        date_str = f.date.strftime('%Y-%m-%d') if f.date else "N/A"
        title_str = (f.title[:50] + "...") if f.title and len(f.title) > 50 else (f.title or "N/A")
        print(f"| {date_str} | {title_str} |")


def analyze_proxy_statements(symbol: str = "AAPL"):
    """Analyze proxy statements (DEF 14A)."""
    print("\n" + "=" * 60)
    print(f"Proxy Statements for {symbol}")
    print("=" * 60)

    client = YFinanceClient()
    filings = client.get_sec_filings(symbol)

    if not filings.filings:
        print("No SEC filings available")
        return

    # Filter for DEF 14A (proxy statements)
    proxy_statements = [f for f in filings.filings if f.type and 'DEF 14A' in f.type]

    print(f"\nTotal proxy statements: {len(proxy_statements)}")
    print("(Proxy statements contain executive compensation, board info, etc.)")

    if not proxy_statements:
        print("No proxy statements found")
        return

    print("\n| Date | Title | Exhibits |")
    print("|------|-------|----------|")

    for f in proxy_statements[:5]:
        date_str = f.date.strftime('%Y-%m-%d') if f.date else "N/A"
        title_str = (f.title[:40] + "...") if f.title and len(f.title) > 40 else (f.title or "N/A")
        exhibits_count = len(f.exhibits) if f.exhibits else 0
        print(f"| {date_str} | {title_str:<45} | {exhibits_count:>8} |")


def compare_filings_across_companies():
    """Compare SEC filing activity across tech companies."""
    print("\n" + "=" * 60)
    print("SEC Filing Comparison - Tech Giants")
    print("=" * 60)

    client = YFinanceClient()
    symbols = ["AAPL", "MSFT", "GOOGL", "AMZN", "META"]

    print("\n| Company | Total Filings | 10-K | 10-Q | 8-K |")
    print("|---------|---------------|------|------|-----|")

    for symbol in symbols:
        filings = client.get_sec_filings(symbol)

        if filings.filings:
            total = len(filings.filings)
            k10 = len([f for f in filings.filings if f.type and '10-K' in f.type])
            q10 = len([f for f in filings.filings if f.type and '10-Q' in f.type])
            k8 = len([f for f in filings.filings if f.type and '8-K' in f.type])
            print(f"| {symbol:<7} | {total:>13} | {k10:>4} | {q10:>4} | {k8:>3} |")
        else:
            print(f"| {symbol:<7} | No data available |")


def fetch_filings_with_exhibits(symbol: str = "AAPL"):
    """Fetch filings that have exhibits attached."""
    print("\n" + "=" * 60)
    print(f"Filings with Exhibits for {symbol}")
    print("=" * 60)

    client = YFinanceClient()
    filings = client.get_sec_filings(symbol)

    if not filings.filings:
        print("No SEC filings available")
        return

    # Filter filings with exhibits
    with_exhibits = [f for f in filings.filings if f.exhibits and len(f.exhibits) > 0]

    print(f"\nFilings with exhibits: {len(with_exhibits)}")

    if not with_exhibits:
        print("No filings with exhibits found")
        return

    print("\n| Date | Type | Exhibits |")
    print("|------|------|----------|")

    for f in with_exhibits[:10]:
        date_str = f.date.strftime('%Y-%m-%d') if f.date else "N/A"
        type_str = f.type or "N/A"
        exhibit_count = len(f.exhibits)
        print(f"| {date_str} | {type_str:<12} | {exhibit_count} exhibits |")

        # Show first exhibit details
        if f.exhibits:
            for ex in f.exhibits[:2]:
                ex_name = ex.get('name', 'Unknown')
                print(f"|        |              | - {ex_name} |")


if __name__ == "__main__":
    fetch_sec_filings("AAPL")
    fetch_recent_filings("AAPL")
    analyze_annual_reports("AAPL")
    analyze_quarterly_reports("AAPL")
    analyze_current_reports("AAPL")
    analyze_proxy_statements("AAPL")
    compare_filings_across_companies()
    fetch_filings_with_exhibits("AAPL")
