"""Option chain examples for FyersClient.

This example demonstrates how to:
1. Get option chain data for an index/stock
2. Get option Greeks (IV, Delta, Gamma, Theta, Vega)
3. Analyze PCR (Put-Call Ratio) and OI

Run from project root:
    python -m broker.fyers.examples.option_chain
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

    # ==== 1. GET OPTION CHAIN FOR NIFTY ====
    symbol = "NSE:NIFTY50-INDEX"
    strike_count = 5  # 5 strikes above and below ATM

    print(f"\nFetching option chain for {symbol}")
    print(f"Strike count: {strike_count} (above + below ATM)")

    option_chain = await client.get_option_chain(symbol, strike_count=strike_count)

    print(f"\nResponse status: {option_chain.s}")

    if option_chain.data:
        oc_data = option_chain.data
        print(f"Spot Price: {oc_data.ltp}")
        print(f"ATM Strike: {oc_data.atm}")
        print(f"Lot Size: {oc_data.lot_size}")
        print(f"Total Options: {len(oc_data.options_chain) if oc_data.options_chain else 0}")

        # Separate calls and puts
        calls = [o for o in oc_data.options_chain if o.option_type == "CE"]
        puts = [o for o in oc_data.options_chain if o.option_type == "PE"]

        print(f"\n--- Call Options (CE) ---")
        print("Strike, LTP, OI, Volume, IV, Change%")
        for opt in sorted(calls, key=lambda x: x.strike_price)[:5]:
            print(f"{opt.strike_price}: LTP={opt.ltp}, OI={opt.oi}, Vol={opt.volume}, IV={opt.iv}, Chg={opt.chp}%")

        print(f"\n--- Put Options (PE) ---")
        print("Strike, LTP, OI, Volume, IV, Change%")
        for opt in sorted(puts, key=lambda x: x.strike_price)[:5]:
            print(f"{opt.strike_price}: LTP={opt.ltp}, OI={opt.oi}, Vol={opt.volume}, IV={opt.iv}, Chg={opt.chp}%")

        # Calculate PCR
        total_call_oi = sum(o.oi for o in calls if o.oi)
        total_put_oi = sum(o.oi for o in puts if o.oi)
        pcr = total_put_oi / total_call_oi if total_call_oi > 0 else 0

        print(f"\n--- PCR Analysis ---")
        print(f"Total Call OI: {total_call_oi:,}")
        print(f"Total Put OI: {total_put_oi:,}")
        print(f"PCR (OI): {pcr:.2f}")
        if pcr > 1.2:
            print("Interpretation: Bullish (more put writers)")
        elif pcr < 0.8:
            print("Interpretation: Bearish (more call writers)")
        else:
            print("Interpretation: Neutral")

    # ==== 2. GET OPTION GREEKS ====
    print(f"\n\nFetching option Greeks for {symbol}")

    try:
        greeks = await client.get_option_greeks(symbol, strike_count=3)

        print(f"\nTotal options with Greeks: {len(greeks)}")

        print("\n--- Options with Greeks ---")
        print("Symbol, Strike, Type, LTP, IV%, Delta, Gamma, Theta, Vega")
        for opt in greeks[:10]:
            print(
                f"{opt.get('symbol', 'N/A')[:30]}: "
                f"K={opt.get('strike', 'N/A')}, "
                f"Type={opt.get('option_type', 'N/A')}, "
                f"LTP={opt.get('ltp', 'N/A')}, "
                f"IV={opt.get('iv', 'N/A'):.1f}%, "
                f"Delta={opt.get('delta', 'N/A'):.3f}, "
                f"Gamma={opt.get('gamma', 'N/A'):.5f}, "
                f"Theta={opt.get('theta', 'N/A'):.2f}, "
                f"Vega={opt.get('vega', 'N/A'):.2f}"
            )
    except Exception as e:
        print(f"Error fetching Greeks: {e}")

    # ==== 3. GET OPTION CHAIN FOR A STOCK ====
    stock_symbol = "NSE:SBIN-EQ"
    print(f"\n\nFetching option chain for stock: {stock_symbol}")

    stock_oc = await client.get_option_chain(stock_symbol, strike_count=3)

    if stock_oc.data and stock_oc.data.options_chain:
        print(f"Spot Price: {stock_oc.data.ltp}")
        print(f"ATM Strike: {stock_oc.data.atm}")
        print(f"Options count: {len(stock_oc.data.options_chain)}")

        print("\n--- Sample Options ---")
        for opt in stock_oc.data.options_chain[:6]:
            print(f"{opt.symbol}: Strike={opt.strike_price}, Type={opt.option_type}, LTP={opt.ltp}, OI={opt.oi}")
    else:
        print("No option chain data available for this stock")

    print("\n" + "="*60)
    print(" Option Chain Example Complete!")
    print("="*60)


if __name__ == "__main__":
    asyncio.run(main())
