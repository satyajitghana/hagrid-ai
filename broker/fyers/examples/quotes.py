"""Quote and market data examples for FyersClient.

This example demonstrates how to:
1. Get real-time quotes for multiple symbols
2. Get market depth (order book)
3. Understand quote response structure

Run from project root:
    python -m broker.fyers.examples.quotes
"""

import asyncio
import json

from dotenv import load_dotenv
load_dotenv()

from broker.fyers import FyersClient, FyersConfig
from core.config import get_settings


def print_json(title: str, data):
    """Pretty print data with a title."""
    print(f"\n{'='*60}")
    print(f" {title}")
    print("=" * 60)
    if hasattr(data, 'model_dump'):
        print(json.dumps(data.model_dump(), indent=2, default=str))
    elif isinstance(data, (dict, list)):
        print(json.dumps(data, indent=2, default=str))
    else:
        print(data)


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

    # ==== 1. GET QUOTES FOR MULTIPLE SYMBOLS ====
    symbols = [
        "NSE:SBIN-EQ",
        "NSE:TCS-EQ",
        "NSE:RELIANCE-EQ",
        "NSE:NIFTY50-INDEX",
        "NSE:NIFTYBANK-INDEX",
    ]

    print(f"\nFetching quotes for: {symbols}")
    quotes = await client.get_quotes(symbols)
    print_json("Quotes Response", quotes)

    # Parse individual quotes
    if quotes.d:
        print("\n--- Parsed Quotes ---")
        for quote in quotes.d:
            v = quote.v  # v is a dict
            print(f"\n{quote.n}:")
            print(f"  LTP: {v.get('lp')}")
            print(f"  Change: {v.get('ch')} ({v.get('chp')}%)")
            print(f"  Open: {v.get('open_price')}, High: {v.get('high_price')}, Low: {v.get('low_price')}")
            print(f"  Prev Close: {v.get('prev_close_price')}")
            print(f"  Volume: {v.get('volume')}")
            print(f"  Bid: {v.get('bid')}, Ask: {v.get('ask')}")

    # ==== 2. GET MARKET DEPTH (ORDER BOOK) ====
    symbol = "NSE:SBIN-EQ"
    print(f"\n\nFetching market depth for: {symbol}")
    depth = await client.get_market_depth(symbol, ohlcv_flag=1)
    print_json("Market Depth Response", depth)

    # Parse depth data
    if depth.d:
        data = depth.d.get(symbol, {})
        print("\n--- Parsed Market Depth ---")
        print(f"LTP: {data.get('ltp')}")
        print(f"Total Buy Qty: {data.get('totalbuyqty')}")
        print(f"Total Sell Qty: {data.get('totalsellqty')}")

        print("\nBids (Price, Volume, Orders):")
        for bid in data.get('bids', [])[:5]:
            print(f"  {bid.get('price')} x {bid.get('volume')} ({bid.get('ord')} orders)")

        print("\nAsks (Price, Volume, Orders):")
        for ask in data.get('ask', [])[:5]:
            print(f"  {ask.get('price')} x {ask.get('volume')} ({ask.get('ord')} orders)")

    print("\n" + "="*60)
    print(" Quotes Example Complete!")
    print("="*60)


if __name__ == "__main__":
    asyncio.run(main())
