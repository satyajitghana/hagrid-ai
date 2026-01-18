"""Examples for using the Option Chain APIs.

This script demonstrates how to:
- Fetch option contract info (expiry dates and strikes)
- Get full option chain data
- Analyze PCR (Put-Call Ratio)
- Find max OI strikes (support/resistance)
- Get ATM and near-ATM strikes
- Analyze option chain sentiment
"""

from tools.nse_india.client import NSEIndiaClient


def fetch_option_contract_info(symbol: str = "GAIL"):
    """Fetch available expiry dates and strike prices for a symbol."""
    print("=" * 60)
    print(f"Option Contract Info for {symbol}")
    print("=" * 60)

    client = NSEIndiaClient()

    contract_info = client.get_option_contract_info(symbol)

    print(f"\nExpiry Dates ({len(contract_info.expiry_dates)}):")
    for expiry in contract_info.expiry_dates[:5]:
        print(f"  - {expiry}")
    if len(contract_info.expiry_dates) > 5:
        print(f"  ... and {len(contract_info.expiry_dates) - 5} more")

    print(f"\nStrike Prices ({len(contract_info.strike_prices)}):")
    strike_floats = contract_info.strike_prices_float
    if strike_floats:
        print(f"  Range: {min(strike_floats):.2f} to {max(strike_floats):.2f}")
        print(f"  Sample: {strike_floats[:10]}")

    client.close()


def fetch_option_chain(symbol: str = "GAIL", expiry: str | None = None):
    """Fetch full option chain for a symbol and expiry."""
    print("\n" + "=" * 60)
    print(f"Option Chain for {symbol}")
    print("=" * 60)

    client = NSEIndiaClient()

    # Get expiry if not provided
    if expiry is None:
        contract_info = client.get_option_contract_info(symbol)
        if not contract_info.expiry_dates:
            print(f"No options available for {symbol}")
            client.close()
            return
        expiry = contract_info.expiry_dates[0]

    print(f"Expiry: {expiry}\n")

    chain = client.get_option_chain(symbol, expiry)

    print(f"Timestamp: {chain.timestamp}")
    print(f"Underlying Value: {chain.underlying_value:.2f}")
    print(f"Total Strikes: {len(chain.data)}")
    print(f"ATM Strike: {chain.atm_strike:.2f}")
    print()

    # OI Summary
    print("Open Interest Summary:")
    print(f"  Total CE OI: {chain.total_ce_oi:,}")
    print(f"  Total PE OI: {chain.total_pe_oi:,}")
    print(f"  PCR: {chain.pcr:.2f}")
    print()

    # Max OI
    max_ce = chain.max_ce_oi_strike
    max_pe = chain.max_pe_oi_strike
    print("Max Open Interest:")
    print(f"  Max CE OI @ {max_ce[0]:.2f}: {max_ce[1]:,} (Resistance)")
    print(f"  Max PE OI @ {max_pe[0]:.2f}: {max_pe[1]:,} (Support)")
    print()

    # ATM Data
    atm_data = chain.get_atm_data()
    if atm_data:
        print(f"ATM Strike ({atm_data.strike_price:.2f}):")
        if atm_data.ce:
            print(f"  CE: LTP={atm_data.ce.last_price:.2f}, IV={atm_data.ce.implied_volatility:.2f}%, OI={atm_data.ce.open_interest:,}")
        if atm_data.pe:
            print(f"  PE: LTP={atm_data.pe.last_price:.2f}, IV={atm_data.pe.implied_volatility:.2f}%, OI={atm_data.pe.open_interest:,}")

    client.close()


def analyze_option_chain(symbol: str = "RELIANCE"):
    """Analyze option chain and generate summary."""
    print("\n" + "=" * 60)
    print(f"Option Chain Analysis for {symbol}")
    print("=" * 60)

    client = NSEIndiaClient()

    # Get near month expiry
    contract_info = client.get_option_contract_info(symbol)
    if not contract_info.expiry_dates:
        print(f"No options available for {symbol}")
        client.close()
        return

    expiry = contract_info.expiry_dates[0]
    analysis = client.get_option_chain_analysis(symbol, expiry)

    print(f"\nExpiry: {analysis.expiry}")
    print(f"Underlying: {analysis.underlying_value:.2f}")
    print(f"Timestamp: {analysis.timestamp}")
    print()

    print("Market Sentiment Analysis:")
    print(f"  PCR: {analysis.pcr:.2f}")
    print(f"  Sentiment: {analysis.sentiment}")
    print()

    print("Key Levels:")
    print(f"  ATM Strike: {analysis.atm_strike:.2f}")
    print(f"  Resistance (Max CE OI): {analysis.resistance_level:.2f} ({analysis.max_ce_oi:,} contracts)")
    print(f"  Support (Max PE OI): {analysis.support_level:.2f} ({analysis.max_pe_oi:,} contracts)")
    print()

    print("ATM Option Prices:")
    print(f"  CE: LTP={analysis.atm_ce_ltp:.2f}, IV={analysis.atm_ce_iv:.2f}%")
    print(f"  PE: LTP={analysis.atm_pe_ltp:.2f}, IV={analysis.atm_pe_iv:.2f}%")

    # Calculate straddle price
    straddle = analysis.atm_ce_ltp + analysis.atm_pe_ltp
    print(f"\nATM Straddle Price: {straddle:.2f}")
    if analysis.underlying_value > 0:
        straddle_pct = (straddle / analysis.underlying_value) * 100
        print(f"Expected Move: {straddle_pct:.2f}%")

    client.close()


def fetch_pcr_data(symbols: list[str] | None = None):
    """Fetch PCR data for multiple symbols."""
    print("\n" + "=" * 60)
    print("Put-Call Ratio Comparison")
    print("=" * 60)

    if symbols is None:
        symbols = ["RELIANCE", "TCS", "INFY", "HDFCBANK", "SBIN"]

    client = NSEIndiaClient()

    print("\n| Symbol    | PCR  | CE OI      | PE OI      | Sentiment |")
    print("|-----------|------|------------|------------|-----------|")

    for symbol in symbols:
        try:
            pcr_data = client.get_option_chain_pcr(symbol)
            pcr = pcr_data["pcr"]
            ce_oi = pcr_data["total_ce_oi"]
            pe_oi = pcr_data["total_pe_oi"]

            # Determine sentiment
            if pcr > 1.2:
                sentiment = "Bullish"
            elif pcr < 0.8:
                sentiment = "Bearish"
            else:
                sentiment = "Neutral"

            print(f"| {symbol:9} | {pcr:.2f} | {ce_oi:>10,} | {pe_oi:>10,} | {sentiment:9} |")
        except Exception as e:
            print(f"| {symbol:9} | Error: {str(e)[:30]} |")

    client.close()


def fetch_max_pain_data(symbol: str = "NIFTY"):
    """Fetch max pain and support/resistance levels."""
    print("\n" + "=" * 60)
    print(f"Max Pain Analysis for {symbol}")
    print("=" * 60)

    client = NSEIndiaClient()

    # Determine if index or equity
    security_type = "Index" if symbol in ["NIFTY", "BANKNIFTY", "FINNIFTY"] else "Equity"

    max_pain = client.get_max_pain(symbol, security_type=security_type)

    print(f"\nUnderlying Value: {max_pain['underlying_value']:.2f}")
    print()
    print("Key Levels:")
    print(f"  Max CE OI Strike: {max_pain['max_ce_oi_strike']:.2f} (Resistance)")
    print(f"    OI: {max_pain['max_ce_oi']:,} contracts")
    print(f"  Max PE OI Strike: {max_pain['max_pe_oi_strike']:.2f} (Support)")
    print(f"    OI: {max_pain['max_pe_oi']:,} contracts")

    # Calculate range
    underlying = max_pain['underlying_value']
    resistance = max_pain['max_ce_oi_strike']
    support = max_pain['max_pe_oi_strike']

    if underlying > 0:
        upside = ((resistance - underlying) / underlying) * 100
        downside = ((underlying - support) / underlying) * 100
        print()
        print(f"Price Analysis:")
        print(f"  Upside to Resistance: {upside:.2f}%")
        print(f"  Downside to Support: {downside:.2f}%")

    client.close()


def show_strikes_near_atm(symbol: str = "RELIANCE"):
    """Show option data for strikes near ATM."""
    print("\n" + "=" * 60)
    print(f"Strikes Near ATM for {symbol}")
    print("=" * 60)

    client = NSEIndiaClient()

    chain = client.get_near_month_option_chain(symbol)
    if not chain:
        print(f"No option chain available for {symbol}")
        client.close()
        return

    print(f"\nUnderlying: {chain.underlying_value:.2f}")
    print(f"ATM: {chain.atm_strike:.2f}")
    print()

    strikes = chain.get_strikes_near_atm(num_strikes=5)

    print("| Strike  | CE OI      | CE LTP  | CE IV   | PE LTP  | PE IV   | PE OI      |")
    print("|---------|------------|---------|---------|---------|---------|------------|")

    for strike in strikes:
        ce_oi = strike.ce.open_interest if strike.ce else 0
        ce_ltp = strike.ce.last_price if strike.ce else 0
        ce_iv = strike.ce.implied_volatility if strike.ce else 0
        pe_ltp = strike.pe.last_price if strike.pe else 0
        pe_iv = strike.pe.implied_volatility if strike.pe else 0
        pe_oi = strike.pe.open_interest if strike.pe else 0

        # Highlight ATM strike
        atm_marker = " *" if strike.strike_price == chain.atm_strike else ""
        print(f"| {strike.strike_price:>7.2f}{atm_marker:2} | {ce_oi:>10,} | {ce_ltp:>7.2f} | {ce_iv:>6.2f}% | {pe_ltp:>7.2f} | {pe_iv:>6.2f}% | {pe_oi:>10,} |")

    client.close()


def analyze_itm_otm_options(symbol: str = "INFY"):
    """Analyze ITM and OTM options."""
    print("\n" + "=" * 60)
    print(f"ITM/OTM Analysis for {symbol}")
    print("=" * 60)

    client = NSEIndiaClient()

    chain = client.get_near_month_option_chain(symbol)
    if not chain:
        print(f"No option chain available for {symbol}")
        client.close()
        return

    print(f"\nUnderlying: {chain.underlying_value:.2f}")

    # ITM/OTM calls
    itm_calls = chain.get_itm_calls()
    otm_calls = chain.get_otm_calls()
    itm_puts = chain.get_itm_puts()
    otm_puts = chain.get_otm_puts()

    print(f"\nCalls:")
    print(f"  ITM: {len(itm_calls)} strikes, Total OI: {sum(s.ce_oi for s in itm_calls):,}")
    print(f"  OTM: {len(otm_calls)} strikes, Total OI: {sum(s.ce_oi for s in otm_calls):,}")

    print(f"\nPuts:")
    print(f"  ITM: {len(itm_puts)} strikes, Total OI: {sum(s.pe_oi for s in itm_puts):,}")
    print(f"  OTM: {len(otm_puts)} strikes, Total OI: {sum(s.pe_oi for s in otm_puts):,}")

    # Show top OTM options by OI
    print("\nTop 5 OTM Calls by OI:")
    top_otm_calls = sorted(otm_calls, key=lambda s: s.ce_oi, reverse=True)[:5]
    for s in top_otm_calls:
        print(f"  Strike {s.strike_price:.2f}: OI={s.ce_oi:,}, LTP={s.ce.last_price if s.ce else 0:.2f}")

    print("\nTop 5 OTM Puts by OI:")
    top_otm_puts = sorted(otm_puts, key=lambda s: s.pe_oi, reverse=True)[:5]
    for s in top_otm_puts:
        print(f"  Strike {s.strike_price:.2f}: OI={s.pe_oi:,}, LTP={s.pe.last_price if s.pe else 0:.2f}")

    client.close()


def compare_expiry_pcr(symbol: str = "RELIANCE"):
    """Compare PCR across different expiries."""
    print("\n" + "=" * 60)
    print(f"PCR Comparison Across Expiries for {symbol}")
    print("=" * 60)

    client = NSEIndiaClient()

    contract_info = client.get_option_contract_info(symbol)
    if not contract_info.expiry_dates:
        print(f"No options available for {symbol}")
        client.close()
        return

    # Get first 4 expiries
    expiries = contract_info.expiry_dates[:4]

    print("\n| Expiry        | PCR  | CE OI      | PE OI      | Max CE Strike | Max PE Strike |")
    print("|---------------|------|------------|------------|---------------|---------------|")

    for expiry in expiries:
        try:
            chain = client.get_option_chain(symbol, expiry)
            max_ce = chain.max_ce_oi_strike
            max_pe = chain.max_pe_oi_strike

            print(f"| {expiry:13} | {chain.pcr:.2f} | {chain.total_ce_oi:>10,} | {chain.total_pe_oi:>10,} | {max_ce[0]:>13.2f} | {max_pe[0]:>13.2f} |")
        except Exception as e:
            print(f"| {expiry:13} | Error: {str(e)[:40]} |")

    client.close()


if __name__ == "__main__":
    # Run all examples
    fetch_option_contract_info("GAIL")
    fetch_option_chain("GAIL")
    analyze_option_chain("RELIANCE")
    fetch_pcr_data()
    fetch_max_pain_data("NIFTY")
    show_strikes_near_atm("RELIANCE")
    analyze_itm_otm_options("INFY")
    compare_expiry_pcr("TCS")
