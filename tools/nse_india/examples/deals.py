"""Examples for fetching bulk deals, block deals, and short selling data from NSE India.

This script demonstrates how to:
- Fetch large deals snapshot (bulk, block, short selling)
- Analyze bulk and block deal activity
- Track short selling positions
- Filter deals by symbol or client
"""

from tools.nse_india import NSEIndiaClient


def fetch_large_deals_snapshot():
    """Fetch snapshot of all large deals."""
    print("=" * 60)
    print("Large Deals Snapshot from NSE")
    print("=" * 60)

    client = NSEIndiaClient()

    snapshot = client.get_large_deals_snapshot()

    print(f"Data as on: {snapshot.as_on_date}")
    print(f"Bulk deals: {snapshot.bulk_deals_count}")
    print(f"Block deals: {snapshot.block_deals_count}")
    print(f"Short selling entries: {snapshot.short_deals_count}")
    print()

    # Summary values
    print("--- Summary Values ---")
    print(f"Total Bulk Buy Value: Rs. {snapshot.total_bulk_buy_value / 10_000_000:,.2f} Cr")
    print(f"Total Bulk Sell Value: Rs. {snapshot.total_bulk_sell_value / 10_000_000:,.2f} Cr")
    print(f"Total Block Buy Value: Rs. {snapshot.total_block_buy_value / 10_000_000:,.2f} Cr")
    print(f"Total Block Sell Value: Rs. {snapshot.total_block_sell_value / 10_000_000:,.2f} Cr")
    print()

    # Unique symbols
    symbols = snapshot.get_unique_symbols()
    print(f"Unique symbols with deals: {len(symbols)}")
    print()

    client.close()
    return snapshot


def show_bulk_deals():
    """Show bulk deals summary."""
    print("\n" + "=" * 60)
    print("Bulk Deals")
    print("=" * 60)

    client = NSEIndiaClient()

    bulk_deals = client.get_bulk_deals()

    print(f"\nTotal Bulk Deals: {len(bulk_deals)}")
    print("\n--- Top Bulk Buys ---")

    buys = client.get_bulk_buys(limit=5)
    print(f"{'Symbol':<12} {'Client':<30} {'Qty':>12} {'Price':>10} {'Value (Cr)':>12}")
    print("-" * 80)
    for deal in buys:
        print(
            f"{deal.symbol:<12} {deal.client_name[:28]:<30} {deal.quantity:>12,} "
            f"{deal.weighted_avg_price:>10.2f} {deal.trade_value_cr:>12.2f}"
        )

    print("\n--- Top Bulk Sells ---")
    sells = client.get_bulk_sells(limit=5)
    print(f"{'Symbol':<12} {'Client':<30} {'Qty':>12} {'Price':>10} {'Value (Cr)':>12}")
    print("-" * 80)
    for deal in sells:
        print(
            f"{deal.symbol:<12} {deal.client_name[:28]:<30} {deal.quantity:>12,} "
            f"{deal.weighted_avg_price:>10.2f} {deal.trade_value_cr:>12.2f}"
        )

    client.close()


def show_block_deals():
    """Show block deals summary."""
    print("\n" + "=" * 60)
    print("Block Deals")
    print("=" * 60)

    client = NSEIndiaClient()

    block_deals = client.get_block_deals()

    print(f"\nTotal Block Deals: {len(block_deals)}")

    if block_deals:
        print("\n--- Block Deal Details ---")
        print(f"{'Symbol':<12} {'Client':<30} {'Type':<6} {'Qty':>12} {'Price':>10} {'Value (Cr)':>12}")
        print("-" * 90)
        for deal in sorted(block_deals, key=lambda d: d.trade_value, reverse=True)[:10]:
            print(
                f"{deal.symbol:<12} {deal.client_name[:28]:<30} {deal.deal_type:<6} "
                f"{deal.quantity:>12,} {deal.weighted_avg_price:>10.2f} {deal.trade_value_cr:>12.2f}"
            )
    else:
        print("No block deals today")

    client.close()


def show_short_selling():
    """Show short selling data."""
    print("\n" + "=" * 60)
    print("Short Selling Data")
    print("=" * 60)

    client = NSEIndiaClient()

    short_data = client.get_short_selling()

    print(f"\nTotal Short Selling Entries: {len(short_data)}")

    if short_data:
        print("\n--- Top Shorted Stocks ---")
        top_shorted = client.get_top_shorted_stocks(limit=10)
        print(f"{'Symbol':<15} {'Company':<35} {'Quantity':>15}")
        print("-" * 70)
        for ss in top_shorted:
            print(f"{ss.symbol:<15} {ss.company_name[:33]:<35} {ss.quantity:>15,}")
    else:
        print("No short selling data today")

    client.close()


def filter_deals_by_symbol(symbol: str = "RELIANCE"):
    """Filter deals for a specific symbol."""
    print("\n" + "=" * 60)
    print(f"Deals for {symbol}")
    print("=" * 60)

    client = NSEIndiaClient()

    bulk = client.get_bulk_deals(symbol=symbol)
    block = client.get_block_deals(symbol=symbol)
    short = client.get_short_selling(symbol=symbol)

    print(f"\nBulk Deals: {len(bulk)}")
    for deal in bulk:
        action = "bought" if deal.is_buy else "sold"
        print(
            f"  {deal.client_name} {action} {deal.quantity:,} @ Rs. {deal.weighted_avg_price:.2f} "
            f"(Rs. {deal.trade_value_cr:.2f} Cr)"
        )

    print(f"\nBlock Deals: {len(block)}")
    for deal in block:
        action = "bought" if deal.is_buy else "sold"
        print(
            f"  {deal.client_name} {action} {deal.quantity:,} @ Rs. {deal.weighted_avg_price:.2f} "
            f"(Rs. {deal.trade_value_cr:.2f} Cr)"
        )

    print(f"\nShort Selling: {len(short)}")
    for ss in short:
        print(f"  {ss.quantity:,} shares shorted")

    client.close()


def track_client_activity(client_name: str = "GOLDMAN"):
    """Track deals by a specific client."""
    print("\n" + "=" * 60)
    print(f"Deals by Client: '{client_name}'")
    print("=" * 60)

    client = NSEIndiaClient()

    deals = client.get_deals_by_client(client_name)

    print(f"\nBulk Deals: {len(deals['bulk_deals'])}")
    for deal in deals["bulk_deals"]:
        action = "BUY" if deal.is_buy else "SELL"
        print(
            f"  [{action}] {deal.symbol}: {deal.quantity:,} @ Rs. {deal.weighted_avg_price:.2f} "
            f"(Rs. {deal.trade_value_cr:.2f} Cr)"
        )

    print(f"\nBlock Deals: {len(deals['block_deals'])}")
    for deal in deals["block_deals"]:
        action = "BUY" if deal.is_buy else "SELL"
        print(
            f"  [{action}] {deal.symbol}: {deal.quantity:,} @ Rs. {deal.weighted_avg_price:.2f} "
            f"(Rs. {deal.trade_value_cr:.2f} Cr)"
        )

    client.close()


def analyze_deal_flow():
    """Analyze overall deal flow for the day."""
    print("\n" + "=" * 60)
    print("Deal Flow Analysis")
    print("=" * 60)

    client = NSEIndiaClient()

    snapshot = client.get_large_deals_snapshot()

    # Bulk deals analysis
    bulk_buy_value = snapshot.total_bulk_buy_value
    bulk_sell_value = snapshot.total_bulk_sell_value
    bulk_net = bulk_buy_value - bulk_sell_value

    print("\n--- Bulk Deals Flow ---")
    print(f"Buy Value:  Rs. {bulk_buy_value / 10_000_000:>12,.2f} Cr")
    print(f"Sell Value: Rs. {bulk_sell_value / 10_000_000:>12,.2f} Cr")
    print(f"Net Flow:   Rs. {bulk_net / 10_000_000:>12,.2f} Cr {'(Bullish)' if bulk_net > 0 else '(Bearish)'}")

    # Block deals analysis
    block_buy_value = snapshot.total_block_buy_value
    block_sell_value = snapshot.total_block_sell_value
    block_net = block_buy_value - block_sell_value

    print("\n--- Block Deals Flow ---")
    print(f"Buy Value:  Rs. {block_buy_value / 10_000_000:>12,.2f} Cr")
    print(f"Sell Value: Rs. {block_sell_value / 10_000_000:>12,.2f} Cr")
    print(f"Net Flow:   Rs. {block_net / 10_000_000:>12,.2f} Cr {'(Bullish)' if block_net > 0 else '(Bearish)'}")

    # Overall
    total_buy = bulk_buy_value + block_buy_value
    total_sell = bulk_sell_value + block_sell_value
    total_net = total_buy - total_sell

    print("\n--- Combined Flow ---")
    print(f"Total Buy:  Rs. {total_buy / 10_000_000:>12,.2f} Cr")
    print(f"Total Sell: Rs. {total_sell / 10_000_000:>12,.2f} Cr")
    print(f"Net Flow:   Rs. {total_net / 10_000_000:>12,.2f} Cr {'(Bullish)' if total_net > 0 else '(Bearish)'}")

    # Most active symbols
    print("\n--- Most Active Symbols (by deal count) ---")
    symbol_count: dict[str, int] = {}
    for deal in snapshot.bulk_deals:
        symbol_count[deal.symbol] = symbol_count.get(deal.symbol, 0) + 1
    for deal in snapshot.block_deals:
        symbol_count[deal.symbol] = symbol_count.get(deal.symbol, 0) + 1

    sorted_symbols = sorted(symbol_count.items(), key=lambda x: x[1], reverse=True)[:10]
    for symbol, count in sorted_symbols:
        print(f"  {symbol}: {count} deals")

    client.close()


if __name__ == "__main__":
    fetch_large_deals_snapshot()
    show_bulk_deals()
    show_block_deals()
    show_short_selling()
    # filter_deals_by_symbol("RELIANCE")  # Uncomment to test
    # track_client_activity("GOLDMAN")    # Uncomment to test
    analyze_deal_flow()
