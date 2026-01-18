"""Global indices example for Public Market Data toolkit.

This example shows how to fetch and analyze global indices data.
"""

from tools.public_market_data import PublicMarketDataClient


def main():
    client = PublicMarketDataClient()

    try:
        print("=" * 70)
        print("Global Indices - Live Market Data")
        print("=" * 70)

        indices = client.get_global_indices()

        # Group by continent
        by_continent = {}
        for idx in indices:
            continent = idx.get("continent", "OTHER")
            if continent not in by_continent:
                by_continent[continent] = []
            by_continent[continent].append(idx)

        # Display by region
        for continent in ["ASIA", "US", "EUROPE"]:
            if continent in by_continent:
                print(f"\n### {continent} ###")
                print("-" * 70)
                print(
                    f"{'Index':<20} {'Price':>12} {'Change':>10} "
                    f"{'Open':>12} {'High':>12} {'Low':>12}"
                )
                print("-" * 70)

                for idx in by_continent[continent]:
                    change = idx.get("day_change_perc", 0) or 0
                    sign = "+" if change >= 0 else ""

                    price = idx.get("value")
                    price_str = f"{price:,.2f}" if price else "N/A"
                    open_str = f"{idx.get('open'):,.2f}" if idx.get("open") else "N/A"
                    high_str = f"{idx.get('high'):,.2f}" if idx.get("high") else "N/A"
                    low_str = f"{idx.get('low'):,.2f}" if idx.get("low") else "N/A"

                    print(
                        f"{idx['name']:<20} {price_str:>12} {sign}{change:>9.2f}% "
                        f"{open_str:>12} {high_str:>12} {low_str:>12}"
                    )

        # Summary
        print("\n" + "=" * 70)
        print("Market Sentiment Summary")
        print("=" * 70)

        positive = sum(1 for idx in indices if (idx.get("day_change_perc") or 0) >= 0)
        negative = len(indices) - positive

        print(f"  Indices in green: {positive}")
        print(f"  Indices in red:   {negative}")

        # SGX Nifty indicator
        sgx = next((idx for idx in indices if "SGX" in idx.get("symbol", "")), None)
        if sgx:
            change = sgx.get("day_change_perc", 0) or 0
            direction = "higher" if change >= 0 else "lower"
            print(f"\n  SGX Nifty indicates Indian markets may open {direction} ({change:+.2f}%)")

    finally:
        client.close()


if __name__ == "__main__":
    main()
