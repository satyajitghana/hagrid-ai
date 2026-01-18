"""Basic usage example for Public Market Data toolkit.

This example shows how to fetch global and Indian indices data.
"""

from tools.public_market_data import PublicMarketDataClient


def main():
    # Initialize the client
    client = PublicMarketDataClient()

    try:
        # Get global indices live prices
        print("=" * 60)
        print("Global Indices - Live Prices")
        print("=" * 60)

        indices = client.get_global_indices()
        for idx in indices:
            change = idx.get("day_change_perc", 0) or 0
            sign = "+" if change >= 0 else ""
            print(
                f"{idx['name']:15} ({idx['country']:12}): "
                f"{idx['value']:>12,.2f}  {sign}{change:.2f}%"
            )

        # Get Indian indices
        print("\n" + "=" * 60)
        print("Indian Indices - 52 Week Range")
        print("=" * 60)

        indices = client.get_indian_indices()
        for idx in indices[:10]:  # Top 10
            fno = "F&O" if idx.get("is_fno_enabled") else "   "
            year_low = idx.get("year_low")
            year_high = idx.get("year_high")
            low_str = f"{year_low:>12,.2f}" if year_low else "         N/A"
            high_str = f"{year_high:>12,.2f}" if year_high else "         N/A"
            print(
                f"{idx['display_name']:25} [{fno}]  "
                f"Low: {low_str}  High: {high_str}"
            )

    finally:
        client.close()


if __name__ == "__main__":
    main()
