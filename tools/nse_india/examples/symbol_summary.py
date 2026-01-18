"""Examples for fetching comprehensive symbol summary from NSE India.

This script demonstrates how to:
- Get comprehensive stock data from multiple APIs
- Access price and trading information
- View performance vs index
- See derivatives data for F&O stocks
"""

from tools.nse_india import NSEIndiaClient


def fetch_symbol_summary(symbol: str = "RELIANCE"):
    """Fetch comprehensive summary data for a symbol."""
    print("=" * 60)
    print(f"Symbol Summary for {symbol}")
    print("=" * 60)

    client = NSEIndiaClient()

    # Get all summary data at once
    data = client.get_symbol_summary_data(symbol)

    # Extract key components
    symbol_name = data.get("symbol_name", {})
    metadata = data.get("metadata", {})
    symbol_data = data.get("symbol_data", {})
    shareholding = data.get("shareholding", {})
    financials = data.get("financials", [])
    yearwise = data.get("yearwise", [])

    # Company info
    print(f"\nCompany: {symbol_name.get('companyName', 'N/A')}")
    print(f"ISIN: {metadata.get('isin', 'N/A')}")
    print(f"F&O Enabled: {metadata.get('isFNOSec', 'No')}")

    # Extract price data
    equity = {}
    if symbol_data and "equityResponse" in symbol_data:
        equity_list = symbol_data.get("equityResponse", [])
        if equity_list:
            equity = equity_list[0]

    meta = equity.get("metaData", {})
    trade_info = equity.get("tradeInfo", {})
    price_info = equity.get("priceInfo", {})
    sec_info = equity.get("secInfo", {})

    # Price info
    print(f"\n--- Price Info ---")
    print(f"Last Price: ₹{meta.get('closePrice', meta.get('lastPrice', 'N/A'))}")
    print(f"Change: {meta.get('change', 0)} ({meta.get('pChange', 0):.2f}%)")
    print(f"Open: ₹{meta.get('open', 'N/A')}")
    print(f"Day High: ₹{meta.get('dayHigh', 'N/A')}")
    print(f"Day Low: ₹{meta.get('dayLow', 'N/A')}")

    # 52-week range
    print(f"\n--- 52 Week Range ---")
    print(f"52W High: ₹{price_info.get('yearHigh', 'N/A')} ({price_info.get('yearHightDt', 'N/A')})")
    print(f"52W Low: ₹{price_info.get('yearLow', 'N/A')} ({price_info.get('yearLowDt', 'N/A')})")

    # Trading info
    print(f"\n--- Trading Info ---")
    print(f"Volume: {trade_info.get('totalTradedVolume', 'N/A'):,}")
    print(f"Value: ₹{trade_info.get('totalTradedValue', 'N/A'):,}")
    print(f"Market Cap: ₹{trade_info.get('totalMarketCap', 'N/A'):,}")
    print(f"Delivery %: {trade_info.get('deliveryToTradedQuantity', 'N/A')}%")

    # Sector info
    print(f"\n--- Sector Info ---")
    print(f"Sector: {sec_info.get('sector', 'N/A')}")
    print(f"Industry: {sec_info.get('basicIndustry', 'N/A')}")
    print(f"P/E Ratio: {sec_info.get('pdSymbolPe', 'N/A')}")
    print(f"Sector P/E: {sec_info.get('pdSectorPe', 'N/A')}")

    # Shareholding
    if shareholding:
        dates = list(shareholding.keys())
        if dates:
            latest = shareholding[dates[0]]
            print(f"\n--- Shareholding (as of {dates[0]}) ---")
            print(f"Promoter: {latest.get('promoter_group', {}).get('value', 'N/A')}%")
            print(f"Public: {latest.get('public', {}).get('value', 'N/A')}%")

    # Performance
    if yearwise:
        perf = yearwise[0] if isinstance(yearwise, list) else yearwise
        print(f"\n--- Performance vs {perf.get('index_name', 'Index')} ---")
        periods = [
            ("1 Day", "yesterday_chng_per", "index_yesterday_chng_per"),
            ("1 Week", "one_week_chng_per", "index_one_week_chng_per"),
            ("1 Month", "one_month_chng_per", "index_one_month_chng_per"),
            ("1 Year", "one_year_chng_per", "index_one_year_chng_per"),
        ]
        for label, stock_key, index_key in periods:
            stock_val = perf.get(stock_key)
            index_val = perf.get(index_key)
            if stock_val is not None:
                print(f"  {label}: Stock {stock_val:+.2f}% | Index {index_val:+.2f}%")

    # Financials
    if financials:
        print(f"\n--- Recent Financials ---")
        for fin in financials[:2]:
            print(f"  {fin.get('to_date_MonYr', 'N/A')}: Revenue ₹{fin.get('totalIncome', 0):,}L, Net Profit ₹{fin.get('netProLossAftTax', 0):,}L, EPS {fin.get('eps', 'N/A')}")

    client.close()


def fetch_individual_apis(symbol: str = "TCS"):
    """Demonstrate individual API calls."""
    print("\n" + "=" * 60)
    print(f"Individual API Calls for {symbol}")
    print("=" * 60)

    client = NSEIndiaClient()

    # Symbol name
    print("\n--- get_symbol_name ---")
    name_data = client.get_symbol_name(symbol)
    print(f"Company: {name_data.get('companyName', 'N/A')}")

    # Metadata
    print("\n--- get_metadata ---")
    meta = client.get_metadata(symbol)
    print(f"ISIN: {meta.get('isin', 'N/A')}")
    print(f"Series: {meta.get('series', 'N/A')}")
    print(f"F&O: {meta.get('isFNOSec', 'N/A')}")

    # Financial status
    print("\n--- get_financial_status ---")
    financials = client.get_financial_status(symbol)
    if financials:
        print(f"Latest quarter: {financials[0].get('to_date_MonYr', 'N/A')}")

    # Corporate actions
    print("\n--- get_corp_actions ---")
    actions = client.get_corp_actions(symbol)
    for action in actions[:3]:
        print(f"  {action.get('subject', 'N/A')} (Ex: {action.get('exDate', 'N/A')})")

    # Board meetings
    print("\n--- get_board_meetings ---")
    meetings = client.get_board_meetings(symbol)
    for meeting in meetings[:2]:
        print(f"  {meeting.get('bm_date', 'N/A')}: {meeting.get('bm_purpose', 'N/A')[:50]}...")

    # Index membership
    print("\n--- get_index_list ---")
    indices = client.get_index_list(symbol)
    print(f"Member of {len(indices)} indices: {', '.join(indices[:5])}")

    client.close()


def fetch_derivatives_data(symbol: str = "RELIANCE"):
    """Fetch derivatives data for F&O stocks."""
    print("\n" + "=" * 60)
    print(f"Derivatives Data for {symbol}")
    print("=" * 60)

    client = NSEIndiaClient()

    # Check if F&O enabled
    meta = client.get_metadata(symbol)
    if meta.get("isFNOSec") != "true":
        print(f"{symbol} is not an F&O stock")
        client.close()
        return

    print(f"{symbol} is an F&O stock\n")

    # Get derivatives filter (expiry dates)
    filter_data = client.get_symbol_derivatives_filter(symbol)
    expiry_dates = filter_data.get("expiryDate", [])
    print(f"Expiry dates: {', '.join(expiry_dates[:3])}")

    # Get derivatives data
    deriv_data = client.get_symbol_derivatives_data(symbol)
    futures = [d for d in deriv_data.get("data", []) if d.get("instrumentType") == "FUTSTK"]
    if futures:
        fut = futures[0]
        print(f"\nNear Month Futures:")
        print(f"  LTP: ₹{fut.get('lastPrice', 'N/A')}")
        print(f"  Change: {fut.get('pchange', 0):.2f}%")
        print(f"  Open Interest: {fut.get('openInterest', 'N/A'):,}")
        print(f"  OI Change: {fut.get('pchangeinOpenInterest', 0):.2f}%")

    # Most active options
    print("\n--- Most Active Calls ---")
    calls = client.get_derivatives_most_active(symbol, "C")
    for opt in calls.get("data", [])[:3]:
        print(f"  {opt.get('contract', 'N/A')}: ₹{opt.get('lastPrice', 0):.2f} ({opt.get('perChange', 0):+.2f}%)")

    print("\n--- Most Active Puts ---")
    puts = client.get_derivatives_most_active(symbol, "P")
    for opt in puts.get("data", [])[:3]:
        print(f"  {opt.get('contract', 'N/A')}: ₹{opt.get('lastPrice', 0):.2f} ({opt.get('perChange', 0):+.2f}%)")

    # Option chain
    if expiry_dates:
        print(f"\n--- Option Chain ({expiry_dates[0]}) ---")
        chain = client.get_option_chain_data(symbol, expiry_dates[0])
        underlying = chain.get("underlyingValue", 0)
        print(f"Underlying: ₹{underlying}")

        # Calculate PCR
        chain_data = chain.get("data", [])
        total_call_oi = sum(d.get("CE", {}).get("openInterest", 0) or 0 for d in chain_data)
        total_put_oi = sum(d.get("PE", {}).get("openInterest", 0) or 0 for d in chain_data)
        pcr = total_put_oi / total_call_oi if total_call_oi > 0 else 0
        print(f"PCR (OI): {pcr:.2f}")
        print(f"Total Call OI: {total_call_oi:,}")
        print(f"Total Put OI: {total_put_oi:,}")

    client.close()


if __name__ == "__main__":
    fetch_symbol_summary("RELIANCE")
    fetch_individual_apis("TCS")
    fetch_derivatives_data("RELIANCE")
