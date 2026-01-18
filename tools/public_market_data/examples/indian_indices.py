"""Indian indices example for Public Market Data toolkit.

This example shows how to fetch and analyze Indian market indices.
"""

from tools.public_market_data import PublicMarketDataClient


def main():
    client = PublicMarketDataClient()

    try:
        print("=" * 80)
        print("Indian Market Indices")
        print("=" * 80)

        indices = client.get_indian_indices()

        # Separate F&O and non-F&O indices
        fno_indices = [idx for idx in indices if idx.get("is_fno_enabled")]
        non_fno_indices = [idx for idx in indices if not idx.get("is_fno_enabled")]

        # F&O enabled indices
        print("\n### F&O Enabled Indices ###")
        print("-" * 80)
        print(
            f"{'Index':<30} {'Symbol':<20} {'52W Low':>12} {'52W High':>12}"
        )
        print("-" * 80)

        for idx in fno_indices:
            year_low = idx.get("year_low")
            year_high = idx.get("year_high")
            low_str = f"{year_low:,.2f}" if year_low else "N/A"
            high_str = f"{year_high:,.2f}" if year_high else "N/A"

            print(
                f"{idx['display_name']:<30} {idx['symbol']:<20} "
                f"{low_str:>12} {high_str:>12}"
            )

        # Sectoral indices
        print("\n### Sectoral Indices ###")
        print("-" * 80)

        sectoral = [
            idx for idx in non_fno_indices
            if any(
                kw in idx.get("display_name", "").upper()
                for kw in ["IT", "PHARMA", "AUTO", "FMCG", "METAL", "PSU", "COMMODITIES"]
            )
        ]

        for idx in sectoral:
            year_low = idx.get("year_low")
            year_high = idx.get("year_high")
            low_str = f"{year_low:,.2f}" if year_low else "N/A"
            high_str = f"{year_high:,.2f}" if year_high else "N/A"

            print(
                f"{idx['display_name']:<30} {idx['symbol']:<20} "
                f"{low_str:>12} {high_str:>12}"
            )

        # Cap-based indices
        print("\n### Cap-based Indices ###")
        print("-" * 80)

        cap_indices = [
            idx for idx in non_fno_indices
            if any(
                kw in idx.get("display_name", "").upper()
                for kw in ["MIDCAP", "SMALLCAP", "100", "500"]
            )
        ]

        for idx in cap_indices:
            year_low = idx.get("year_low")
            year_high = idx.get("year_high")
            low_str = f"{year_low:,.2f}" if year_low else "N/A"
            high_str = f"{year_high:,.2f}" if year_high else "N/A"

            print(
                f"{idx['display_name']:<30} {idx['symbol']:<20} "
                f"{low_str:>12} {high_str:>12}"
            )

        # Summary
        print("\n" + "=" * 80)
        print("Summary")
        print("=" * 80)
        print(f"  Total indices tracked:   {len(indices)}")
        print(f"  F&O enabled indices:     {len(fno_indices)}")
        print(f"  Non-F&O indices:         {len(non_fno_indices)}")

    finally:
        client.close()


if __name__ == "__main__":
    main()
