"""Examples for using the YahooFinanceToolkit with agents.

This script demonstrates how to:
- Use the toolkit directly for formatted output
- List available tools
- Integrate with Agno agents

The toolkit is designed to return formatted strings (markdown/text)
that are easy for LLMs to process and present to users.
"""

from tools.yahoo_finance import YahooFinanceToolkit


def list_available_tools():
    """List all available tools in the toolkit."""
    print("=" * 60)
    print("Available Tools in YahooFinanceToolkit")
    print("=" * 60)

    toolkit = YahooFinanceToolkit()

    print(f"\nToolkit name: {toolkit.name}")
    print(f"Total tools: {len(toolkit.tools)}")
    print("\n--- Tool List ---")

    for tool in toolkit.tools:
        # Get first line of docstring (tool description for agents)
        doc = tool.__doc__ or "No description"
        first_line = doc.split('\n')[0].strip()
        print(f"  {tool.__name__}: {first_line}")


def demo_get_stock_info():
    """Demo: Get stock information."""
    print("\n" + "=" * 60)
    print("Demo: get_stock_info")
    print("=" * 60)

    toolkit = YahooFinanceToolkit()
    result = toolkit.get_stock_info("AAPL")
    print(result)


def demo_get_stock_price():
    """Demo: Get quick price info."""
    print("\n" + "=" * 60)
    print("Demo: get_stock_price")
    print("=" * 60)

    toolkit = YahooFinanceToolkit()
    result = toolkit.get_stock_price("MSFT")
    print(result)


def demo_get_historical_prices():
    """Demo: Get historical prices."""
    print("\n" + "=" * 60)
    print("Demo: get_historical_prices")
    print("=" * 60)

    toolkit = YahooFinanceToolkit()
    result = toolkit.get_historical_prices("GOOGL", period="5d", interval="1d")
    print(result)


def demo_get_analyst_recommendations():
    """Demo: Get analyst recommendations."""
    print("\n" + "=" * 60)
    print("Demo: get_analyst_recommendations")
    print("=" * 60)

    toolkit = YahooFinanceToolkit()
    result = toolkit.get_analyst_recommendations("NVDA", limit=5)
    print(result)


def demo_get_options_chain():
    """Demo: Get options chain."""
    print("\n" + "=" * 60)
    print("Demo: get_options_chain")
    print("=" * 60)

    toolkit = YahooFinanceToolkit()
    result = toolkit.get_options_chain("AAPL")
    print(result)


def demo_get_dividends_splits():
    """Demo: Get dividends and splits."""
    print("\n" + "=" * 60)
    print("Demo: get_dividends_splits")
    print("=" * 60)

    toolkit = YahooFinanceToolkit()
    result = toolkit.get_dividends_splits("JNJ", limit=10)
    print(result)


def demo_get_news():
    """Demo: Get news."""
    print("\n" + "=" * 60)
    print("Demo: get_news")
    print("=" * 60)

    toolkit = YahooFinanceToolkit()
    result = toolkit.get_news("TSLA", limit=5)
    print(result)


def demo_search_tickers():
    """Demo: Search for tickers."""
    print("\n" + "=" * 60)
    print("Demo: search_tickers")
    print("=" * 60)

    toolkit = YahooFinanceToolkit()
    result = toolkit.search_tickers("Tesla", max_results=5)
    print(result)


def demo_get_sector_info():
    """Demo: Get sector information."""
    print("\n" + "=" * 60)
    print("Demo: get_sector_info")
    print("=" * 60)

    toolkit = YahooFinanceToolkit()
    result = toolkit.get_sector_info("technology")
    print(result)


def demo_screen_stocks():
    """Demo: Screen stocks."""
    print("\n" + "=" * 60)
    print("Demo: screen_stocks")
    print("=" * 60)

    toolkit = YahooFinanceToolkit()
    result = toolkit.screen_stocks("day_gainers", limit=10)
    print(result)


def demo_get_global_indexes():
    """Demo: Get global indexes."""
    print("\n" + "=" * 60)
    print("Demo: get_global_indexes")
    print("=" * 60)

    toolkit = YahooFinanceToolkit()
    result = toolkit.get_global_indexes()
    print(result)


def demo_get_fund_data():
    """Demo: Get ETF/fund data."""
    print("\n" + "=" * 60)
    print("Demo: get_fund_data")
    print("=" * 60)

    toolkit = YahooFinanceToolkit()
    result = toolkit.get_fund_data("SPY")
    print(result)


def demo_download_multiple():
    """Demo: Download multiple tickers."""
    print("\n" + "=" * 60)
    print("Demo: download_multiple")
    print("=" * 60)

    toolkit = YahooFinanceToolkit()
    result = toolkit.download_multiple("AAPL,MSFT,GOOGL", period="5d")
    print(result)


def demo_indian_stocks():
    """Demo: Indian stocks support."""
    print("\n" + "=" * 60)
    print("Demo: Indian Stocks Support")
    print("=" * 60)

    toolkit = YahooFinanceToolkit()

    print("\n--- Reliance Industries ---")
    result = toolkit.get_stock_price("RELIANCE.NS")
    print(result)

    print("\n--- TCS ---")
    result = toolkit.get_stock_price("TCS.NS")
    print(result)


def demo_agent_integration():
    """Demo: Example of how to integrate with Agno agent.

    Note: This is a demonstration of the pattern.
    The actual agent requires Agno framework to be installed.
    """
    print("\n" + "=" * 60)
    print("Demo: Agent Integration Pattern")
    print("=" * 60)

    print("""
# Example: Integrating with Agno Agent

```python
from agno.agent import Agent
from agno.models.openai import OpenAIChat
from tools.yahoo_finance import YahooFinanceToolkit

# Create the agent with Yahoo Finance toolkit
agent = Agent(
    model=OpenAIChat(id="gpt-4o"),
    tools=[YahooFinanceToolkit()],
    instructions=[
        "You are a financial analyst assistant.",
        "Use the Yahoo Finance toolkit to look up stock information.",
        "Provide clear, actionable insights based on the data.",
    ],
    markdown=True,
)

# Ask the agent about stocks
agent.print_response("What's the current price of Apple stock?")
agent.print_response("Compare Microsoft and Google - which has better analyst ratings?")
agent.print_response("Show me the top gaining stocks today")
agent.print_response("What are the top holdings in SPY ETF?")
```

# The toolkit automatically formats data for LLM consumption:
# - Stock info is formatted as markdown
# - Tables use markdown table format
# - Numbers are formatted with appropriate units (B, M, K)
# - Dates are human-readable
    """)

    # Show available tool signatures
    toolkit = YahooFinanceToolkit()
    print("\n--- Tool Signatures for Agent ---")
    for tool in toolkit.tools:
        doc = tool.__doc__ or ""
        first_line = doc.split('\n')[0].strip()
        print(f"\n{tool.__name__}:")
        print(f"  Description: {first_line}")


if __name__ == "__main__":
    # List all available tools
    list_available_tools()

    # Run demos
    demo_get_stock_info()
    demo_get_stock_price()
    demo_get_historical_prices()
    demo_get_analyst_recommendations()
    demo_get_options_chain()
    demo_get_dividends_splits()
    demo_get_news()
    demo_search_tickers()
    demo_get_sector_info()
    demo_screen_stocks()
    demo_get_global_indexes()
    demo_get_fund_data()
    demo_download_multiple()
    demo_indian_stocks()
    demo_agent_integration()
