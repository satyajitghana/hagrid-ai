"""Example: Get options chain data from Groww API.

Run with: uv run python tools/groww/examples/option_chain.py
"""

from tools.groww import GrowwClient, GrowwToolkit


def example_client_index():
    """Get options chain for an index using client."""
    print("=" * 60)
    print("Options Chain for BANKNIFTY (Index)")
    print("=" * 60)

    with GrowwClient() as client:
        # Get options chain for BANKNIFTY
        data = client.get_option_chain("BANKNIFTY")

        print(f"\nSpot Price: {data['spot_price']:,.2f}")
        print(f"Expiry: {data['expiry_date']}")
        print(f"Available Expiries: {', '.join(data['available_expiries'][:3])}")

        print("\nOption Chain (first 5 strikes):")
        for strike_data in data["option_chain"][:5]:
            strike = strike_data["strike_price"]
            ce = strike_data.get("ce") or {}
            pe = strike_data.get("pe") or {}

            ce_ltp = ce.get("ltp", 0)
            pe_ltp = pe.get("ltp", 0)
            ce_oi = ce.get("oi", 0)
            pe_oi = pe.get("oi", 0)

            print(f"  Strike {strike:,.0f}: CE={ce_ltp:,.2f} (OI:{ce_oi:,}) | PE={pe_ltp:,.2f} (OI:{pe_oi:,})")


def example_client_stock():
    """Get options chain for a stock using client."""
    print("\n" + "=" * 60)
    print("Options Chain for RELIANCE (Stock)")
    print("=" * 60)

    with GrowwClient() as client:
        # Get options chain for RELIANCE
        # For stocks, use the search_id (URL slug)
        data = client.get_option_chain("reliance-industries-ltd")

        print(f"\nSpot Price: {data['spot_price']:,.2f}")
        print(f"Expiry: {data['expiry_date']}")

        print("\nOption Chain (first 5 strikes):")
        for strike_data in data["option_chain"][:5]:
            strike = strike_data["strike_price"]
            ce = strike_data.get("ce") or {}
            pe = strike_data.get("pe") or {}

            print(f"  Strike {strike:,.0f}")
            if ce:
                print(f"    CE: LTP={ce.get('ltp', 0):,.2f}, IV={ce.get('iv', 'N/A')}, Delta={ce.get('delta', 'N/A')}")
            if pe:
                print(f"    PE: LTP={pe.get('ltp', 0):,.2f}, IV={pe.get('iv', 'N/A')}, Delta={pe.get('delta', 'N/A')}")


def example_toolkit():
    """Using the toolkit (formatted output for agents)."""
    print("\n" + "=" * 60)
    print("Using GrowwToolkit (formatted markdown output)")
    print("=" * 60)

    toolkit = GrowwToolkit()

    try:
        # Get NIFTY options chain - returns formatted markdown
        result = toolkit.get_option_chain("NIFTY", strikes_around_atm=5)
        print("\n" + result)

    finally:
        toolkit.close()


if __name__ == "__main__":
    example_client_index()
    example_client_stock()
    example_toolkit()
