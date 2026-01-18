"""Examples for fetching shareholding patterns from NSE India.

This script demonstrates how to:
- Fetch shareholding pattern history (quarterly data)
- Get detailed shareholding with shareholder names
- Analyze promoter vs public holding trends
- Find significant beneficial owners
"""

from tools.nse_india import NSEIndiaClient


def fetch_shareholding_history(symbol: str = "RELIANCE"):
    """Fetch historical shareholding pattern data."""
    print("=" * 60)
    print(f"Shareholding History for {symbol}")
    print("=" * 60)

    client = NSEIndiaClient()

    patterns = client.get_shareholding_patterns_history(symbol=symbol)

    print(f"Found {len(patterns)} quarterly patterns\n")

    # Show recent quarters
    print(f"{'Quarter':<12} {'Date':<15} {'Promoter %':>12} {'Public %':>12}")
    print("-" * 55)

    for pattern in patterns[:8]:
        quarter = pattern.quarter or "-"
        date_str = pattern.pattern_date.strftime("%d-%b-%Y") if pattern.pattern_date else "-"
        promoter = f"{pattern.promoter_percentage:.2f}%" if pattern.promoter_percentage else "-"
        public = f"{pattern.public_percentage:.2f}%" if pattern.public_percentage else "-"
        print(f"{quarter:<12} {date_str:<15} {promoter:>12} {public:>12}")

    client.close()
    return patterns


def analyze_shareholding_trend(symbol: str = "RELIANCE"):
    """Analyze promoter holding trend over time."""
    print("\n" + "=" * 60)
    print(f"Shareholding Trend Analysis for {symbol}")
    print("=" * 60)

    client = NSEIndiaClient()

    patterns = client.get_shareholding_patterns_history(symbol=symbol)

    # Filter valid patterns (non-zero promoter %)
    valid = [p for p in patterns if p.promoter_percentage and p.promoter_percentage > 0]

    if len(valid) < 2:
        print("Not enough data for trend analysis")
        client.close()
        return

    latest = valid[0]
    oldest = valid[-1]

    # Calculate changes
    promoter_change = latest.promoter_percentage - oldest.promoter_percentage
    public_change = (latest.public_percentage or 0) - (oldest.public_percentage or 0)

    print(f"\nAnalysis Period: {oldest.pattern_date.strftime('%b %Y')} to {latest.pattern_date.strftime('%b %Y')}")
    print(f"Number of quarters: {len(valid)}")
    print()

    # Promoter trend
    direction = "↑ increased" if promoter_change > 0 else "↓ decreased" if promoter_change < 0 else "→ unchanged"
    print(f"Promoter Holding: {oldest.promoter_percentage:.2f}% → {latest.promoter_percentage:.2f}%")
    print(f"  Change: {direction} by {abs(promoter_change):.2f}%")

    # Public trend
    direction = "↑ increased" if public_change > 0 else "↓ decreased" if public_change < 0 else "→ unchanged"
    print(f"\nPublic Holding: {oldest.public_percentage:.2f}% → {latest.public_percentage:.2f}%")
    print(f"  Change: {direction} by {abs(public_change):.2f}%")

    # Quarter-over-quarter changes
    print("\nQuarter-over-Quarter Promoter Changes:")
    for i in range(min(4, len(valid) - 1)):
        current = valid[i]
        previous = valid[i + 1]
        change = current.promoter_percentage - previous.promoter_percentage
        symbol_char = "+" if change >= 0 else ""
        print(f"  {current.quarter}: {symbol_char}{change:.2f}%")

    client.close()


def fetch_detailed_shareholding(symbol: str = "RELIANCE"):
    """Fetch detailed shareholding with individual shareholder names."""
    print("\n" + "=" * 60)
    print(f"Detailed Shareholding for {symbol}")
    print("=" * 60)

    client = NSEIndiaClient()

    # Get the latest detailed shareholding
    details = client.get_latest_shareholding_details(symbol=symbol)

    if not details:
        print("No detailed shareholding data found")
        client.close()
        return

    print(f"\nCompany: {details.company_name}")
    print(f"Period Ended: {details.period_ended.strftime('%d-%b-%Y') if details.period_ended else 'N/A'}")

    # Summary
    print("\n--- Summary by Category ---")
    for s in details.summary:
        if s.total_shares > 0 or "total" in s.category_name.lower():
            print(f"  {s.category_name}: {s.shareholding_percentage:.2f}% ({s.total_shares:,} shares)")

    # Top promoters
    print("\n--- Top 10 Promoter Shareholders ---")
    top_promoters = details.top_promoters
    count = 0
    for p in top_promoters:
        if "total" in p.name.lower() or "sub-total" in p.name.lower():
            continue
        count += 1
        if count > 10:
            break
        entity_type = f"({p.entity_type})" if p.entity_type else ""
        print(f"  {count}. {p.name} {entity_type}")
        print(f"     Holdings: {p.total_shares:,} shares ({p.shareholding_percentage:.2f}%)")

    # Beneficial owners
    print("\n--- Significant Beneficial Owners ---")
    top_bos = details.top_beneficial_owners
    seen = set()
    count = 0
    for bo in top_bos:
        if bo.sbo_name in seen:
            continue
        seen.add(bo.sbo_name)
        count += 1
        if count > 5:
            break
        print(f"  {count}. {bo.sbo_name}")
        print(f"     Through: {bo.registered_owner_name}")
        print(f"     Holding: {bo.shareholding_percentage:.2f}% | Voting: {bo.voting_rights_percentage:.2f}%")

    # Institutional holders
    print("\n--- Major Institutional Holders ---")
    institutions = [i for i in details.public_institutions if i.total_shares > 0 and "total" not in i.name.lower()]
    for inst in sorted(institutions, key=lambda x: x.shareholding_percentage, reverse=True)[:5]:
        print(f"  {inst.name}: {inst.shareholding_percentage:.2f}%")

    client.close()


def get_shareholding_for_specific_quarter(symbol: str = "RELIANCE", quarter_index: int = 0):
    """Get detailed shareholding for a specific quarter."""
    print("\n" + "=" * 60)
    print(f"Detailed Shareholding for Specific Quarter - {symbol}")
    print("=" * 60)

    client = NSEIndiaClient()

    # First get the history to find available quarters
    patterns = client.get_shareholding_patterns_history(symbol=symbol)

    if quarter_index >= len(patterns):
        print(f"Only {len(patterns)} quarters available")
        client.close()
        return

    selected = patterns[quarter_index]
    print(f"\nSelected Quarter: {selected.quarter} ({selected.pattern_date.strftime('%d-%b-%Y') if selected.pattern_date else 'N/A'})")
    print(f"Record ID: {selected.record_id}")

    # Fetch detailed data using the record_id
    details = client.get_shareholding_details(
        nds_id=selected.record_id,
        symbol=selected.symbol,
        company_name=selected.company_name,
        period_ended=selected.pattern_date.strftime("%d-%b-%Y") if selected.pattern_date else None,
    )

    print(f"\nPromoter Total: {details.promoter_total_percentage:.2f}%")
    print(f"Public Total: {details.public_total_percentage:.2f}%")

    client.close()


def compare_shareholding_across_companies():
    """Compare shareholding patterns across multiple companies."""
    print("\n" + "=" * 60)
    print("Comparing Shareholding Across Companies")
    print("=" * 60)

    symbols = ["RELIANCE", "TCS", "INFY", "HDFCBANK", "WIPRO"]

    client = NSEIndiaClient()

    print(f"\n{'Company':<15} {'Promoter %':>12} {'Public %':>12} {'Quarter':<12}")
    print("-" * 55)

    for symbol in symbols:
        patterns = client.get_shareholding_patterns_history(symbol=symbol)
        if patterns:
            latest = patterns[0]
            promoter = f"{latest.promoter_percentage:.2f}%" if latest.promoter_percentage else "-"
            public = f"{latest.public_percentage:.2f}%" if latest.public_percentage else "-"
            quarter = latest.quarter or "-"
            print(f"{symbol:<15} {promoter:>12} {public:>12} {quarter:<12}")

    client.close()


if __name__ == "__main__":
    # Run all examples
    fetch_shareholding_history("RELIANCE")
    analyze_shareholding_trend("RELIANCE")
    fetch_detailed_shareholding("RELIANCE")
    get_shareholding_for_specific_quarter("RELIANCE", quarter_index=1)
    compare_shareholding_across_companies()
