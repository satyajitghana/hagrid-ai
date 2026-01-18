"""Examples for using the Public Market Data Toolkit with AI agents.

This script demonstrates how to:
- Initialize the toolkit
- Use toolkit methods (returns formatted strings for LLMs)
- Integrate with an Agno agent
"""

from tools.public_market_data import PublicMarketDataToolkit


def global_indices_usage():
    """Fetch global indices live prices."""
    print("=" * 60)
    print("Public Market Data Toolkit - Global Indices")
    print("=" * 60)

    toolkit = PublicMarketDataToolkit()

    # Get global indices (returns formatted markdown table)
    print("\n--- get_global_indices ---")
    result = toolkit.get_global_indices()
    print(result)


def indian_indices_usage():
    """Fetch Indian indices data."""
    print("\n" + "=" * 60)
    print("Public Market Data Toolkit - Indian Indices")
    print("=" * 60)

    toolkit = PublicMarketDataToolkit()

    # Get Indian indices (returns formatted markdown table)
    print("\n--- get_indian_indices ---")
    result = toolkit.get_indian_indices()
    print(result)


def fii_data_usage():
    """Fetch FII/FPI data from CDSL."""
    print("\n" + "=" * 60)
    print("Public Market Data Toolkit - FII Data")
    print("=" * 60)

    toolkit = PublicMarketDataToolkit()

    # List available fortnightly dates
    print("\n--- list_fii_fortnightly_dates ---")
    result = toolkit.list_fii_fortnightly_dates()
    print(result[:1000] + "\n... (truncated)")

    # Get fortnightly data
    print("\n--- get_fii_fortnightly_data ---")
    result = toolkit.get_fii_fortnightly_data("December 31, 2025")
    print(result[:1500] + "\n... (truncated)")


def list_toolkit_tools():
    """List all available tools in the toolkit."""
    print("\n" + "=" * 60)
    print("Public Market Data Toolkit - Available Tools")
    print("=" * 60)

    toolkit = PublicMarketDataToolkit()

    print(f"\nToolkit Name: {toolkit.name}")
    print(f"Number of tools: {len(toolkit.tools)}\n")

    print("Available tools:")
    for i, tool in enumerate(toolkit.tools, 1):
        func = tool
        name = func.__name__
        doc = func.__doc__ or ""
        first_line = doc.split("\n")[0] if doc else "No description"
        print(f"  {i}. {name}")
        print(f"     {first_line}")
        print()


def agno_agent_integration_example():
    """Example of integrating with an Agno agent."""
    print("\n" + "=" * 60)
    print("Agno Agent Integration Example")
    print("=" * 60)

    print("""
To use the Public Market Data toolkit with an Agno agent:

```python
from agno.agent import Agent
from agno.models.openai import OpenAIChat
from tools.public_market_data import PublicMarketDataToolkit

# Create agent with Public Market Data toolkit
agent = Agent(
    name="Market Analyst",
    model=OpenAIChat(id="gpt-4"),
    tools=[PublicMarketDataToolkit()],
    instructions=[
        "You are a market analyst specializing in global and Indian markets.",
        "Use the public market data tools to fetch real-time indices data.",
        "Provide analysis on FII/FPI flows and global market sentiment.",
    ],
)

# Example queries
agent.print_response("What are the global indices showing right now?")
agent.print_response("How are Asian markets performing compared to US markets?")
agent.print_response("Show me the FII investment data for the latest fortnight")
agent.print_response("Which Indian indices have F&O trading available?")
```

The toolkit provides these tools for the agent:

1. get_global_indices
   - Live prices for SGX Nifty, Dow, S&P 500, Nikkei, etc.
   - Useful for pre-market analysis and global sentiment

2. get_indian_indices
   - List of Indian indices with 52-week high/low
   - Shows F&O availability status

3. get_fii_monthly_data
   - Daily FII/FPI investment and derivative trading data
   - Asset-wise breakdown (Equity, Debt, Hybrid, MF, AIFs)

4. get_fii_fortnightly_data
   - Sector-wise FPI investment data
   - AUC and net investment by sector

5. list_fii_fortnightly_dates
   - Available report dates for fortnightly data
""")


def combined_market_overview():
    """Get a combined market overview."""
    print("\n" + "=" * 60)
    print("Combined Market Overview")
    print("=" * 60)

    toolkit = PublicMarketDataToolkit()

    # Global markets
    print("\n### Global Markets ###")
    print(toolkit.get_global_indices())

    # Indian indices (just first few)
    print("\n### Indian Indices (Top F&O enabled) ###")
    result = toolkit.get_indian_indices()
    # Print only lines with F&O enabled
    lines = result.split("\n")
    header_printed = False
    for line in lines:
        if "---" in line or "Index" in line or not line.strip():
            if not header_printed:
                print(line)
                if "---" in line:
                    header_printed = True
        elif "✓" in line:
            print(line)

    print("\n*Shows only F&O enabled indices*")


if __name__ == "__main__":
    list_toolkit_tools()
    global_indices_usage()
    indian_indices_usage()
    # fii_data_usage()  # Uncomment to test (fetches large HTML pages)
    agno_agent_integration_example()
    # combined_market_overview()  # Uncomment for combined view
