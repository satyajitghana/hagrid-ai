"""Examples for market calendars from Yahoo Finance.

This script demonstrates how to:
- Fetch earnings calendar events
- Get IPO calendar information
- Track stock split events
- View economic events calendar
"""

from tools.yahoo_finance import YFinanceClient
from datetime import datetime, timedelta


def fetch_earnings_calendar():
    """Fetch upcoming earnings announcements."""
    print("=" * 60)
    print("Earnings Calendar")
    print("=" * 60)

    client = YFinanceClient()
    cal = client.get_calendars()

    print(f"\nDate Range: {cal.start_date} to {cal.end_date}")
    print(f"Total earnings events: {len(cal.earnings)}")

    if not cal.earnings:
        print("No earnings events found")
        return

    print("\n| Date | Symbol | Company | EPS Est |")
    print("|------|--------|---------|---------|")

    for event in cal.earnings[:20]:
        date = event.get('startdatetime', 'N/A')
        if date and date != 'N/A':
            try:
                dt = datetime.fromisoformat(date.replace('Z', '+00:00'))
                date_str = dt.strftime('%Y-%m-%d')
            except:
                date_str = str(date)[:10]
        else:
            date_str = 'N/A'

        symbol = event.get('ticker', 'N/A')
        company = event.get('companyshortname', 'N/A')
        if len(company) > 20:
            company = company[:17] + "..."
        eps_est = event.get('epsestimate', 'N/A')
        eps_str = f"${eps_est:.2f}" if isinstance(eps_est, (int, float)) else 'N/A'

        print(f"| {date_str} | {symbol:<6} | {company:<20} | {eps_str:>7} |")


def fetch_ipo_calendar():
    """Fetch upcoming IPO events."""
    print("\n" + "=" * 60)
    print("IPO Calendar")
    print("=" * 60)

    client = YFinanceClient()
    cal = client.get_calendars()

    print(f"\nTotal IPO events: {len(cal.ipo_info)}")

    if not cal.ipo_info:
        print("No IPO events found")
        return

    print("\n| Date | Company | Exchange | Price Range |")
    print("|------|---------|----------|-------------|")

    for event in cal.ipo_info[:15]:
        date = event.get('date', 'N/A')
        if date and date != 'N/A':
            try:
                dt = datetime.fromisoformat(str(date).replace('Z', '+00:00'))
                date_str = dt.strftime('%Y-%m-%d')
            except:
                date_str = str(date)[:10]
        else:
            date_str = 'N/A'

        company = event.get('company', event.get('companyName', 'N/A'))
        if len(company) > 25:
            company = company[:22] + "..."
        exchange = event.get('exchange', 'N/A')
        price_range = event.get('priceRange', 'N/A')

        print(f"| {date_str} | {company:<25} | {exchange:<8} | {price_range:>11} |")


def fetch_splits_calendar():
    """Fetch upcoming stock split events."""
    print("\n" + "=" * 60)
    print("Stock Splits Calendar")
    print("=" * 60)

    client = YFinanceClient()
    cal = client.get_calendars()

    print(f"\nTotal split events: {len(cal.splits)}")

    if not cal.splits:
        print("No split events found")
        return

    print("\n| Date | Symbol | Company | Ratio |")
    print("|------|--------|---------|-------|")

    for event in cal.splits[:15]:
        date = event.get('date', event.get('payableDate', 'N/A'))
        if date and date != 'N/A':
            try:
                dt = datetime.fromisoformat(str(date).replace('Z', '+00:00'))
                date_str = dt.strftime('%Y-%m-%d')
            except:
                date_str = str(date)[:10]
        else:
            date_str = 'N/A'

        symbol = event.get('symbol', event.get('ticker', 'N/A'))
        company = event.get('company', event.get('companyName', 'N/A'))
        if company and len(company) > 20:
            company = company[:17] + "..."

        # Split ratio
        from_factor = event.get('fromFactor', event.get('from', 1))
        to_factor = event.get('toFactor', event.get('to', 1))
        ratio = f"{to_factor}:{from_factor}"

        print(f"| {date_str} | {symbol:<6} | {company or 'N/A':<20} | {ratio:>5} |")


def fetch_economic_events():
    """Fetch upcoming economic events."""
    print("\n" + "=" * 60)
    print("Economic Events Calendar")
    print("=" * 60)

    client = YFinanceClient()
    cal = client.get_calendars()

    print(f"\nTotal economic events: {len(cal.economic_events)}")

    if not cal.economic_events:
        print("No economic events found")
        return

    print("\n| Date | Event | Country | Estimate | Prior |")
    print("|------|-------|---------|----------|-------|")

    for event in cal.economic_events[:20]:
        date = event.get('startdatetime', event.get('date', 'N/A'))
        if date and date != 'N/A':
            try:
                dt = datetime.fromisoformat(str(date).replace('Z', '+00:00'))
                date_str = dt.strftime('%Y-%m-%d')
            except:
                date_str = str(date)[:10]
        else:
            date_str = 'N/A'

        event_name = event.get('eventName', event.get('event', 'N/A'))
        if event_name and len(event_name) > 25:
            event_name = event_name[:22] + "..."

        country = event.get('country', 'N/A')
        estimate = event.get('estimate', event.get('consensus', 'N/A'))
        prior = event.get('prior', event.get('previous', 'N/A'))

        print(f"| {date_str} | {event_name:<25} | {country:<7} | {str(estimate)[:8]:>8} | {str(prior)[:5]:>5} |")


def fetch_calendars_custom_range():
    """Fetch calendars for a custom date range."""
    print("\n" + "=" * 60)
    print("Custom Date Range Calendar")
    print("=" * 60)

    client = YFinanceClient()

    # Get calendars for next 14 days
    start = datetime.now()
    end = start + timedelta(days=14)

    cal = client.get_calendars(
        start_date=start.strftime('%Y-%m-%d'),
        end_date=end.strftime('%Y-%m-%d')
    )

    print(f"\nDate Range: {start.strftime('%Y-%m-%d')} to {end.strftime('%Y-%m-%d')}")
    print(f"\nEvents Summary:")
    print(f"  Earnings: {len(cal.earnings)}")
    print(f"  IPOs: {len(cal.ipo_info)}")
    print(f"  Splits: {len(cal.splits)}")
    print(f"  Economic: {len(cal.economic_events)}")


def fetch_this_week_earnings():
    """Fetch this week's earnings announcements."""
    print("\n" + "=" * 60)
    print("This Week's Earnings")
    print("=" * 60)

    client = YFinanceClient()

    # Get calendars for this week
    today = datetime.now()
    # Start of week (Monday)
    start = today - timedelta(days=today.weekday())
    # End of week (Friday)
    end = start + timedelta(days=4)

    cal = client.get_calendars(
        start_date=start.strftime('%Y-%m-%d'),
        end_date=end.strftime('%Y-%m-%d')
    )

    print(f"\nWeek: {start.strftime('%Y-%m-%d')} to {end.strftime('%Y-%m-%d')}")
    print(f"Total earnings this week: {len(cal.earnings)}")

    if cal.earnings:
        # Group by day
        by_day = {}
        for event in cal.earnings:
            date = event.get('startdatetime', '')
            if date:
                try:
                    dt = datetime.fromisoformat(date.replace('Z', '+00:00'))
                    day = dt.strftime('%A')
                    if day not in by_day:
                        by_day[day] = []
                    by_day[day].append(event.get('ticker', 'N/A'))
                except:
                    pass

        for day, tickers in by_day.items():
            print(f"\n{day}: {', '.join(tickers[:10])}" + ("..." if len(tickers) > 10 else ""))


def summarize_calendar():
    """Provide a summary of all calendar events."""
    print("\n" + "=" * 60)
    print("Calendar Summary")
    print("=" * 60)

    client = YFinanceClient()
    cal = client.get_calendars()

    print(f"\n--- Period: {cal.start_date} to {cal.end_date} ---\n")

    print("| Category | Count |")
    print("|----------|-------|")
    print(f"| Earnings | {len(cal.earnings):>5} |")
    print(f"| IPOs     | {len(cal.ipo_info):>5} |")
    print(f"| Splits   | {len(cal.splits):>5} |")
    print(f"| Economic | {len(cal.economic_events):>5} |")
    print(f"| TOTAL    | {len(cal.earnings) + len(cal.ipo_info) + len(cal.splits) + len(cal.economic_events):>5} |")


if __name__ == "__main__":
    fetch_earnings_calendar()
    fetch_ipo_calendar()
    fetch_splits_calendar()
    fetch_economic_events()
    fetch_calendars_custom_range()
    fetch_this_week_earnings()
    summarize_calendar()
