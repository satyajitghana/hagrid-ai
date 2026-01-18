"""Example: Get company details and fundamentals from Groww API.

Run with: uv run python tools/groww/examples/stock_details.py
"""

from tools.groww import GrowwClient, GrowwToolkit


def example_client():
    """Get company details using client directly."""
    print("=" * 60)
    print("Company Details using GrowwClient")
    print("=" * 60)

    with GrowwClient() as client:
        # Get company details for Reliance
        # Use the search_id (URL slug)
        data = client.get_company_details("reliance-industries-ltd")

        basic = data.get("basic", {})
        stats = data.get("stats", {})
        live = data.get("live_data", {})
        holding = data.get("shareholding", {})
        financials = data.get("financials_summary", {})

        print(f"\n{basic.get('name', 'N/A')}")
        print("-" * 40)
        print(f"NSE Symbol: {basic.get('nse_symbol', 'N/A')}")
        print(f"Sector: {basic.get('sector', 'N/A')}")
        print(f"Industry: {basic.get('industry', 'N/A')}")
        print(f"CEO: {basic.get('ceo', 'N/A')}")
        print(f"Website: {basic.get('website', 'N/A')}")

        print("\nKey Metrics:")
        print(f"  Market Cap: {stats.get('market_cap', 'N/A')}")
        print(f"  P/E Ratio: {stats.get('pe_ratio', 'N/A')}")
        print(f"  P/B Ratio: {stats.get('pb_ratio', 'N/A')}")
        print(f"  ROE: {stats.get('roe', 'N/A')}")
        print(f"  EPS: {stats.get('eps', 'N/A')}")
        print(f"  Dividend Yield: {stats.get('dividend_yield', 'N/A')}")

        print("\nLive Price:")
        print(f"  LTP: Rs.{live.get('ltp', 0):,.2f}")
        change = live.get("day_change", 0)
        change_sign = "+" if change >= 0 else ""
        print(f"  Change: {change_sign}{change:,.2f} ({change_sign}{live.get('day_change_perc', 0):.2f}%)")

        if holding:
            print("\nShareholding:")
            for key, value in holding.items():
                if value:
                    print(f"  {key.replace('_', ' ').title()}: {value:.2f}%")


def example_toolkit():
    """Using the toolkit (formatted output for agents)."""
    print("\n" + "=" * 60)
    print("Using GrowwToolkit (formatted output)")
    print("=" * 60)

    toolkit = GrowwToolkit()

    try:
        # Get formatted company details
        result = toolkit.get_stock_details("tata-consultancy-services-ltd")
        print("\n" + result)

    finally:
        toolkit.close()


if __name__ == "__main__":
    example_client()
    example_toolkit()
