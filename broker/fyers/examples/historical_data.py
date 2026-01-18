"""Historical data examples for FyersClient.

This example demonstrates how to:
1. Get daily OHLCV candles
2. Get intraday candles (1min, 5min, 15min, etc.)
3. Work with the candle data

Run from project root:
    python -m broker.fyers.examples.historical_data
"""

import asyncio
import json
from datetime import datetime, timedelta

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

    symbol = "NSE:SBIN-EQ"

    # ==== 1. DAILY CANDLES (Last 30 days) ====
    range_to = datetime.now().strftime("%Y-%m-%d")
    range_from = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")

    print(f"\nFetching daily candles for {symbol}")
    print(f"From: {range_from} to {range_to}")

    history = await client.get_history(
        symbol=symbol,
        resolution="D",
        date_format=1,
        range_from=range_from,
        range_to=range_to,
    )

    print(f"\nResponse status: {history.s}")
    print(f"Total candles: {len(history.candles) if history.candles else 0}")

    if history.candles:
        print("\n--- Last 5 Daily Candles ---")
        print("Timestamp, Open, High, Low, Close, Volume")
        for candle in history.candles[-5:]:
            # candle format: [timestamp, open, high, low, close, volume]
            ts = datetime.fromtimestamp(candle[0]).strftime("%Y-%m-%d")
            print(f"{ts}: O={candle[1]}, H={candle[2]}, L={candle[3]}, C={candle[4]}, V={candle[5]}")

    # ==== 2. INTRADAY CANDLES (5-minute, last 5 days) ====
    range_to = datetime.now().strftime("%Y-%m-%d")
    range_from = (datetime.now() - timedelta(days=5)).strftime("%Y-%m-%d")

    print(f"\n\nFetching 5-minute candles for {symbol}")
    print(f"From: {range_from} to {range_to}")

    history_5min = await client.get_history(
        symbol=symbol,
        resolution="5",
        date_format=1,
        range_from=range_from,
        range_to=range_to,
    )

    print(f"\nResponse status: {history_5min.s}")
    print(f"Total candles: {len(history_5min.candles) if history_5min.candles else 0}")

    if history_5min.candles:
        print("\n--- Last 10 x 5-minute Candles ---")
        print("DateTime, Open, High, Low, Close, Volume")
        for candle in history_5min.candles[-10:]:
            ts = datetime.fromtimestamp(candle[0]).strftime("%Y-%m-%d %H:%M")
            print(f"{ts}: O={candle[1]}, H={candle[2]}, L={candle[3]}, C={candle[4]}, V={candle[5]}")

    # ==== 3. INDEX HISTORICAL DATA ====
    index_symbol = "NSE:NIFTY50-INDEX"
    print(f"\n\nFetching daily candles for {index_symbol}")

    index_history = await client.get_history(
        symbol=index_symbol,
        resolution="D",
        date_format=1,
        range_from=(datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d"),
        range_to=datetime.now().strftime("%Y-%m-%d"),
    )

    if index_history.candles:
        print(f"Total candles: {len(index_history.candles)}")
        print("\n--- Last 5 Index Candles ---")
        for candle in index_history.candles[-5:]:
            ts = datetime.fromtimestamp(candle[0]).strftime("%Y-%m-%d")
            print(f"{ts}: O={candle[1]:.2f}, H={candle[2]:.2f}, L={candle[3]:.2f}, C={candle[4]:.2f}")

    print("\n" + "="*60)
    print(" Historical Data Example Complete!")
    print("="*60)


if __name__ == "__main__":
    asyncio.run(main())
