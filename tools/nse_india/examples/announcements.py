"""Examples for fetching corporate announcements from NSE India.

This script demonstrates how to:
- Fetch equity announcements
- Fetch debt announcements
- Filter by symbol and date range
- Track new announcements
- Download attachments
"""

from datetime import date, timedelta

from tools.nse_india import AnnouncementIndex, NSEIndiaClient


def fetch_equity_announcements():
    """Fetch recent equity corporate announcements."""
    print("=" * 60)
    print("Fetching Equity Announcements")
    print("=" * 60)

    client = NSEIndiaClient()

    # Get all recent equity announcements
    announcements = client.get_announcements(AnnouncementIndex.EQUITIES)

    print(f"Found {len(announcements)} announcements\n")

    # Show first 5 announcements
    for ann in announcements[:5]:
        print(f"Symbol: {ann.symbol}")
        print(f"Company: {ann.company_name}")
        print(f"Subject: {ann.subject}")
        print(f"Date: {ann.broadcast_datetime}")
        print(f"Has Attachment: {ann.has_attachment}")
        print("-" * 40)

    client.close()


def fetch_debt_announcements():
    """Fetch recent debt corporate announcements."""
    print("\n" + "=" * 60)
    print("Fetching Debt Announcements")
    print("=" * 60)

    client = NSEIndiaClient()

    # Debt announcements don't have a symbol column
    announcements = client.get_announcements(AnnouncementIndex.DEBT)

    print(f"Found {len(announcements)} debt announcements\n")

    for ann in announcements[:3]:
        print(f"Company: {ann.company_name}")
        print(f"Subject: {ann.subject}")
        print(f"Date: {ann.broadcast_datetime}")
        print("-" * 40)

    client.close()


def fetch_symbol_announcements(symbol: str = "RELIANCE"):
    """Fetch announcements for a specific symbol."""
    print("\n" + "=" * 60)
    print(f"Fetching Announcements for {symbol}")
    print("=" * 60)

    client = NSEIndiaClient()

    # Get announcements for a specific symbol
    announcements = client.get_announcements(
        index=AnnouncementIndex.EQUITIES,
        symbol=symbol,
    )

    print(f"Found {len(announcements)} announcements for {symbol}\n")

    for ann in announcements[:5]:
        print(f"Subject: {ann.subject}")
        print(f"Date: {ann.broadcast_datetime}")
        print(f"Details: {ann.details[:100]}...")
        print("-" * 40)

    client.close()


def fetch_announcements_by_date_range():
    """Fetch announcements within a date range."""
    print("\n" + "=" * 60)
    print("Fetching Announcements by Date Range")
    print("=" * 60)

    client = NSEIndiaClient()

    # Get announcements from the last 7 days
    today = date.today()
    week_ago = today - timedelta(days=7)

    announcements = client.get_announcements(
        index=AnnouncementIndex.EQUITIES,
        from_date=week_ago,
        to_date=today,
    )

    print(f"Found {len(announcements)} announcements from {week_ago} to {today}\n")

    # Group by subject type
    subjects = {}
    for ann in announcements:
        subject = ann.subject
        subjects[subject] = subjects.get(subject, 0) + 1

    print("Announcements by subject:")
    for subject, count in sorted(subjects.items(), key=lambda x: -x[1])[:10]:
        print(f"  {subject}: {count}")

    client.close()


def track_new_announcements():
    """Track and process only new (unprocessed) announcements."""
    print("\n" + "=" * 60)
    print("Tracking New Announcements")
    print("=" * 60)

    # Using a custom database path for this example
    client = NSEIndiaClient(db_path="example_announcements.db")

    # First run: get new announcements
    new_announcements = client.get_new_announcements(AnnouncementIndex.EQUITIES)
    print(f"First run: {len(new_announcements)} new announcements")

    # Process and mark them as processed (without downloading attachments)
    processed = client.process_announcements(
        index=AnnouncementIndex.EQUITIES,
        download_attachments=False,
    )
    print(f"Processed {len(processed)} announcements")

    # Second run: should return fewer or no new announcements
    new_announcements_2 = client.get_new_announcements(AnnouncementIndex.EQUITIES)
    print(f"Second run: {len(new_announcements_2)} new announcements")

    # Check if a specific announcement was processed
    if processed:
        first_processed = processed[0]
        is_done = client.tracker.is_processed(first_processed.unique_id)
        print(f"\nAnnouncement '{first_processed.subject[:50]}...' is processed: {is_done}")

    client.close()


def download_announcement_attachments(symbol: str = "TCS"):
    """Download PDF attachments from announcements."""
    print("\n" + "=" * 60)
    print(f"Downloading Attachments for {symbol}")
    print("=" * 60)

    client = NSEIndiaClient(attachments_dir="./example_attachments")

    # Get announcements with attachments
    announcements = client.get_announcements(
        index=AnnouncementIndex.EQUITIES,
        symbol=symbol,
    )

    # Filter those with attachments
    with_attachments = [a for a in announcements if a.has_attachment]
    print(f"Found {len(with_attachments)} announcements with attachments\n")

    # Download first attachment
    if with_attachments:
        ann = with_attachments[0]
        print(f"Downloading: {ann.subject}")
        print(f"URL: {ann.attachment_url}")

        path = client.download_attachment(ann, subdir=symbol)
        if path:
            print(f"Saved to: {path}")
    else:
        print("No attachments to download")

    client.close()


if __name__ == "__main__":
    # Run all examples
    fetch_equity_announcements()
    fetch_debt_announcements()
    fetch_symbol_announcements("IREDA")
    fetch_announcements_by_date_range()
    track_new_announcements()
    # Uncomment to download attachments:
    # download_announcement_attachments("RELIANCE")
