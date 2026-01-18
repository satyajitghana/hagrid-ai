"""Examples for fetching options chain data from Yahoo Finance.

This script demonstrates how to:
- Fetch available expiration dates
- Get calls and puts for nearest expiration
- Analyze options by strike price
- Calculate implied volatility summary
- Analyze open interest distribution
"""

from tools.yahoo_finance import YFinanceClient


def fetch_options_overview(symbol: str = "AAPL"):
    """Fetch options chain overview."""
    print("=" * 60)
    print(f"Options Chain Overview for {symbol}")
    print("=" * 60)

    client = YFinanceClient()
    options = client.get_options(symbol)

    print(f"\nSymbol: {options.symbol}")
    print(f"Expiration Dates Available: {len(options.expiration_dates)}")

    if options.expiration_dates:
        print("\n--- Expiration Dates ---")
        for i, date in enumerate(options.expiration_dates[:10]):
            print(f"  {i+1}. {date}")
        if len(options.expiration_dates) > 10:
            print(f"  ... and {len(options.expiration_dates) - 10} more")

        print(f"\n--- Nearest Expiration: {options.expiration_dates[0]} ---")
        print(f"Calls: {len(options.calls)} contracts")
        print(f"Puts: {len(options.puts)} contracts")
    else:
        print("\nNo options available for this symbol")


def fetch_calls_chain(symbol: str = "MSFT"):
    """Fetch and display call options chain."""
    print("\n" + "=" * 60)
    print(f"Call Options Chain for {symbol}")
    print("=" * 60)

    client = YFinanceClient()
    options = client.get_options(symbol)

    if not options.calls:
        print("\nNo call options available")
        return

    # Get current price for reference
    info = client.get_ticker_info(symbol)
    current_price = info.info.get('currentPrice', 0)

    print(f"\nCurrent Stock Price: ${current_price:.2f}" if current_price else "\nCurrent Stock Price: N/A")
    print(f"Expiration: {options.expiration_dates[0] if options.expiration_dates else 'N/A'}")
    print()

    print(f"| {'Strike':>8} | {'Last':>8} | {'Bid':>8} | {'Ask':>8} | {'Volume':>8} | {'OI':>10} | {'IV':>8} | {'ITM':>5} |")
    print("|" + "-" * 10 + "|" + "-" * 10 + "|" + "-" * 10 + "|" + "-" * 10 + "|" + "-" * 10 + "|" + "-" * 12 + "|" + "-" * 10 + "|" + "-" * 7 + "|")

    # Filter to show strikes around current price
    for call in options.calls:
        strike = call.get('strike', 0)

        # Only show strikes within 20% of current price
        if current_price and (strike < current_price * 0.8 or strike > current_price * 1.2):
            continue

        last = call.get('lastPrice', 0)
        bid = call.get('bid', 0)
        ask = call.get('ask', 0)
        volume = call.get('volume', 0) or 0
        oi = call.get('openInterest', 0) or 0
        iv = call.get('impliedVolatility', 0)
        itm = "Yes" if call.get('inTheMoney', False) else "No"

        iv_str = f"{iv*100:.1f}%" if iv else "N/A"

        print(f"| {strike:>8.2f} | {last:>8.2f} | {bid:>8.2f} | {ask:>8.2f} | {volume:>8} | {oi:>10,} | {iv_str:>8} | {itm:>5} |")


def fetch_puts_chain(symbol: str = "GOOGL"):
    """Fetch and display put options chain."""
    print("\n" + "=" * 60)
    print(f"Put Options Chain for {symbol}")
    print("=" * 60)

    client = YFinanceClient()
    options = client.get_options(symbol)

    if not options.puts:
        print("\nNo put options available")
        return

    # Get current price for reference
    info = client.get_ticker_info(symbol)
    current_price = info.info.get('currentPrice', 0)

    print(f"\nCurrent Stock Price: ${current_price:.2f}" if current_price else "\nCurrent Stock Price: N/A")
    print(f"Expiration: {options.expiration_dates[0] if options.expiration_dates else 'N/A'}")
    print()

    print(f"| {'Strike':>8} | {'Last':>8} | {'Bid':>8} | {'Ask':>8} | {'Volume':>8} | {'OI':>10} | {'IV':>8} | {'ITM':>5} |")
    print("|" + "-" * 10 + "|" + "-" * 10 + "|" + "-" * 10 + "|" + "-" * 10 + "|" + "-" * 10 + "|" + "-" * 12 + "|" + "-" * 10 + "|" + "-" * 7 + "|")

    for put in options.puts:
        strike = put.get('strike', 0)

        # Only show strikes within 20% of current price
        if current_price and (strike < current_price * 0.8 or strike > current_price * 1.2):
            continue

        last = put.get('lastPrice', 0)
        bid = put.get('bid', 0)
        ask = put.get('ask', 0)
        volume = put.get('volume', 0) or 0
        oi = put.get('openInterest', 0) or 0
        iv = put.get('impliedVolatility', 0)
        itm = "Yes" if put.get('inTheMoney', False) else "No"

        iv_str = f"{iv*100:.1f}%" if iv else "N/A"

        print(f"| {strike:>8.2f} | {last:>8.2f} | {bid:>8.2f} | {ask:>8.2f} | {volume:>8} | {oi:>10,} | {iv_str:>8} | {itm:>5} |")


def analyze_options_volume(symbol: str = "NVDA"):
    """Analyze options volume and open interest."""
    print("\n" + "=" * 60)
    print(f"Options Volume Analysis for {symbol}")
    print("=" * 60)

    client = YFinanceClient()
    options = client.get_options(symbol)

    if not options.calls and not options.puts:
        print("\nNo options available")
        return

    # Calculate totals for calls
    call_volume = sum(c.get('volume', 0) or 0 for c in options.calls)
    call_oi = sum(c.get('openInterest', 0) or 0 for c in options.calls)

    # Calculate totals for puts
    put_volume = sum(p.get('volume', 0) or 0 for p in options.puts)
    put_oi = sum(p.get('openInterest', 0) or 0 for p in options.puts)

    print(f"\n--- Volume Summary ---")
    print(f"  Total Call Volume: {call_volume:,}")
    print(f"  Total Put Volume: {put_volume:,}")
    print(f"  Total Volume: {call_volume + put_volume:,}")
    print(f"  Put/Call Volume Ratio: {put_volume/call_volume:.2f}" if call_volume > 0 else "  Put/Call Volume Ratio: N/A")

    print(f"\n--- Open Interest Summary ---")
    print(f"  Total Call OI: {call_oi:,}")
    print(f"  Total Put OI: {put_oi:,}")
    print(f"  Total OI: {call_oi + put_oi:,}")
    print(f"  Put/Call OI Ratio (PCR): {put_oi/call_oi:.2f}" if call_oi > 0 else "  Put/Call OI Ratio: N/A")

    # Find max OI strikes
    if options.calls:
        max_call_oi = max(options.calls, key=lambda x: x.get('openInterest', 0) or 0)
        print(f"\n  Max Call OI Strike: ${max_call_oi.get('strike', 0):.2f} (OI: {max_call_oi.get('openInterest', 0):,})")

    if options.puts:
        max_put_oi = max(options.puts, key=lambda x: x.get('openInterest', 0) or 0)
        print(f"  Max Put OI Strike: ${max_put_oi.get('strike', 0):.2f} (OI: {max_put_oi.get('openInterest', 0):,})")


def analyze_implied_volatility(symbol: str = "AMZN"):
    """Analyze implied volatility across strikes."""
    print("\n" + "=" * 60)
    print(f"Implied Volatility Analysis for {symbol}")
    print("=" * 60)

    client = YFinanceClient()
    options = client.get_options(symbol)
    info = client.get_ticker_info(symbol)

    current_price = info.info.get('currentPrice', 0)

    if not options.calls and not options.puts:
        print("\nNo options available")
        return

    print(f"\nCurrent Stock Price: ${current_price:.2f}" if current_price else "\nCurrent Stock Price: N/A")

    # Calculate IV statistics for calls
    call_ivs = [c.get('impliedVolatility', 0) for c in options.calls if c.get('impliedVolatility')]
    put_ivs = [p.get('impliedVolatility', 0) for p in options.puts if p.get('impliedVolatility')]

    if call_ivs:
        print(f"\n--- Call IV Statistics ---")
        print(f"  Average IV: {sum(call_ivs)/len(call_ivs)*100:.1f}%")
        print(f"  Min IV: {min(call_ivs)*100:.1f}%")
        print(f"  Max IV: {max(call_ivs)*100:.1f}%")

    if put_ivs:
        print(f"\n--- Put IV Statistics ---")
        print(f"  Average IV: {sum(put_ivs)/len(put_ivs)*100:.1f}%")
        print(f"  Min IV: {min(put_ivs)*100:.1f}%")
        print(f"  Max IV: {max(put_ivs)*100:.1f}%")

    # Find ATM options IV
    if current_price and options.calls:
        # Find closest to ATM
        atm_call = min(options.calls, key=lambda x: abs(x.get('strike', 0) - current_price))
        atm_put = min(options.puts, key=lambda x: abs(x.get('strike', 0) - current_price)) if options.puts else None

        print(f"\n--- ATM Options (Strike ~${atm_call.get('strike', 0):.2f}) ---")
        call_iv = atm_call.get('impliedVolatility', 0)
        print(f"  ATM Call IV: {call_iv*100:.1f}%" if call_iv else "  ATM Call IV: N/A")
        if atm_put:
            put_iv = atm_put.get('impliedVolatility', 0)
            print(f"  ATM Put IV: {put_iv*100:.1f}%" if put_iv else "  ATM Put IV: N/A")


def find_high_volume_options(symbol: str = "TSLA"):
    """Find options with highest volume."""
    print("\n" + "=" * 60)
    print(f"High Volume Options for {symbol}")
    print("=" * 60)

    client = YFinanceClient()
    options = client.get_options(symbol)

    if not options.calls and not options.puts:
        print("\nNo options available")
        return

    # Sort calls by volume
    sorted_calls = sorted(options.calls, key=lambda x: x.get('volume', 0) or 0, reverse=True)

    # Sort puts by volume
    sorted_puts = sorted(options.puts, key=lambda x: x.get('volume', 0) or 0, reverse=True)

    print(f"\n--- Top 10 Calls by Volume ---")
    print(f"| {'Strike':>8} | {'Last':>8} | {'Volume':>10} | {'OI':>10} | {'IV':>8} |")
    print("|" + "-" * 10 + "|" + "-" * 10 + "|" + "-" * 12 + "|" + "-" * 12 + "|" + "-" * 10 + "|")

    for call in sorted_calls[:10]:
        strike = call.get('strike', 0)
        last = call.get('lastPrice', 0)
        volume = call.get('volume', 0) or 0
        oi = call.get('openInterest', 0) or 0
        iv = call.get('impliedVolatility', 0)
        iv_str = f"{iv*100:.1f}%" if iv else "N/A"

        print(f"| {strike:>8.2f} | {last:>8.2f} | {volume:>10,} | {oi:>10,} | {iv_str:>8} |")

    print(f"\n--- Top 10 Puts by Volume ---")
    print(f"| {'Strike':>8} | {'Last':>8} | {'Volume':>10} | {'OI':>10} | {'IV':>8} |")
    print("|" + "-" * 10 + "|" + "-" * 10 + "|" + "-" * 12 + "|" + "-" * 12 + "|" + "-" * 10 + "|")

    for put in sorted_puts[:10]:
        strike = put.get('strike', 0)
        last = put.get('lastPrice', 0)
        volume = put.get('volume', 0) or 0
        oi = put.get('openInterest', 0) or 0
        iv = put.get('impliedVolatility', 0)
        iv_str = f"{iv*100:.1f}%" if iv else "N/A"

        print(f"| {strike:>8.2f} | {last:>8.2f} | {volume:>10,} | {oi:>10,} | {iv_str:>8} |")


def calculate_straddle_price(symbol: str = "META"):
    """Calculate ATM straddle price."""
    print("\n" + "=" * 60)
    print(f"ATM Straddle Analysis for {symbol}")
    print("=" * 60)

    client = YFinanceClient()
    options = client.get_options(symbol)
    info = client.get_ticker_info(symbol)

    current_price = info.info.get('currentPrice', 0)

    if not current_price:
        print("\nCannot determine current price")
        return

    if not options.calls or not options.puts:
        print("\nNo options available")
        return

    print(f"\nCurrent Stock Price: ${current_price:.2f}")
    print(f"Expiration: {options.expiration_dates[0] if options.expiration_dates else 'N/A'}")

    # Find ATM strike
    atm_call = min(options.calls, key=lambda x: abs(x.get('strike', 0) - current_price))
    atm_strike = atm_call.get('strike', 0)

    # Find corresponding put
    atm_put = None
    for put in options.puts:
        if put.get('strike', 0) == atm_strike:
            atm_put = put
            break

    if not atm_put:
        atm_put = min(options.puts, key=lambda x: abs(x.get('strike', 0) - atm_strike))

    print(f"\n--- ATM Strike: ${atm_strike:.2f} ---")

    call_mid = (atm_call.get('bid', 0) + atm_call.get('ask', 0)) / 2
    put_mid = (atm_put.get('bid', 0) + atm_put.get('ask', 0)) / 2

    print(f"  Call Price (Mid): ${call_mid:.2f}")
    print(f"  Put Price (Mid): ${put_mid:.2f}")

    straddle_price = call_mid + put_mid
    print(f"\n  Straddle Price: ${straddle_price:.2f}")

    expected_move_pct = (straddle_price / current_price) * 100
    print(f"  Expected Move: {expected_move_pct:.1f}%")
    print(f"  Upper Breakeven: ${atm_strike + straddle_price:.2f}")
    print(f"  Lower Breakeven: ${atm_strike - straddle_price:.2f}")


def compare_pcr_across_stocks():
    """Compare Put/Call ratios across stocks."""
    print("\n" + "=" * 60)
    print("Put/Call Ratio Comparison")
    print("=" * 60)

    symbols = ["AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "TSLA"]
    client = YFinanceClient()

    print("\n| Symbol | Call OI    | Put OI     | PCR  | Sentiment  |")
    print("|--------|------------|------------|------|------------|")

    for symbol in symbols:
        try:
            options = client.get_options(symbol)

            call_oi = sum(c.get('openInterest', 0) or 0 for c in options.calls)
            put_oi = sum(p.get('openInterest', 0) or 0 for p in options.puts)

            pcr = put_oi / call_oi if call_oi > 0 else 0

            if pcr > 1.2:
                sentiment = "Bearish"
            elif pcr < 0.7:
                sentiment = "Bullish"
            else:
                sentiment = "Neutral"

            print(f"| {symbol:<6} | {call_oi:>10,} | {put_oi:>10,} | {pcr:.2f} | {sentiment:<10} |")
        except Exception as e:
            print(f"| {symbol:<6} | Error: {str(e)[:30]} |")


def show_options_greeks(symbol: str = "SPY"):
    """Show options with Greeks (if available)."""
    print("\n" + "=" * 60)
    print(f"Options Greeks for {symbol} (Near ATM)")
    print("=" * 60)

    client = YFinanceClient()
    options = client.get_options(symbol)
    info = client.get_ticker_info(symbol)

    current_price = info.info.get('currentPrice', 0)

    if not current_price or not options.calls:
        print("\nNo data available")
        return

    print(f"\nCurrent Price: ${current_price:.2f}")
    print()

    # Note: yfinance may not provide Greeks directly, but we can show what's available
    print("--- Call Options Near ATM ---")
    print(f"| {'Strike':>8} | {'Last':>8} | {'Bid':>8} | {'Ask':>8} | {'IV':>8} | {'Change':>8} |")
    print("|" + "-" * 10 + "|" + "-" * 10 + "|" + "-" * 10 + "|" + "-" * 10 + "|" + "-" * 10 + "|" + "-" * 10 + "|")

    for call in options.calls:
        strike = call.get('strike', 0)

        # Only show strikes within 5% of current price
        if abs(strike - current_price) / current_price > 0.05:
            continue

        last = call.get('lastPrice', 0)
        bid = call.get('bid', 0)
        ask = call.get('ask', 0)
        iv = call.get('impliedVolatility', 0)
        change = call.get('change', 0)

        iv_str = f"{iv*100:.1f}%" if iv else "N/A"
        change_str = f"{change:+.2f}" if change else "N/A"

        print(f"| {strike:>8.2f} | {last:>8.2f} | {bid:>8.2f} | {ask:>8.2f} | {iv_str:>8} | {change_str:>8} |")


if __name__ == "__main__":
    # Run all examples
    fetch_options_overview("AAPL")
    fetch_calls_chain("MSFT")
    fetch_puts_chain("GOOGL")
    analyze_options_volume("NVDA")
    analyze_implied_volatility("AMZN")
    find_high_volume_options("TSLA")
    calculate_straddle_price("META")
    compare_pcr_across_stocks()
    show_options_greeks("SPY")
