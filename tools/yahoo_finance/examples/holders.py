"""Examples for fetching holder information from Yahoo Finance.

This script demonstrates how to:
- Fetch major holders breakdown
- Get institutional holders
- Get mutual fund holders
- Get insider roster and transactions
- Compare holder structure across companies
"""

from tools.yahoo_finance import YFinanceClient


def format_shares(shares):
    """Format share numbers for display."""
    if shares is None or (isinstance(shares, float) and shares != shares):
        return "N/A"
    try:
        shares = int(float(shares))
        if shares >= 1e9:
            return f"{shares/1e9:.2f}B"
        elif shares >= 1e6:
            return f"{shares/1e6:.2f}M"
        elif shares >= 1e3:
            return f"{shares/1e3:.1f}K"
        else:
            return str(shares)
    except (ValueError, TypeError):
        return "N/A"


def format_value(value):
    """Format dollar values for display."""
    if value is None or (isinstance(value, float) and value != value):
        return "N/A"
    try:
        value = float(value)
        if value >= 1e12:
            return f"${value/1e12:.2f}T"
        elif value >= 1e9:
            return f"${value/1e9:.2f}B"
        elif value >= 1e6:
            return f"${value/1e6:.2f}M"
        else:
            return f"${value:,.0f}"
    except (ValueError, TypeError):
        return "N/A"


def fetch_major_holders(symbol: str = "AAPL"):
    """Fetch major holders breakdown."""
    print("=" * 60)
    print(f"Major Holders Breakdown for {symbol}")
    print("=" * 60)

    client = YFinanceClient()
    holders = client.get_holders(symbol)

    print(f"\nSymbol: {holders.symbol}")
    print()

    if not holders.major_holders:
        print("No major holders data available")
        return

    print("--- Ownership Breakdown ---")
    for h in holders.major_holders:
        # major_holders typically has columns like 'Value' and '0' (description)
        value = h.get('Value', h.get(0, 'N/A'))
        desc = h.get('Breakdown', h.get(1, 'N/A'))
        print(f"  {desc}: {value}")


def fetch_institutional_holders(symbol: str = "MSFT"):
    """Fetch top institutional holders."""
    print("\n" + "=" * 60)
    print(f"Institutional Holders for {symbol}")
    print("=" * 60)

    client = YFinanceClient()
    holders = client.get_holders(symbol)

    if not holders.institutional_holders:
        print("No institutional holders data available")
        return

    print("\n--- Top Institutional Holders ---")
    print(f"| {'Holder':<40} | {'Shares':>12} | {'Value':>12} | {'% Out':>7} |")
    print("|" + "-" * 42 + "|" + "-" * 14 + "|" + "-" * 14 + "|" + "-" * 9 + "|")

    for h in holders.institutional_holders[:15]:  # Top 15
        holder = str(h.get('Holder', 'N/A'))[:40]
        shares = format_shares(h.get('Shares'))
        value = format_value(h.get('Value'))
        pct_out = h.get('% Out', h.get('pctHeld', 0))
        if pct_out and isinstance(pct_out, (int, float)):
            pct_str = f"{pct_out*100:.2f}%" if pct_out < 1 else f"{pct_out:.2f}%"
        else:
            pct_str = "N/A"

        print(f"| {holder:<40} | {shares:>12} | {value:>12} | {pct_str:>7} |")


def fetch_mutual_fund_holders(symbol: str = "GOOGL"):
    """Fetch top mutual fund holders."""
    print("\n" + "=" * 60)
    print(f"Mutual Fund Holders for {symbol}")
    print("=" * 60)

    client = YFinanceClient()
    holders = client.get_holders(symbol)

    if not holders.mutualfund_holders:
        print("No mutual fund holders data available")
        return

    print("\n--- Top Mutual Fund Holders ---")
    print(f"| {'Fund':<45} | {'Shares':>12} | {'Value':>12} |")
    print("|" + "-" * 47 + "|" + "-" * 14 + "|" + "-" * 14 + "|")

    for h in holders.mutualfund_holders[:15]:  # Top 15
        fund = str(h.get('Holder', 'N/A'))[:45]
        shares = format_shares(h.get('Shares'))
        value = format_value(h.get('Value'))

        print(f"| {fund:<45} | {shares:>12} | {value:>12} |")


def fetch_insider_roster(symbol: str = "NVDA"):
    """Fetch insider roster (executives and directors)."""
    print("\n" + "=" * 60)
    print(f"Insider Roster for {symbol}")
    print("=" * 60)

    client = YFinanceClient()
    holders = client.get_holders(symbol)

    if not holders.insider_roster_holders:
        print("No insider roster data available")
        return

    print("\n--- Insider Roster ---")
    print(f"| {'Name':<30} | {'Position':<25} | {'Shares':>12} | {'Latest Trans':>12} |")
    print("|" + "-" * 32 + "|" + "-" * 27 + "|" + "-" * 14 + "|" + "-" * 14 + "|")

    for h in holders.insider_roster_holders[:20]:
        name = str(h.get('Name', 'N/A'))[:30]
        position = str(h.get('Position', h.get('Relation', 'N/A')))[:25]
        shares = format_shares(h.get('Shares', h.get('Most Recent Transaction', 0)))

        # Try to get latest transaction date
        trans_date = h.get('Latest Transaction Date', h.get('positionDirectDate', 'N/A'))
        if trans_date and trans_date != 'N/A':
            trans_str = str(trans_date)[:12]
        else:
            trans_str = "N/A"

        print(f"| {name:<30} | {position:<25} | {shares:>12} | {trans_str:>12} |")


def analyze_holder_concentration(symbol: str = "AMZN"):
    """Analyze ownership concentration."""
    print("\n" + "=" * 60)
    print(f"Holder Concentration Analysis for {symbol}")
    print("=" * 60)

    client = YFinanceClient()
    holders = client.get_holders(symbol)

    # Major holders summary
    print("\n--- Ownership Summary ---")
    if holders.major_holders:
        for h in holders.major_holders:
            value = h.get('Value', h.get(0, 'N/A'))
            desc = h.get('Breakdown', h.get(1, 'N/A'))
            print(f"  {desc}: {value}")
    else:
        print("  No major holders data available")

    # Top institutional holders concentration
    print("\n--- Institutional Concentration ---")
    if holders.institutional_holders:
        total_inst_shares = 0
        for h in holders.institutional_holders:
            shares = h.get('Shares', 0)
            if shares and isinstance(shares, (int, float)):
                total_inst_shares += shares

        print(f"  Total Institutional Holders Listed: {len(holders.institutional_holders)}")
        print(f"  Combined Shares (Listed): {format_shares(total_inst_shares)}")

        # Top 5 concentration
        top5_shares = sum(
            h.get('Shares', 0) or 0
            for h in holders.institutional_holders[:5]
        )
        if total_inst_shares > 0:
            top5_pct = (top5_shares / total_inst_shares) * 100
            print(f"  Top 5 Holders Share of Listed: {top5_pct:.1f}%")
    else:
        print("  No institutional holders data available")

    # Mutual fund summary
    print("\n--- Mutual Fund Summary ---")
    if holders.mutualfund_holders:
        print(f"  Total Mutual Fund Holders Listed: {len(holders.mutualfund_holders)}")
        total_mf_value = sum(
            h.get('Value', 0) or 0
            for h in holders.mutualfund_holders
        )
        print(f"  Combined Value (Listed): {format_value(total_mf_value)}")
    else:
        print("  No mutual fund holders data available")


def compare_holder_structure():
    """Compare holder structure across companies."""
    print("\n" + "=" * 60)
    print("Holder Structure Comparison")
    print("=" * 60)

    symbols = ["AAPL", "MSFT", "GOOGL", "META", "NVDA"]
    client = YFinanceClient()

    print("\n| Symbol | Inst. Holders | MF Holders | Insiders |")
    print("|--------|---------------|------------|----------|")

    for symbol in symbols:
        try:
            holders = client.get_holders(symbol)

            inst_count = len(holders.institutional_holders) if holders.institutional_holders else 0
            mf_count = len(holders.mutualfund_holders) if holders.mutualfund_holders else 0
            insider_count = len(holders.insider_roster_holders) if holders.insider_roster_holders else 0

            print(f"| {symbol:<6} | {inst_count:>13} | {mf_count:>10} | {insider_count:>8} |")
        except Exception as e:
            print(f"| {symbol:<6} | Error: {str(e)[:30]} |")


def fetch_all_holder_data(symbol: str = "TSLA"):
    """Fetch all holder data for a company."""
    print("\n" + "=" * 60)
    print(f"Complete Holder Data for {symbol}")
    print("=" * 60)

    client = YFinanceClient()
    holders = client.get_holders(symbol)

    # Major holders
    print("\n--- Major Holders ---")
    if holders.major_holders:
        for h in holders.major_holders:
            value = h.get('Value', h.get(0, 'N/A'))
            desc = h.get('Breakdown', h.get(1, 'N/A'))
            print(f"  {desc}: {value}")
    else:
        print("  No data available")

    # Top 10 Institutional
    print("\n--- Top 10 Institutional Holders ---")
    if holders.institutional_holders:
        for i, h in enumerate(holders.institutional_holders[:10], 1):
            holder = str(h.get('Holder', 'N/A'))[:35]
            value = format_value(h.get('Value'))
            print(f"  {i:2}. {holder:<35} {value:>12}")
    else:
        print("  No data available")

    # Top 10 Mutual Funds
    print("\n--- Top 10 Mutual Fund Holders ---")
    if holders.mutualfund_holders:
        for i, h in enumerate(holders.mutualfund_holders[:10], 1):
            fund = str(h.get('Holder', 'N/A'))[:35]
            value = format_value(h.get('Value'))
            print(f"  {i:2}. {fund:<35} {value:>12}")
    else:
        print("  No data available")

    # Insider roster
    print("\n--- Insider Roster ---")
    if holders.insider_roster_holders:
        for h in holders.insider_roster_holders[:10]:
            name = str(h.get('Name', 'N/A'))[:25]
            position = str(h.get('Position', h.get('Relation', 'N/A')))[:20]
            print(f"  {name:<25} - {position}")
    else:
        print("  No data available")


def fetch_indian_company_holders(symbol: str = "RELIANCE.NS"):
    """Fetch holder data for Indian companies."""
    print("\n" + "=" * 60)
    print(f"Holder Data for {symbol.replace('.NS', '')} (NSE)")
    print("=" * 60)

    client = YFinanceClient()
    holders = client.get_holders(symbol)

    print("\n--- Major Holders ---")
    if holders.major_holders:
        for h in holders.major_holders:
            value = h.get('Value', h.get(0, 'N/A'))
            desc = h.get('Breakdown', h.get(1, 'N/A'))
            print(f"  {desc}: {value}")
    else:
        print("  No data available")

    print("\n--- Top Institutional Holders ---")
    if holders.institutional_holders:
        for h in holders.institutional_holders[:10]:
            holder = str(h.get('Holder', 'N/A'))[:40]
            shares = format_shares(h.get('Shares'))
            print(f"  {holder:<40} {shares:>12} shares")
    else:
        print("  No data available")


def analyze_vanguard_holdings():
    """Find Vanguard's holdings across major stocks."""
    print("\n" + "=" * 60)
    print("Vanguard Holdings Across Major Stocks")
    print("=" * 60)

    symbols = ["AAPL", "MSFT", "GOOGL", "AMZN", "META", "NVDA", "TSLA"]
    client = YFinanceClient()

    print("\n| Symbol | Vanguard Shares | Est. Value   |")
    print("|--------|-----------------|--------------|")

    for symbol in symbols:
        try:
            holders = client.get_holders(symbol)

            vanguard_shares = 0
            vanguard_value = 0

            if holders.institutional_holders:
                for h in holders.institutional_holders:
                    holder_name = str(h.get('Holder', '')).lower()
                    if 'vanguard' in holder_name:
                        shares = h.get('Shares', 0) or 0
                        value = h.get('Value', 0) or 0
                        vanguard_shares += shares
                        vanguard_value += value

            print(f"| {symbol:<6} | {format_shares(vanguard_shares):>15} | {format_value(vanguard_value):>12} |")
        except Exception as e:
            print(f"| {symbol:<6} | Error: {str(e)[:25]} |")


def analyze_blackrock_holdings():
    """Find BlackRock's holdings across major stocks."""
    print("\n" + "=" * 60)
    print("BlackRock Holdings Across Major Stocks")
    print("=" * 60)

    symbols = ["AAPL", "MSFT", "GOOGL", "AMZN", "META", "NVDA", "TSLA"]
    client = YFinanceClient()

    print("\n| Symbol | BlackRock Shares | Est. Value   |")
    print("|--------|------------------|--------------|")

    for symbol in symbols:
        try:
            holders = client.get_holders(symbol)

            blackrock_shares = 0
            blackrock_value = 0

            if holders.institutional_holders:
                for h in holders.institutional_holders:
                    holder_name = str(h.get('Holder', '')).lower()
                    if 'blackrock' in holder_name:
                        shares = h.get('Shares', 0) or 0
                        value = h.get('Value', 0) or 0
                        blackrock_shares += shares
                        blackrock_value += value

            print(f"| {symbol:<6} | {format_shares(blackrock_shares):>16} | {format_value(blackrock_value):>12} |")
        except Exception as e:
            print(f"| {symbol:<6} | Error: {str(e)[:25]} |")


if __name__ == "__main__":
    # Run all examples
    fetch_major_holders("AAPL")
    fetch_institutional_holders("MSFT")
    fetch_mutual_fund_holders("GOOGL")
    fetch_insider_roster("NVDA")
    analyze_holder_concentration("AMZN")
    compare_holder_structure()
    fetch_all_holder_data("TSLA")
    fetch_indian_company_holders("RELIANCE.NS")
    analyze_vanguard_holdings()
    analyze_blackrock_holdings()
