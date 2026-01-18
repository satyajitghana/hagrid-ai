"""Example: Get market movers (top gainers/losers) from Groww API.

Run with: uv run python tools/groww/examples/market_movers.py
"""

from tools.groww import GrowwClient, GrowwToolkit


def example_client():
    """Get market movers using client directly."""
    print("=" * 60)
    print("Market Movers using GrowwClient")
    print("=" * 60)

    with GrowwClient() as client:
        # Get top gainers and losers
        data = client.get_market_movers(
            categories=["TOP_GAINERS", "TOP_LOSERS"],
            size=5
        )

        # Top Gainers
        print("\nTop Gainers:")
        print("-" * 40)
        for stock in data.get("top_gainers", []):
            symbol = stock.get("symbol", "N/A")
            name = stock.get("name", "N/A")
            ltp = stock.get("ltp", 0)
            change = stock.get("day_change_perc", 0)
            print(f"  {symbol}: Rs.{ltp:,.2f} (+{change:.2f}%)")

        # Top Losers
        print("\nTop Losers:")
        print("-" * 40)
        for stock in data.get("top_losers", []):
            symbol = stock.get("symbol", "N/A")
            name = stock.get("name", "N/A")
            ltp = stock.get("ltp", 0)
            change = stock.get("day_change_perc", 0)
            print(f"  {symbol}: Rs.{ltp:,.2f} ({change:.2f}%)")


def example_toolkit():
    """Using the toolkit (formatted output for agents)."""
    print("\n" + "=" * 60)
    print("Using GrowwToolkit (formatted output)")
    print("=" * 60)

    toolkit = GrowwToolkit()

    try:
        # Get formatted market movers
        result = toolkit.get_market_movers(category="all", size=5)
        print("\n" + result)

    finally:
        toolkit.close()


if __name__ == "__main__":
    example_client()
    example_toolkit()
