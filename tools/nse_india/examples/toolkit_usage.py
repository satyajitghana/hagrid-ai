"""Examples for using the NSE India Toolkit with AI agents.

This script demonstrates how to:
- Initialize the toolkit
- Use toolkit methods (returns formatted strings for LLMs)
- Integrate with an Agno agent
"""

from tools.nse_india import NSEIndiaToolkit


def basic_toolkit_usage():
    """Basic usage of the NSE India toolkit."""
    print("=" * 60)
    print("NSE India Toolkit - Basic Usage")
    print("=" * 60)

    # Initialize toolkit
    toolkit = NSEIndiaToolkit()

    # Get equity announcements (returns formatted CSV string)
    print("\n--- get_equity_announcements ---")
    result = toolkit.get_equity_announcements(limit=5)
    print(result[:500] + "...\n")

    # Get announcements for specific symbol
    print("\n--- get_symbol_announcements ---")
    result = toolkit.get_symbol_announcements(symbol="RELIANCE", limit=3)
    print(result)

    # Get annual reports
    print("\n--- get_annual_reports ---")
    result = toolkit.get_annual_reports(symbol="TCS")
    print(result)


def shareholding_toolkit_usage():
    """Using shareholding tools."""
    print("\n" + "=" * 60)
    print("NSE India Toolkit - Shareholding Tools")
    print("=" * 60)

    toolkit = NSEIndiaToolkit()

    # Get shareholding pattern history (formatted markdown)
    print("\n--- get_shareholding_patterns ---")
    result = toolkit.get_shareholding_patterns(symbol="RELIANCE", limit=5)
    print(result)

    # Get detailed shareholding with shareholder names
    print("\n--- get_detailed_shareholding ---")
    result = toolkit.get_detailed_shareholding(symbol="RELIANCE")
    print(result)


def symbol_summary_toolkit_usage():
    """Using the symbol summary tool."""
    print("\n" + "=" * 60)
    print("NSE India Toolkit - Symbol Summary")
    print("=" * 60)

    toolkit = NSEIndiaToolkit()

    # Get comprehensive symbol summary (formatted markdown)
    print("\n--- get_symbol_summary ---")
    result = toolkit.get_symbol_summary(symbol="TCS")
    print(result[:2000] + "...\n")  # Truncated for readability


def list_toolkit_tools():
    """List all available tools in the toolkit."""
    print("\n" + "=" * 60)
    print("NSE India Toolkit - Available Tools")
    print("=" * 60)

    toolkit = NSEIndiaToolkit()

    print(f"\nToolkit Name: {toolkit.name}")
    print(f"Number of tools: {len(toolkit.tools)}\n")

    print("Available tools:")
    for i, tool in enumerate(toolkit.tools, 1):
        # Get function name and docstring
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
To use the NSE India toolkit with an Agno agent:

```python
from agno.agent import Agent
from agno.models.openai import OpenAIChat
from tools.nse_india import NSEIndiaToolkit

# Create agent with NSE India toolkit
agent = Agent(
    name="Stock Analyst",
    model=OpenAIChat(id="gpt-4"),
    tools=[NSEIndiaToolkit()],
    instructions=[
        "You are a stock market analyst specializing in NSE India stocks.",
        "Use the NSE India tools to fetch real-time data about stocks.",
        "Provide analysis based on corporate announcements, shareholding patterns, and financials.",
    ],
)

# Example queries
agent.print_response("What are the recent announcements for Reliance?")
agent.print_response("Show me the shareholding pattern trend for TCS")
agent.print_response("Who are the major shareholders of Infosys?")
agent.print_response("Give me a complete summary of HDFC Bank stock")
```

The toolkit provides these tools for the agent:
1. get_equity_announcements - Recent corporate announcements
2. get_debt_announcements - Debt market announcements
3. get_symbol_announcements - Announcements for specific symbol
4. get_new_announcements - Only new/unprocessed announcements
5. get_annual_reports - Annual report links
6. get_shareholding_patterns - Historical shareholding trend
7. get_detailed_shareholding - Individual shareholder names
8. get_symbol_summary - Comprehensive stock summary
""")


def custom_toolkit_configuration():
    """Example of custom toolkit configuration."""
    print("\n" + "=" * 60)
    print("Custom Toolkit Configuration")
    print("=" * 60)

    # Custom database and attachments directory
    toolkit = NSEIndiaToolkit(
        db_path="custom_nse.db",
        attachments_dir="./custom_attachments",
    )

    print(f"Toolkit initialized with:")
    print(f"  Database: custom_nse.db")
    print(f"  Attachments: ./custom_attachments")

    # The toolkit can track which announcements have been processed
    result = toolkit.get_new_announcements(index="equities", limit=3)
    print(f"\nNew announcements:\n{result}")


if __name__ == "__main__":
    basic_toolkit_usage()
    shareholding_toolkit_usage()
    # symbol_summary_toolkit_usage()  # Uncomment to test (takes longer)
    list_toolkit_tools()
    agno_agent_integration_example()
    custom_toolkit_configuration()
