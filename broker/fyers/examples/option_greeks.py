"""Option Greeks examples for FyersClient.

This example demonstrates how to:
1. Get option chain with raw data
2. Understand expiry data structure
3. Compute Greeks (IV, Delta, Gamma, Theta, Vega)
4. Verify Greeks calculations

Run from project root:
    python -m broker.fyers.examples.option_greeks
"""

import asyncio
import json
from datetime import datetime

from dotenv import load_dotenv
load_dotenv()

from broker.fyers import FyersClient, FyersConfig
from core.config import get_settings


def print_section(title: str):
    print(f"\n{'='*60}")
    print(f" {title}")
    print("="*60)


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

    symbol = "NSE:NIFTY50-INDEX"

    # ==== 1. GET RAW OPTION CHAIN DATA ====
    print_section("1. Raw Option Chain Data Structure")

    oc = await client.get_option_chain(symbol, strike_count=3)
    print(f"Status: {oc.s}")
    print(f"Data keys: {list(oc.data.keys()) if oc.data else None}")

    # Expiry data - critical for Greeks
    print("\nExpiry Data (first 3):")
    expiry_data = oc.data.get('expiryData', []) if oc.data else []
    for exp in expiry_data[:3]:
        date_str = exp.get('date')
        epoch = exp.get('expiry')
        expiry_dt = datetime.fromtimestamp(int(epoch)) if epoch else None
        print(f"  Date: {date_str}, Epoch: {epoch}, Parsed: {expiry_dt}")

    # India VIX
    print("\nIndia VIX:")
    vix = oc.data.get('indiavixData', {}) if oc.data else {}
    print(f"  LTP: {vix.get('ltp')}, Change: {vix.get('ltpch')} ({vix.get('ltpchp')}%)")

    # OI Summary
    print(f"\nOI Summary:")
    print(f"  Total Call OI: {oc.get_call_oi():,}")
    print(f"  Total Put OI: {oc.get_put_oi():,}")
    print(f"  PCR (OI): {oc.get_put_oi() / oc.get_call_oi():.2f}" if oc.get_call_oi() > 0 else "  PCR: N/A")

    # ==== 2. OPTION CHAIN DETAILS ====
    print_section("2. Option Chain Details")

    options = oc.get_options_chain()
    print(f"Total options: {len(options)}")

    # First option is the underlying spot
    if options:
        underlying = options[0]
        print(f"\nUnderlying: {underlying.get('symbol')}")
        print(f"  Spot Price: {underlying.get('ltp')}")

    # Sample call and put
    calls = [o for o in options if o.get('option_type') == 'CE']
    puts = [o for o in options if o.get('option_type') == 'PE']

    if calls:
        print("\nSample Call Option:")
        call = calls[0]
        for k in ['symbol', 'strike_price', 'ltp', 'bid', 'ask', 'oi', 'volume', 'ltpch', 'ltpchp']:
            print(f"  {k}: {call.get(k)}")

    if puts:
        print("\nSample Put Option:")
        put = puts[0]
        for k in ['symbol', 'strike_price', 'ltp', 'bid', 'ask', 'oi', 'volume', 'ltpch', 'ltpchp']:
            print(f"  {k}: {put.get(k)}")

    # ==== 3. COMPUTE GREEKS MANUALLY ====
    print_section("3. Manual Greeks Computation")

    # Get spot price
    quotes = await client.get_quotes([symbol])
    spot_price = quotes.d[0].v.get('lp') if quotes.d else None
    print(f"Spot Price: {spot_price}")

    # Get nearest expiry
    nearest_expiry = expiry_data[0] if expiry_data else None
    if nearest_expiry:
        expiry_epoch = int(nearest_expiry.get('expiry'))
        expiry_dt = datetime.fromtimestamp(expiry_epoch)
        now = datetime.now()
        days_to_expiry = (expiry_dt - now).days + (expiry_dt - now).seconds / 86400
        print(f"Nearest Expiry: {nearest_expiry.get('date')} ({days_to_expiry:.2f} days)")

        # Try to compute Greeks for one option
        if calls and spot_price and days_to_expiry > 0:
            from broker.fyers.utils.greeks import compute_greeks, implied_volatility

            call = calls[0]
            strike = call.get('strike_price')
            premium = call.get('ltp')
            bid = call.get('bid')
            ask = call.get('ask')

            print(f"\nComputing Greeks for {call.get('symbol')}:")
            print(f"  Strike: {strike}")
            print(f"  Premium: {premium}")
            print(f"  Bid/Ask: {bid}/{ask}")

            time_to_expiry_years = days_to_expiry / 365
            risk_free_rate = 0.065  # 6.5%

            try:
                # First compute IV from market price
                iv = implied_volatility(
                    market_price=premium,
                    S=spot_price,
                    K=strike,
                    T=time_to_expiry_years,
                    r=risk_free_rate,
                    option_type='CE',
                )
                print(f"\n  Computed IV: {iv * 100:.2f}%")

                # Then compute Greeks using the IV
                greeks = compute_greeks(
                    S=spot_price,
                    K=strike,
                    T=time_to_expiry_years,
                    r=risk_free_rate,
                    sigma=iv,
                    option_type='CE',
                )
                print(f"\nComputed Greeks:")
                print(f"  Delta: {greeks.get('delta'):.4f}")
                print(f"  Gamma: {greeks.get('gamma'):.6f}")
                print(f"  Theta: {greeks.get('theta'):.4f} (per day)")
                print(f"  Vega: {greeks.get('vega'):.4f} (per 1% IV)")
                print(f"  Rho: {greeks.get('rho'):.4f} (per 1% rate)")
            except Exception as e:
                print(f"  Error computing Greeks: {e}")
                import traceback
                traceback.print_exc()
        else:
            print("Cannot compute Greeks: Missing data or expiry passed")

    # ==== 4. USE CLIENT'S get_option_greeks ====
    print_section("4. Using client.get_option_greeks()")

    try:
        greeks_data = await client.get_option_greeks(symbol, strike_count=3)
        print(f"Total options with Greeks: {len(greeks_data)}")

        # Show first few with Greeks
        print("\nOptions with computed Greeks:")
        for opt in greeks_data[1:5]:  # Skip underlying
            if opt.get('iv'):
                print(f"\n  {opt.get('symbol')}:")
                print(f"    Strike: {opt.get('strike')}, Type: {opt.get('option_type')}")
                print(f"    LTP: {opt.get('ltp')}, Days to Expiry: {opt.get('time_to_expiry_days'):.2f}")
                print(f"    IV: {opt.get('iv'):.2f}%")
                print(f"    Delta: {opt.get('delta'):.4f}")
                print(f"    Gamma: {opt.get('gamma'):.6f}")
                print(f"    Theta: {opt.get('theta'):.4f}")
                print(f"    Vega: {opt.get('vega'):.4f}")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

    # ==== 5. VERIFY GREEKS CALCULATION ====
    print_section("5. Greeks Verification")

    print("""
Greeks Sanity Checks:
- IV should be positive (typically 10-50% for index options)
- Delta should be between -1 and 1 (CE: 0 to 1, PE: -1 to 0)
- Gamma should be positive and highest near ATM
- Theta should be negative (time decay)
- Vega should be positive (higher IV = higher premium)

If Greeks are empty, check:
1. Is expiry data being extracted correctly?
2. Is time_to_expiry > 0?
3. Is spot price available?
""")

    print("\n" + "="*60)
    print(" Option Greeks Example Complete!")
    print("="*60)


if __name__ == "__main__":
    asyncio.run(main())
