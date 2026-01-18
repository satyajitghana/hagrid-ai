"""FyersToolkit usage examples.

This example demonstrates how to use the FyersToolkit
which wraps the client methods for agent consumption.

The toolkit returns CSV-formatted strings optimized for LLM consumption.

Run from project root:
    python -m broker.fyers.examples.toolkit_usage
"""

import asyncio

from dotenv import load_dotenv
load_dotenv()

from broker.fyers import FyersClient, FyersConfig, FyersToolkit
from core.config import get_settings


def print_result(title: str, result: str):
    """Print toolkit result with title."""
    print(f"\n{'='*60}")
    print(f" {title}")
    print("="*60)
    # Show first 50 lines max
    lines = result.split('\n')
    for line in lines[:50]:
        print(line)
    if len(lines) > 50:
        print(f"... ({len(lines) - 50} more lines)")


async def main():
    settings = get_settings()

    config = FyersConfig(
        client_id=settings.FYERS_CLIENT_ID,
        secret_key=settings.FYERS_SECRET_KEY,
        token_file_path=settings.FYERS_TOKEN_FILE,
    )
    client = FyersClient(config)

    loaded = await client.load_saved_token()
    if not loaded:
        print("No valid token. Run: python -m scripts fyers login")
        return

    print(f"Authenticated as: {client.user_name}")

    # Create toolkit with all tools
    toolkit = FyersToolkit(client)
    print(f"\nToolkit created with {len(toolkit.tools)} tools")
    print(f"Cache enabled: {toolkit.cache.enabled}")

    # ==== 1. GET QUOTES ====
    symbols = ["NSE:SBIN-EQ", "NSE:TCS-EQ", "NSE:NIFTY50-INDEX"]
    result = await toolkit.get_quotes(symbols)
    print_result(f"get_quotes({symbols})", result)

    # ==== 2. GET MARKET DEPTH ====
    symbol = "NSE:SBIN-EQ"
    result = await toolkit.get_market_depth(symbol)
    print_result(f"get_market_depth('{symbol}')", result)

    # ==== 3. GET HISTORICAL DATA ====
    result = await toolkit.get_historical_data(
        symbol="NSE:SBIN-EQ",
        resolution="D",
        days=30
    )
    print_result("get_historical_data('NSE:SBIN-EQ', 'D', 30)", result)

    # ==== 4. GET OPTION CHAIN ====
    result = await toolkit.get_option_chain(
        symbol="NSE:NIFTY50-INDEX",
        strike_count=3
    )
    print_result("get_option_chain('NSE:NIFTY50-INDEX', 3)", result)

    # ==== 5. GET OPTION GREEKS ====
    try:
        result = await toolkit.get_option_greeks(
            symbol="NSE:NIFTY50-INDEX",
            strike_count=3
        )
        print_result("get_option_greeks('NSE:NIFTY50-INDEX', 3)", result)
    except Exception as e:
        print(f"\nget_option_greeks error: {e}")

    # ==== 6. GET TECHNICAL INDICATORS ====
    result = await toolkit.get_technical_indicators(
        symbol="NSE:SBIN-EQ",
        resolution="D",
        days=100
    )
    print_result("get_technical_indicators('NSE:SBIN-EQ', 'D', 100)", result)

    # ==== 7. GET POSITIONS ====
    result = await toolkit.get_positions()
    print_result("get_positions()", result)

    # ==== 8. GET ORDERS ====
    result = await toolkit.get_orders()
    print_result("get_orders()", result)

    # ==== 9. GET HOLDINGS ====
    result = await toolkit.get_holdings()
    print_result("get_holdings()", result)

    # ==== 10. GET FUNDS ====
    result = await toolkit.get_funds()
    print_result("get_funds()", result)

    # ==== 11. GET PROFILE ====
    result = await toolkit.get_profile()
    print_result("get_profile()", result)

    # ==== 12. GET MARKET STATUS ====
    result = await toolkit.get_market_status()
    print_result("get_market_status()", result)

    # ==== 13. GET CORRELATION MATRIX ====
    symbols = ["NSE:SBIN-EQ", "NSE:HDFCBANK-EQ", "NSE:ICICIBANK-EQ"]
    result = await toolkit.get_correlation_matrix(symbols, days=30)
    print_result(f"get_correlation_matrix({symbols}, 30)", result)

    # ==== 14. CACHE STATS ====
    cache_stats = toolkit.cache.stats()
    print(f"\n{'='*60}")
    print(" Cache Statistics")
    print("="*60)
    print(f"Enabled: {cache_stats['enabled']}")
    print(f"Memory entries: {cache_stats['memory_entries']}")
    print(f"Valid entries: {cache_stats['valid_memory_entries']}")
    print(f"File entries: {cache_stats['file_entries']}")

    print("\n" + "="*60)
    print(" Toolkit Usage Example Complete!")
    print("="*60)


if __name__ == "__main__":
    asyncio.run(main())
