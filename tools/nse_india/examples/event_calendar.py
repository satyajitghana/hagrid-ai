"""Examples for using the Event Calendar API.

This script demonstrates how to:
- Fetch all corporate events for a symbol
- Filter events by date range
- Get upcoming events
- Analyze event types (results, dividends, etc.)
"""

from datetime import date, timedelta

from tools.nse_india.client import NSEIndiaClient


def fetch_all_events(symbol: str = "RELIANCE"):
    """Fetch complete event history for a symbol."""
    print("=" * 60)
    print(f"Event Calendar for {symbol}")
    print("=" * 60)

    client = NSEIndiaClient()

    events = client.get_event_calendar(symbol)
    print(f"Found {len(events)} total events\n")

    # Show recent events (last 10)
    recent = sorted(events, key=lambda e: e.event_date, reverse=True)[:10]

    print("Recent Events:")
    print("-" * 60)
    for event in recent:
        print(f"Date: {event.event_date.strftime('%d-%b-%Y')}")
        print(f"Purpose: {event.purpose}")
        print(f"Description: {event.description[:100]}...")
        print("-" * 40)

    client.close()


def fetch_events_by_date_range(symbol: str = "RELIANCE"):
    """Fetch events within a specific date range."""
    print("\n" + "=" * 60)
    print(f"Events by Date Range for {symbol}")
    print("=" * 60)

    client = NSEIndiaClient()

    # Get events from last year
    today = date.today()
    one_year_ago = today - timedelta(days=365)

    events = client.get_event_calendar_by_date_range(
        symbol=symbol,
        from_date=one_year_ago,
        to_date=today,
    )
    print(f"Found {len(events)} events in the last year\n")

    # Group by purpose
    by_purpose = {}
    for event in events:
        purpose = event.purpose
        by_purpose[purpose] = by_purpose.get(purpose, 0) + 1

    print("Events by Purpose:")
    for purpose, count in sorted(by_purpose.items(), key=lambda x: -x[1]):
        print(f"  {purpose}: {count}")

    client.close()


def fetch_upcoming_events(symbol: str = "RELIANCE"):
    """Fetch upcoming corporate events."""
    print("\n" + "=" * 60)
    print(f"Upcoming Events for {symbol}")
    print("=" * 60)

    client = NSEIndiaClient()

    # Get events for next 180 days
    upcoming = client.get_upcoming_events(symbol, days_ahead=180)
    print(f"Found {len(upcoming)} upcoming events\n")

    if upcoming:
        for event in upcoming:
            print(f"📅 {event.event_date.strftime('%d-%b-%Y')}: {event.purpose}")
            if event.is_financial_results:
                print("   📊 Financial Results")
            if event.is_dividend:
                print("   💰 Dividend Related")
            if event.is_bonus:
                print("   🎁 Bonus Issue")
            if event.is_fund_raising:
                print("   💵 Fund Raising")
            print()
    else:
        print("No upcoming events found")

    client.close()


def analyze_event_types(symbol: str = "TCS"):
    """Analyze different types of events for a symbol."""
    print("\n" + "=" * 60)
    print(f"Event Type Analysis for {symbol}")
    print("=" * 60)

    client = NSEIndiaClient()

    events = client.get_event_calendar(symbol)
    print(f"Total events: {len(events)}\n")

    # Count by type using properties
    results_count = sum(1 for e in events if e.is_financial_results)
    dividend_count = sum(1 for e in events if e.is_dividend)
    bonus_count = sum(1 for e in events if e.is_bonus)
    fund_raising_count = sum(1 for e in events if e.is_fund_raising)

    print("Event Type Breakdown:")
    print(f"  📊 Financial Results: {results_count}")
    print(f"  💰 Dividend Related: {dividend_count}")
    print(f"  🎁 Bonus Issues: {bonus_count}")
    print(f"  💵 Fund Raising: {fund_raising_count}")

    # Find all unique purposes
    purposes = set(e.purpose for e in events)
    print(f"\nUnique Event Types ({len(purposes)}):")
    for p in sorted(purposes):
        print(f"  - {p}")

    client.close()


def compare_event_frequency():
    """Compare event frequency across multiple stocks."""
    print("\n" + "=" * 60)
    print("Event Frequency Comparison")
    print("=" * 60)

    client = NSEIndiaClient()
    symbols = ["RELIANCE", "TCS", "INFY", "HDFCBANK", "ICICIBANK"]

    print("\n| Symbol | Total Events | Results | Dividends | Last Event |")
    print("|--------|--------------|---------|-----------|------------|")

    for symbol in symbols:
        try:
            events = client.get_event_calendar(symbol)
            results = sum(1 for e in events if e.is_financial_results)
            dividends = sum(1 for e in events if e.is_dividend)
            last_event = max(events, key=lambda e: e.event_date) if events else None
            last_date = last_event.event_date.strftime("%d-%b-%Y") if last_event else "N/A"

            print(f"| {symbol:6} | {len(events):12} | {results:7} | {dividends:9} | {last_date:10} |")
        except Exception as e:
            print(f"| {symbol:6} | Error: {str(e)[:30]} |")

    client.close()


if __name__ == "__main__":
    # Run all examples
    fetch_all_events("RELIANCE")
    fetch_events_by_date_range("RELIANCE")
    fetch_upcoming_events("RELIANCE")
    analyze_event_types("TCS")
    compare_event_frequency()
