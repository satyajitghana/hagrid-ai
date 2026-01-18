"""Examples for using the Insider Trading (PIT) APIs.

This script demonstrates how to:
- Fetch insider trading plans
- Get insider transactions for a symbol
- Filter by transaction type (buy/sell)
- Filter by person category (promoter/director)
- Analyze insider activity patterns
"""

from tools.nse_india.client import NSEIndiaClient


def fetch_insider_trading_plans():
    """Fetch all recent insider trading plans."""
    print("=" * 60)
    print("Insider Trading Plans")
    print("=" * 60)

    client = NSEIndiaClient()

    plans = client.get_insider_trading_plans()
    print(f"Found {len(plans)} trading plans\n")

    for plan in plans[:10]:
        print(f"Symbol: {plan.symbol}")
        print(f"Company: {plan.company_name}")
        print(f"Submission Date: {plan.submission_date}")
        print(f"iXBRL URL: {plan.ixbrl_url}")
        print("-" * 40)

    client.close()


def fetch_insider_transactions(symbol: str = "RELIANCE"):
    """Fetch insider transactions for a specific symbol."""
    print("\n" + "=" * 60)
    print(f"Insider Transactions for {symbol}")
    print("=" * 60)

    client = NSEIndiaClient()

    response = client.get_insider_transactions(symbol)
    print(f"Total transactions: {response.total_transactions}")
    print(f"Buy transactions: {len(response.buy_transactions)}")
    print(f"Sell transactions: {len(response.sell_transactions)}")
    print(f"Acquirer names: {', '.join(response.acquirer_names[:5])}...")
    print()

    # Show recent transactions
    print("Recent Transactions:")
    print("-" * 60)
    for txn in response.transactions[:5]:
        print(f"Date: {txn.disclosure_date}")
        print(f"Acquirer: {txn.acquirer_name}")
        print(f"Category: {txn.person_category}")
        print(f"Type: {txn.transaction_type}")
        print(f"Shares: {txn.securities_acquired}")
        print(f"Value: ₹{txn.security_value}")
        print(f"Mode: {txn.acquisition_mode}")
        print(f"Before: {txn.before_percentage}% → After: {txn.after_percentage}%")
        print("-" * 40)

    client.close()


def analyze_insider_activity(symbol: str = "TCS"):
    """Analyze insider buying and selling activity."""
    print("\n" + "=" * 60)
    print(f"Insider Activity Analysis for {symbol}")
    print("=" * 60)

    client = NSEIndiaClient()

    response = client.get_insider_transactions(symbol)

    if not response.transactions:
        print(f"No insider transactions found for {symbol}")
        client.close()
        return

    # Calculate totals
    total_buy_value = 0.0
    total_sell_value = 0.0
    total_buy_shares = 0
    total_sell_shares = 0

    for txn in response.transactions:
        if txn.is_buy:
            total_buy_value += txn.value_amount
            total_buy_shares += txn.shares_count
        else:
            total_sell_value += txn.value_amount
            total_sell_shares += txn.shares_count

    print(f"\nSummary:")
    print(f"  Total Buy Value: ₹{total_buy_value:,.0f}")
    print(f"  Total Buy Shares: {total_buy_shares:,}")
    print(f"  Total Sell Value: ₹{total_sell_value:,.0f}")
    print(f"  Total Sell Shares: {total_sell_shares:,}")

    # Net position
    net_value = total_buy_value - total_sell_value
    net_shares = total_buy_shares - total_sell_shares
    sentiment = "Bullish" if net_value > 0 else "Bearish" if net_value < 0 else "Neutral"

    print(f"\n  Net Value: ₹{net_value:,.0f}")
    print(f"  Net Shares: {net_shares:,}")
    print(f"  Insider Sentiment: {sentiment}")

    # By category
    print("\nBy Person Category:")
    categories = {}
    for txn in response.transactions:
        cat = txn.person_category
        if cat not in categories:
            categories[cat] = {"buys": 0, "sells": 0}
        if txn.is_buy:
            categories[cat]["buys"] += txn.shares_count
        else:
            categories[cat]["sells"] += txn.shares_count

    for cat, data in sorted(categories.items()):
        print(f"  {cat}: Buys={data['buys']:,}, Sells={data['sells']:,}")

    client.close()


def fetch_promoter_transactions(symbol: str = "RELIANCE"):
    """Fetch only promoter transactions."""
    print("\n" + "=" * 60)
    print(f"Promoter Transactions for {symbol}")
    print("=" * 60)

    client = NSEIndiaClient()

    transactions = client.get_promoter_transactions(symbol, limit=10)
    print(f"Found {len(transactions)} promoter transactions\n")

    for txn in transactions:
        emoji = "🟢" if txn.is_buy else "🔴"
        print(f"{emoji} {txn.disclosure_date.strftime('%d-%b-%Y') if txn.disclosure_date else 'N/A'}")
        print(f"   {txn.acquirer_name}")
        print(f"   {txn.transaction_type}: {txn.securities_acquired} shares @ ₹{txn.security_value}")
        print(f"   Holding: {txn.before_percentage}% → {txn.after_percentage}%")
        print()

    client.close()


def compare_insider_activity():
    """Compare insider activity across multiple stocks."""
    print("\n" + "=" * 60)
    print("Insider Activity Comparison")
    print("=" * 60)

    client = NSEIndiaClient()
    symbols = ["RELIANCE", "TCS", "INFY", "HDFCBANK", "ICICIBANK"]

    print("\n| Symbol | Total Txns | Buys | Sells | Net Sentiment |")
    print("|--------|------------|------|-------|---------------|")

    for symbol in symbols:
        try:
            response = client.get_insider_transactions(symbol)
            buys = len(response.buy_transactions)
            sells = len(response.sell_transactions)
            total = response.total_transactions

            # Calculate net value sentiment
            buy_value = sum(t.value_amount for t in response.buy_transactions)
            sell_value = sum(t.value_amount for t in response.sell_transactions)
            sentiment = "Bullish" if buy_value > sell_value else "Bearish" if sell_value > buy_value else "Neutral"

            print(f"| {symbol:6} | {total:10} | {buys:4} | {sells:5} | {sentiment:13} |")
        except Exception as e:
            print(f"| {symbol:6} | Error: {str(e)[:30]} |")

    client.close()


def fetch_recent_buys_and_sells(symbol: str = "BAJFINANCE"):
    """Fetch recent buy and sell transactions separately."""
    print("\n" + "=" * 60)
    print(f"Recent Insider Activity for {symbol}")
    print("=" * 60)

    client = NSEIndiaClient()

    # Get recent buys
    buys = client.get_recent_insider_buys(symbol, limit=5)
    print(f"\nRecent Buys ({len(buys)}):")
    for txn in buys:
        date_str = txn.disclosure_date.strftime("%d-%b-%Y") if txn.disclosure_date else "N/A"
        print(f"  🟢 {date_str}: {txn.acquirer_name} bought {txn.securities_acquired} shares")

    # Get recent sells
    sells = client.get_recent_insider_sells(symbol, limit=5)
    print(f"\nRecent Sells ({len(sells)}):")
    for txn in sells:
        date_str = txn.disclosure_date.strftime("%d-%b-%Y") if txn.disclosure_date else "N/A"
        print(f"  🔴 {date_str}: {txn.acquirer_name} sold {txn.securities_acquired} shares")

    client.close()


if __name__ == "__main__":
    # Run all examples
    fetch_insider_trading_plans()
    fetch_insider_transactions("MAANALU")
    analyze_insider_activity("TCS")
    fetch_promoter_transactions("RELIANCE")
    compare_insider_activity()
    fetch_recent_buys_and_sells("BAJFINANCE")
