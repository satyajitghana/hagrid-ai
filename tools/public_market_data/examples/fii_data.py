"""FII/FPI data usage example for Public Market Data toolkit.

This example shows how to fetch FII/FPI investment data from CDSL.
"""

from tools.public_market_data import PublicMarketDataClient


def main():
    client = PublicMarketDataClient()

    try:
        # List available fortnightly dates
        print("=" * 60)
        print("Available FII Fortnightly Report Dates")
        print("=" * 60)

        dates = client.list_available_fortnightly_dates()
        print(f"Total available reports: {len(dates)}")
        print("\nMost recent 5:")
        for d in dates[:5]:
            print(f"  - {d}")

        # Get the most recent fortnightly report
        print("\n" + "=" * 60)
        print("FII Fortnightly Data (Latest)")
        print("=" * 60)

        data = client.get_fii_fortnightly_data()
        # Print first 2000 chars (it's markdown, can be long)
        print(data[:2000])
        print("\n... (truncated)")

        # Get monthly FII data
        print("\n" + "=" * 60)
        print("FII Monthly Data (Current Month)")
        print("=" * 60)

        data = client.get_fii_monthly_data()
        # Print first 2000 chars
        print(data[:2000])
        print("\n... (truncated)")

    finally:
        client.close()


if __name__ == "__main__":
    main()
