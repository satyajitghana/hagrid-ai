"""Basic usage examples for FyersClient.

This example demonstrates how to:
1. Load environment and authenticate
2. Get user profile
3. Get account funds
4. Get market status

Run from project root:
    python -m broker.fyers.examples.basic_usage
"""

import asyncio
import json
from pathlib import Path

# Load env first
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

    print(f"Token file: {settings.FYERS_TOKEN_FILE}")
    print(f"Client ID: {settings.FYERS_CLIENT_ID}")

    # Create client
    config = FyersConfig(
        client_id=settings.FYERS_CLIENT_ID,
        secret_key=settings.FYERS_SECRET_KEY,
        token_file_path=settings.FYERS_TOKEN_FILE,
    )
    client = FyersClient(config)

    # Load saved token
    loaded = await client.load_saved_token()
    if not loaded:
        print("\nNo valid token found. Please run: python -m scripts fyers login")
        return

    print(f"\nAuthenticated as: {client.user_name} ({client.user_id})")

    # 1. Get Profile
    profile = await client.get_profile()
    print_json("User Profile", profile)

    # 2. Get Funds
    funds = await client.get_funds()
    print_json("Account Funds", funds)

    # 3. Get Market Status
    market_status = await client.get_market_status()
    print_json("Market Status", market_status)

    # 4. Get Holdings
    holdings = await client.get_holdings()
    print_json("Holdings", holdings)

    print("\n" + "="*60)
    print(" Basic Usage Example Complete!")
    print("="*60)


if __name__ == "__main__":
    asyncio.run(main())
