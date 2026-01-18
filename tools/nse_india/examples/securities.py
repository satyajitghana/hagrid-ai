"""Examples for fetching listed securities data from NSE India.

This script demonstrates how to:
- Fetch all listed securities on NSE
- Search securities by name or ISIN
- Filter by trading series (EQ, BE, BZ, SM)
- Get recently listed securities
- Get securities statistics
"""

from tools.nse_india import NSEIndiaClient


def fetch_all_securities():
    """Fetch all listed securities from NSE."""
    print("=" * 60)
    print("All Listed Securities on NSE")
    print("=" * 60)

    client = NSEIndiaClient()

    response = client.get_listed_securities()

    print(f"\nTotal Securities Listed: {response.total_count}")
    print(f"Equity (EQ) Securities: {len(response.equity_securities)}")
    print(f"Trade-to-Trade Securities: {len(response.trade_to_trade_securities)}")
    print(f"SME Securities: {len(response.sme_securities)}")

    # Show series breakdown
    counts = response.get_series_counts()
    print("\n--- Breakdown by Series ---")
    for series, count in sorted(counts.items(), key=lambda x: x[1], reverse=True):
        print(f"  {series}: {count}")

    client.close()
    return response


def show_securities_count():
    """Show count of securities by series."""
    print("\n" + "=" * 60)
    print("Securities Count by Series")
    print("=" * 60)

    client = NSEIndiaClient()

    counts = client.get_securities_count()

    print(f"\nTotal Securities: {counts.get('total', 0)}")
    print("\n--- By Series ---")
    for series, count in sorted(counts.items(), key=lambda x: x[1] if isinstance(x[1], int) else 0, reverse=True):
        if series != "total":
            print(f"  {series}: {count}")

    client.close()


def get_security_details(symbol: str = "RELIANCE"):
    """Get details for a specific security."""
    print("\n" + "=" * 60)
    print(f"Security Details: {symbol}")
    print("=" * 60)

    client = NSEIndiaClient()

    security = client.get_security_by_symbol(symbol)

    if security:
        print(f"\nSymbol: {security.symbol}")
        print(f"Company Name: {security.company_name}")
        print(f"Series: {security.series}")
        print(f"ISIN: {security.isin}")
        print(f"Listing Date: {security.listing_date}")
        print(f"Face Value: Rs. {security.face_value}")
        print(f"Paid Up Value: Rs. {security.paid_up_value}")
        print(f"Market Lot: {security.market_lot}")
        if security.years_listed:
            print(f"Years Listed: {security.years_listed}")
        print(f"Is Equity: {security.is_equity}")
        print(f"Is Trade-to-Trade: {security.is_trade_to_trade}")
        print(f"Is SME: {security.is_sme}")
    else:
        print(f"Security {symbol} not found")

    client.close()


def search_securities_by_name(query: str = "Reliance"):
    """Search securities by company name."""
    print("\n" + "=" * 60)
    print(f"Search Results: '{query}'")
    print("=" * 60)

    client = NSEIndiaClient()

    results = client.search_securities(query)

    print(f"\nFound {len(results)} securities")
    print(f"\n{'Symbol':<15} {'Series':<6} {'Company Name':<40}")
    print("-" * 65)

    for sec in results[:20]:  # Show first 20 results
        print(f"{sec.symbol:<15} {sec.series:<6} {sec.company_name[:38]:<40}")

    if len(results) > 20:
        print(f"\n... and {len(results) - 20} more")

    client.close()


def get_by_isin(isin: str = "INE002A01018"):
    """Get security by ISIN."""
    print("\n" + "=" * 60)
    print(f"Security by ISIN: {isin}")
    print("=" * 60)

    client = NSEIndiaClient()

    security = client.get_security_by_isin(isin)

    if security:
        print(f"\nSymbol: {security.symbol}")
        print(f"Company Name: {security.company_name}")
        print(f"Series: {security.series}")
        print(f"ISIN: {security.isin}")
        print(f"Listing Date: {security.listing_date}")
    else:
        print(f"Security with ISIN {isin} not found")

    client.close()


def show_securities_by_series(series: str = "EQ"):
    """Show securities of a specific series."""
    print("\n" + "=" * 60)
    print(f"Securities in Series: {series}")
    print("=" * 60)

    client = NSEIndiaClient()

    securities = client.get_securities_by_series(series)

    print(f"\nTotal {series} Securities: {len(securities)}")
    print(f"\n{'Symbol':<15} {'Company Name':<45} {'Listing Date':<12}")
    print("-" * 75)

    for sec in securities[:30]:  # Show first 30
        listing_str = sec.listing_date.strftime("%d-%b-%Y") if sec.listing_date else "N/A"
        print(f"{sec.symbol:<15} {sec.company_name[:43]:<45} {listing_str:<12}")

    if len(securities) > 30:
        print(f"\n... and {len(securities) - 30} more")

    client.close()


def show_recently_listed(days: int = 90):
    """Show recently listed securities."""
    print("\n" + "=" * 60)
    print(f"Securities Listed in Last {days} Days")
    print("=" * 60)

    client = NSEIndiaClient()

    recent = client.get_recently_listed_securities(days)

    print(f"\nNewly Listed: {len(recent)} securities")

    if recent:
        # Sort by listing date (newest first)
        recent_sorted = sorted(recent, key=lambda s: s.listing_date or date.min, reverse=True)

        print(f"\n{'Symbol':<15} {'Series':<6} {'Listing Date':<12} {'Company Name':<35}")
        print("-" * 72)

        for sec in recent_sorted[:20]:
            listing_str = sec.listing_date.strftime("%d-%b-%Y") if sec.listing_date else "N/A"
            print(f"{sec.symbol:<15} {sec.series:<6} {listing_str:<12} {sec.company_name[:33]:<35}")

        if len(recent) > 20:
            print(f"\n... and {len(recent) - 20} more")
    else:
        print("No new listings in this period")

    client.close()


def get_all_symbols():
    """Get list of all trading symbols."""
    print("\n" + "=" * 60)
    print("All Trading Symbols on NSE")
    print("=" * 60)

    client = NSEIndiaClient()

    symbols = client.get_all_symbols()

    print(f"\nTotal Symbols: {len(symbols)}")
    print("\nFirst 50 symbols (alphabetical):")

    sorted_symbols = sorted(symbols)
    for i, symbol in enumerate(sorted_symbols[:50]):
        print(f"  {symbol}", end="")
        if (i + 1) % 5 == 0:
            print()

    print(f"\n\n... and {len(symbols) - 50} more")

    client.close()


def show_trade_to_trade_securities():
    """Show trade-to-trade (BE/BZ) securities."""
    print("\n" + "=" * 60)
    print("Trade-to-Trade Securities (BE/BZ Series)")
    print("=" * 60)

    client = NSEIndiaClient()

    response = client.get_listed_securities()
    t2t = response.trade_to_trade_securities

    print(f"\nTotal Trade-to-Trade Securities: {len(t2t)}")

    # Separate by series
    be_securities = [s for s in t2t if s.series == "BE"]
    bz_securities = [s for s in t2t if s.series == "BZ"]

    print(f"  BE (Book Entry): {len(be_securities)}")
    print(f"  BZ (Suspended): {len(bz_securities)}")

    if be_securities:
        print(f"\n--- BE Securities (First 10) ---")
        print(f"{'Symbol':<15} {'Company Name':<45}")
        print("-" * 62)
        for sec in be_securities[:10]:
            print(f"{sec.symbol:<15} {sec.company_name[:43]:<45}")

    if bz_securities:
        print(f"\n--- BZ Securities (First 10) ---")
        print(f"{'Symbol':<15} {'Company Name':<45}")
        print("-" * 62)
        for sec in bz_securities[:10]:
            print(f"{sec.symbol:<15} {sec.company_name[:43]:<45}")

    client.close()


def analyze_listing_trends():
    """Analyze listing trends by year."""
    print("\n" + "=" * 60)
    print("Listing Trends by Year")
    print("=" * 60)

    client = NSEIndiaClient()

    response = client.get_listed_securities()

    # Count by year
    year_counts: dict[int, int] = {}
    for sec in response.securities:
        if sec.listing_date:
            year = sec.listing_date.year
            year_counts[year] = year_counts.get(year, 0) + 1

    # Get last 10 years
    from datetime import date as dt
    current_year = dt.today().year
    recent_years = range(current_year - 9, current_year + 1)

    print(f"\n{'Year':<8} {'Listings':>10} {'Bar'}")
    print("-" * 50)

    max_count = max(year_counts.get(y, 0) for y in recent_years)
    scale = 30 / max_count if max_count > 0 else 1

    for year in recent_years:
        count = year_counts.get(year, 0)
        bar = "#" * int(count * scale)
        print(f"{year:<8} {count:>10} {bar}")

    # Total historical
    total_before = sum(c for y, c in year_counts.items() if y < current_year - 9)
    print(f"\nBefore {current_year - 9}: {total_before} securities")

    client.close()


if __name__ == "__main__":
    from datetime import date

    fetch_all_securities()
    show_securities_count()
    get_security_details("RELIANCE")
    search_securities_by_name("Tata")
    # get_by_isin("INE002A01018")  # Uncomment to test
    show_securities_by_series("EQ")
    show_recently_listed(90)
    # get_all_symbols()  # Uncomment to test
    show_trade_to_trade_securities()
    analyze_listing_trends()
