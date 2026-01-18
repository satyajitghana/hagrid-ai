"""Example: Get live stock prices from Groww API.

Run with: uv run python tools/groww/examples/stock_price.py
"""

from tools.groww import GrowwClient, GrowwToolkit


def example_client():
    """Get live price using client directly."""
    print("=" * 60)
    print("Live Stock Prices using GrowwClient")
    print("=" * 60)

    with GrowwClient() as client:
        # Get live price for multiple stocks
        symbols = ["RELIANCE", "TCS", "INFY", "HDFCBANK"]

        for symbol in symbols:
            try:
                data = client.get_live_price(symbol, exchange="NSE")

                ltp = data.get("ltp", 0)
                change = data.get("day_change", 0)
                change_perc = data.get("day_change_perc", 0)
                volume = data.get("volume", 0)

                change_sign = "+" if change >= 0 else ""
                print(f"\n{symbol}:")
                print(f"  LTP: Rs.{ltp:,.2f} ({change_sign}{change_perc:.2f}%)")
                print(f"  Open: Rs.{data.get('open', 0):,.2f}")
                print(f"  High: Rs.{data.get('high', 0):,.2f}")
                print(f"  Low: Rs.{data.get('low', 0):,.2f}")
                print(f"  Volume: {volume:,}")
                print(f"  52W Range: Rs.{data.get('year_low', 0):,.2f} - Rs.{data.get('year_high', 0):,.2f}")

            except Exception as e:
                print(f"\n{symbol}: Error - {e}")


def example_toolkit():
    """Using the toolkit (formatted output for agents)."""
    print("\n" + "=" * 60)
    print("Using GrowwToolkit (formatted output)")
    print("=" * 60)

    toolkit = GrowwToolkit()

    try:
        # Get formatted price data
        result = toolkit.get_stock_price("RELIANCE")
        print("\n" + result)

    finally:
        toolkit.close()


if __name__ == "__main__":
    example_client()
    example_toolkit()
