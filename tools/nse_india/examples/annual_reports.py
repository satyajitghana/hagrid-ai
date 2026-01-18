"""Examples for fetching annual reports from NSE India.

This script demonstrates how to:
- Fetch annual reports for a company
- Get report metadata (financial year, broadcast date)
- Download annual report PDFs/ZIPs
"""

from tools.nse_india import NSEIndiaClient


def fetch_annual_reports(symbol: str = "RELIANCE"):
    """Fetch annual reports for a company."""
    print("=" * 60)
    print(f"Annual Reports for {symbol}")
    print("=" * 60)

    client = NSEIndiaClient()

    reports = client.get_annual_reports(symbol=symbol)

    print(f"Found {len(reports)} annual reports\n")

    for report in reports:
        print(f"Company: {report.company_name}")
        print(f"Financial Year: {report.financial_year}")
        print(f"Broadcast Date: {report.broadcast_datetime}")
        print(f"File Type: {'ZIP' if report.is_zip else 'PDF'}")
        print(f"URL: {report.file_url}")
        print("-" * 40)

    client.close()
    return reports


def download_annual_report(symbol: str = "TCS"):
    """Download the most recent annual report."""
    print("\n" + "=" * 60)
    print(f"Downloading Latest Annual Report for {symbol}")
    print("=" * 60)

    client = NSEIndiaClient(attachments_dir="./example_attachments")

    reports = client.get_annual_reports(symbol=symbol)

    if reports:
        latest = reports[0]
        print(f"Downloading: {latest.financial_year}")
        print(f"File Type: {'ZIP' if latest.is_zip else 'PDF'}")

        path = client.download_annual_report(latest, symbol=symbol)
        print(f"Saved to: {path}")
    else:
        print("No annual reports found")

    client.close()


def compare_annual_reports():
    """Compare annual report availability across companies."""
    print("\n" + "=" * 60)
    print("Comparing Annual Reports Across Companies")
    print("=" * 60)

    symbols = ["RELIANCE", "TCS", "INFY", "HDFCBANK", "ICICIBANK"]

    client = NSEIndiaClient()

    for symbol in symbols:
        reports = client.get_annual_reports(symbol=symbol)
        years = [r.financial_year for r in reports]
        print(f"{symbol}: {len(reports)} reports - {', '.join(years[:3])}")

    client.close()


if __name__ == "__main__":
    fetch_annual_reports("RELIANCE")
    compare_annual_reports()
    # Uncomment to download:
    # download_annual_report("TCS")
