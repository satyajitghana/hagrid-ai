"""Example: Using GrowwToolkit with agents.

This example shows how to integrate GrowwToolkit with Agno agents.

Run with: uv run python tools/groww/examples/toolkit_usage.py
"""

from tools.groww import GrowwToolkit


def demo_all_tools():
    """Demonstrate all toolkit methods."""
    toolkit = GrowwToolkit()

    try:
        print("=" * 70)
        print("GrowwToolkit Demo - All Available Tools")
        print("=" * 70)

        # 1. Search for stocks
        print("\n1. SEARCH STOCKS")
        print("-" * 50)
        print(toolkit.search_stocks("infosys", size=3))

        # 2. Get live price
        print("\n2. LIVE STOCK PRICE")
        print("-" * 50)
        print(toolkit.get_stock_price("INFY"))

        # 3. Get company details
        print("\n3. COMPANY DETAILS")
        print("-" * 50)
        print(toolkit.get_stock_details("infosys-ltd"))

        # 4. Get options chain
        print("\n4. OPTIONS CHAIN (NIFTY)")
        print("-" * 50)
        print(toolkit.get_option_chain("NIFTY", strikes_around_atm=3))

        # 5. Market movers
        print("\n5. MARKET MOVERS")
        print("-" * 50)
        print(toolkit.get_market_movers(category="all", size=3))

        # 6. Global indices
        print("\n6. GLOBAL INDICES")
        print("-" * 50)
        print(toolkit.get_global_indices())

        # 7. Indian indices
        print("\n7. INDIAN INDICES")
        print("-" * 50)
        print(toolkit.get_indian_indices())

    finally:
        toolkit.close()


def agent_integration_example():
    """Example of how to use GrowwToolkit with Agno agents.

    This is a conceptual example - actual agent integration would look like this.
    """
    print("\n" + "=" * 70)
    print("Agent Integration Example (Conceptual)")
    print("=" * 70)

    print("""
# How to use GrowwToolkit with Agno agents:

from agno import Agent
from tools.groww import GrowwToolkit

# Create toolkit
groww_toolkit = GrowwToolkit()

# Create agent with the toolkit
agent = Agent(
    name="Market Analyst",
    model="gpt-4",
    instructions="You are a market analyst. Use the Groww toolkit to fetch market data.",
    tools=[groww_toolkit],
)

# Agent can now use:
# - search_stocks(query) - Search for stocks
# - get_stock_price(symbol) - Get live price
# - get_stock_details(search_id) - Get company info
# - get_option_chain(symbol) - Get options data
# - get_market_movers() - Get top gainers/losers
# - get_global_indices() - Get global market indices
# - get_indian_indices() - Get Indian market indices

# Example query:
response = agent.run("What is the current price of Reliance and show me its key fundamentals?")
""")


if __name__ == "__main__":
    demo_all_tools()
    agent_integration_example()
