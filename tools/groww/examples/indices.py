"""Example: Get global and Indian indices data from Groww API.

Run with: uv run python tools/groww/examples/indices.py
"""

from tools.groww import GrowwClient, GrowwToolkit


def example_global_indices():
    """Get global indices using client directly."""
    print("=" * 60)
    print("Global Indices using GrowwClient")
    print("=" * 60)

    with GrowwClient() as client:
        data = client.get_global_indices()

        for item in data:
            name = item.get("name", "N/A")
            value = item.get("value", 0)
            change = item.get("day_change", 0)
            change_perc = item.get("day_change_perc", 0)
            continent = item.get("continent", "N/A")

            change_sign = "+" if change >= 0 else ""
            print(f"\n{name} ({continent}):")
            print(f"  Value: {value:,.2f} ({change_sign}{change_perc:.2f}%)")


def example_indian_indices():
    """Get Indian indices using client directly."""
    print("\n" + "=" * 60)
    print("Indian Indices using GrowwClient")
    print("=" * 60)

    with GrowwClient() as client:
        data = client.get_indian_indices()

        # Show only F&O enabled indices
        fno_indices = [i for i in data if i.get("is_fno_enabled")]

        print("\nF&O Enabled Indices:")
        print("-" * 40)
        for item in fno_indices:
            name = item.get("display_name", "N/A")
            year_low = item.get("year_low", 0)
            year_high = item.get("year_high", 0)
            print(f"  {name}")
            print(f"    52W Range: {year_low:,.0f} - {year_high:,.0f}")


def example_toolkit():
    """Using the toolkit (formatted output for agents)."""
    print("\n" + "=" * 60)
    print("Using GrowwToolkit (formatted output)")
    print("=" * 60)

    toolkit = GrowwToolkit()

    try:
        # Get formatted global indices
        print("\nGlobal Indices:")
        result = toolkit.get_global_indices()
        print(result)

        # Get formatted Indian indices
        print("\n\nIndian Indices:")
        result = toolkit.get_indian_indices()
        print(result)

    finally:
        toolkit.close()


if __name__ == "__main__":
    example_global_indices()
    example_indian_indices()
    example_toolkit()
