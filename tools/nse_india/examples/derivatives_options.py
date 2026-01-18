"""Examples of using Derivatives and Options APIs.

This example demonstrates how to fetch F&O data including:
- Futures contracts
- Most active options
- Option chain data
- Put-Call Ratio calculation
"""

import json

from tools.nse_india.client import NSEIndiaClient


def print_json(title: str, data: dict | list):
    """Pretty print JSON data with a title."""
    print(f"\n{'='*60}")
    print(f" {title}")
    print("=" * 60)
    print(json.dumps(data, indent=2, default=str))


def main():
    client = NSEIndiaClient()
    symbol = "RELIANCE"  # Must be an F&O enabled stock

    try:
        # First check if the stock is F&O enabled
        metadata = client.get_metadata(symbol)
        is_fno = metadata.get("isFNOSec") == "true"

        if not is_fno:
            print(f"{symbol} is not F&O enabled. Try RELIANCE, TCS, INFY, etc.")
            return

        print(f"\n{symbol} is F&O enabled. Fetching derivatives data...\n")

        # 1. Get derivatives filter (expiry dates, strike prices)
        derivatives_filter = client.get_symbol_derivatives_filter(symbol)
        print_json("Derivatives Filter (Expiry Dates)", {
            "expiryDates": derivatives_filter.get("expiryDates", [])[:5],
            "strikePrice": derivatives_filter.get("strikePrice", [])[:10],
        })

        # 2. Get all derivatives data (futures and options contracts)
        derivatives_data = client.get_symbol_derivatives_data(symbol)
        futures = derivatives_data.get("futuresData", [])
        options = derivatives_data.get("optionsData", [])
        print(f"\nTotal Futures Contracts: {len(futures)}")
        print(f"Total Options Contracts: {len(options)}")

        if futures:
            print_json("Near Month Future", futures[0])

        # 3. Get most active options by different criteria
        # By Calls
        most_active_calls = client.get_derivatives_most_active(symbol, call_type="C")
        print_json("Most Active Calls", most_active_calls.get("data", [])[:3])

        # By Puts
        most_active_puts = client.get_derivatives_most_active(symbol, call_type="P")
        print_json("Most Active Puts", most_active_puts.get("data", [])[:3])

        # By Open Interest
        most_active_oi = client.get_derivatives_most_active(symbol, call_type="O")
        print_json("Most Active by Open Interest", most_active_oi.get("data", [])[:3])

        # 4. Get option chain dropdown (expiry dates for option chain)
        option_dropdown = client.get_option_chain_dropdown(symbol)
        expiry_dates = option_dropdown.get("expiryDates", [])
        print_json("Option Chain Expiry Dates", expiry_dates[:5])

        # 5. Get full option chain for near month expiry
        if expiry_dates:
            near_month_expiry = expiry_dates[0]
            print(f"\nFetching option chain for expiry: {near_month_expiry}")

            option_chain = client.get_option_chain_data(symbol, near_month_expiry)
            chain_data = option_chain.get("data", [])

            # Calculate PCR (Put-Call Ratio)
            total_call_oi = 0
            total_put_oi = 0
            max_call_oi = 0
            max_call_oi_strike = 0
            max_put_oi = 0
            max_put_oi_strike = 0

            for item in chain_data:
                ce = item.get("CE", {})
                pe = item.get("PE", {})
                strike = item.get("strikePrice", 0)

                call_oi = ce.get("openInterest", 0)
                put_oi = pe.get("openInterest", 0)

                total_call_oi += call_oi
                total_put_oi += put_oi

                if call_oi > max_call_oi:
                    max_call_oi = call_oi
                    max_call_oi_strike = strike

                if put_oi > max_put_oi:
                    max_put_oi = put_oi
                    max_put_oi_strike = strike

            pcr = total_put_oi / total_call_oi if total_call_oi > 0 else 0

            print(f"\n{'='*60}")
            print(" Option Chain Analysis")
            print("=" * 60)
            print(f"Total Call OI: {total_call_oi:,}")
            print(f"Total Put OI: {total_put_oi:,}")
            print(f"PCR (OI): {pcr:.2f}")
            print(f"Max Call OI: {max_call_oi:,} @ Strike {max_call_oi_strike}")
            print(f"Max Put OI: {max_put_oi:,} @ Strike {max_put_oi_strike}")

            # Show sample of option chain data
            underlying = option_chain.get("underlyingValue", 0)
            print(f"\nUnderlying Value: {underlying}")

            # Find ATM strike
            atm_strike = min(
                [item.get("strikePrice", 0) for item in chain_data],
                key=lambda x: abs(x - underlying)
            )
            print(f"ATM Strike: {atm_strike}")

            # Show ATM options
            for item in chain_data:
                if item.get("strikePrice") == atm_strike:
                    ce = item.get("CE", {})
                    pe = item.get("PE", {})
                    print(f"\nATM Call (CE): LTP={ce.get('lastPrice')}, OI={ce.get('openInterest')}, IV={ce.get('impliedVolatility')}%")
                    print(f"ATM Put (PE): LTP={pe.get('lastPrice')}, OI={pe.get('openInterest')}, IV={pe.get('impliedVolatility')}%")
                    break

    finally:
        client.close()


if __name__ == "__main__":
    main()
