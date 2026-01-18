"""Example: Search for stocks using Groww API.

Run with: uv run python tools/groww/examples/search.py
"""

from tools.groww import GrowwClient, GrowwToolkit


def example_client():
    """Using the client directly."""
    print("=" * 60)
    print("Using GrowwClient directly")
    print("=" * 60)

    with GrowwClient() as client:
        # Search for stocks
        results = client.search("reliance", size=5)

        print("\nSearch results for 'reliance':")
        for r in results:
            print(f"  - {r['title']}")
            print(f"    search_id: {r['search_id']}")
            print(f"    NSE: {r['nse_scrip_code'] or 'N/A'}")
            print(f"    Type: {r['entity_type']}")
            print()


def example_toolkit():
    """Using the toolkit (formatted output for agents)."""
    print("=" * 60)
    print("Using GrowwToolkit (formatted output)")
    print("=" * 60)

    toolkit = GrowwToolkit()

    try:
        # Search for stocks - returns markdown formatted string
        result = toolkit.search_stocks("tcs", size=5)
        print("\n" + result)

    finally:
        toolkit.close()


if __name__ == "__main__":
    example_client()
    print("\n")
    example_toolkit()
