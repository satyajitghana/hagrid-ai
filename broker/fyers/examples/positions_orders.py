"""Positions and orders examples for FyersClient.

This example demonstrates how to:
1. Get current positions
2. Get today's orders
3. Get tradebook (executed trades)

Note: This is read-only. Order placement examples are in a separate file.

Run from project root:
    python -m broker.fyers.examples.positions_orders
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

    # ==== 1. GET POSITIONS ====
    print("\n" + "="*60)
    print(" Current Positions")
    print("="*60)

    positions = await client.get_positions()
    print_json("Positions Response", positions)

    if positions.net_positions:
        print("\n--- Net Positions ---")
        total_pnl = 0
        for pos in positions.net_positions:
            side = "LONG" if pos.side == 1 else "SHORT" if pos.side == -1 else "CLOSED"
            pnl = (pos.realized_profit or 0) + (pos.unrealized_profit or 0)
            total_pnl += pnl
            print(f"\n{pos.symbol}:")
            print(f"  Side: {side}, Qty: {pos.net_qty}")
            print(f"  Avg Price: {pos.net_avg}")
            print(f"  LTP: {pos.ltp}")
            print(f"  Realized P&L: {pos.realized_profit}")
            print(f"  Unrealized P&L: {pos.unrealized_profit}")
            print(f"  Product: {pos.product_type}")

        print(f"\n--- Total P&L: {total_pnl:.2f} ---")
    else:
        print("\nNo open positions")

    # ==== 2. GET ORDERS ====
    print("\n" + "="*60)
    print(" Today's Orders")
    print("="*60)

    orders = await client.get_orders()
    print_json("Orders Response (raw)", orders)

    if orders.order_book:
        print("\n--- Order Book ---")
        status_map = {
            1: "CANCELLED",
            2: "TRADED",
            4: "TRANSIT",
            5: "REJECTED",
            6: "PENDING",
            7: "EXPIRED"
        }
        for order in orders.order_book:
            side = "BUY" if order.side == 1 else "SELL"
            status = status_map.get(order.status, f"UNKNOWN({order.status})")
            print(f"\n{order.symbol}:")
            print(f"  Order ID: {order.id}")
            print(f"  Side: {side}, Qty: {order.qty}, Filled: {order.filled_qty}")
            print(f"  Type: {order.type}, Status: {status}")
            print(f"  Price: {order.limit_price}")
            print(f"  Message: {order.message or 'N/A'}")
    else:
        print("\nNo orders today")

    # ==== 3. GET TRADEBOOK ====
    print("\n" + "="*60)
    print(" Today's Trades (Executed)")
    print("="*60)

    trades = await client.get_tradebook()
    print_json("Tradebook Response", trades)

    if trades.trade_book:
        print("\n--- Trade Book ---")
        for trade in trades.trade_book:
            side = "BUY" if trade.side == 1 else "SELL"
            print(f"\n{trade.symbol}:")
            print(f"  Trade ID: {trade.id}")
            print(f"  Order ID: {trade.order_id}")
            print(f"  Side: {side}, Qty: {trade.traded_qty}")
            print(f"  Price: {trade.trade_price}")
            print(f"  Time: {trade.order_datetime}")
    else:
        print("\nNo trades executed today")

    print("\n" + "="*60)
    print(" Positions & Orders Example Complete!")
    print("="*60)


if __name__ == "__main__":
    asyncio.run(main())
