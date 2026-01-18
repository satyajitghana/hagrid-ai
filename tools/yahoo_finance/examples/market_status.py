"""Examples for market status from Yahoo Finance.

This script demonstrates how to:
- Fetch market status for different regions
- Get market summary information
- Track market open/close times
- Compare multiple markets
"""

from tools.yahoo_finance import YFinanceClient


def fetch_us_market_status():
    """Fetch US market status."""
    print("=" * 60)
    print("US Market Status")
    print("=" * 60)

    client = YFinanceClient()
    ms = client.get_market_status("US")

    print(f"\nMarket: {ms.market}")

    print("\n--- Status ---")
    if ms.status:
        for key, value in ms.status.items():
            print(f"{key}: {value}")
    else:
        print("No status data available")

    print("\n--- Summary ---")
    if ms.summary:
        for key, value in list(ms.summary.items())[:10]:
            if isinstance(value, dict):
                print(f"{key}:")
                for k, v in list(value.items())[:5]:
                    print(f"  {k}: {v}")
            else:
                print(f"{key}: {value}")
    else:
        print("No summary data available")


def fetch_asia_market_status():
    """Fetch Asian market status."""
    print("\n" + "=" * 60)
    print("Asian Market Status")
    print("=" * 60)

    client = YFinanceClient()
    ms = client.get_market_status("ASIA")

    print(f"\nMarket: {ms.market}")

    print("\n--- Status ---")
    if ms.status:
        for key, value in ms.status.items():
            print(f"{key}: {value}")
    else:
        print("No status data available")


def fetch_europe_market_status():
    """Fetch European market status."""
    print("\n" + "=" * 60)
    print("European Market Status")
    print("=" * 60)

    client = YFinanceClient()
    ms = client.get_market_status("EUROPE")

    print(f"\nMarket: {ms.market}")

    print("\n--- Status ---")
    if ms.status:
        for key, value in ms.status.items():
            print(f"{key}: {value}")
    else:
        print("No status data available")


def fetch_gb_market_status():
    """Fetch Great Britain market status."""
    print("\n" + "=" * 60)
    print("Great Britain Market Status")
    print("=" * 60)

    client = YFinanceClient()
    ms = client.get_market_status("GB")

    print(f"\nMarket: {ms.market}")

    print("\n--- Status ---")
    if ms.status:
        for key, value in ms.status.items():
            print(f"{key}: {value}")


def compare_all_markets():
    """Compare status of all available markets."""
    print("\n" + "=" * 60)
    print("Global Markets Status Comparison")
    print("=" * 60)

    client = YFinanceClient()

    markets = ["US", "GB", "ASIA", "EUROPE"]

    print("\n| Market | Status |")
    print("|--------|--------|")

    for market in markets:
        try:
            ms = client.get_market_status(market)
            # Try to extract status string
            if ms.status:
                status_str = str(list(ms.status.values())[0]) if ms.status else "Unknown"
                if len(status_str) > 20:
                    status_str = status_str[:17] + "..."
            else:
                status_str = "No data"
            print(f"| {market:<6} | {status_str:<20} |")
        except Exception as e:
            print(f"| {market:<6} | Error: {str(e)[:15]} |")


def fetch_commodity_markets():
    """Fetch commodity markets status."""
    print("\n" + "=" * 60)
    print("Commodity Markets Status")
    print("=" * 60)

    client = YFinanceClient()
    ms = client.get_market_status("COMMODITIES")

    print(f"\nMarket: {ms.market}")

    print("\n--- Summary ---")
    if ms.summary:
        # Summary often contains market quotes
        for key, value in list(ms.summary.items())[:15]:
            if isinstance(value, dict):
                name = value.get('shortName', key)
                price = value.get('regularMarketPrice', 'N/A')
                change = value.get('regularMarketChangePercent', 0)
                print(f"{name}: {price} ({change:+.2f}%)" if isinstance(change, (int, float)) else f"{name}: {price}")
            else:
                print(f"{key}: {value}")


def fetch_currency_markets():
    """Fetch currency markets status."""
    print("\n" + "=" * 60)
    print("Currency Markets Status")
    print("=" * 60)

    client = YFinanceClient()
    ms = client.get_market_status("CURRENCIES")

    print(f"\nMarket: {ms.market}")

    print("\n--- Status ---")
    if ms.status:
        for key, value in ms.status.items():
            print(f"{key}: {value}")


def fetch_crypto_markets():
    """Fetch cryptocurrency markets status."""
    print("\n" + "=" * 60)
    print("Cryptocurrency Markets Status")
    print("=" * 60)

    client = YFinanceClient()
    ms = client.get_market_status("CRYPTOCURRENCIES")

    print(f"\nMarket: {ms.market}")

    print("\n--- Status ---")
    if ms.status:
        for key, value in ms.status.items():
            print(f"{key}: {value}")


def fetch_rates_markets():
    """Fetch rates/bonds markets status."""
    print("\n" + "=" * 60)
    print("Rates/Bonds Markets Status")
    print("=" * 60)

    client = YFinanceClient()
    ms = client.get_market_status("RATES")

    print(f"\nMarket: {ms.market}")

    print("\n--- Status ---")
    if ms.status:
        for key, value in ms.status.items():
            print(f"{key}: {value}")


def print_available_markets():
    """Print all available market codes."""
    print("\n" + "=" * 60)
    print("Available Market Codes")
    print("=" * 60)

    markets = [
        ("US", "United States equity markets"),
        ("GB", "Great Britain equity markets"),
        ("ASIA", "Asian equity markets"),
        ("EUROPE", "European equity markets"),
        ("RATES", "Bond and interest rate markets"),
        ("COMMODITIES", "Commodity markets (gold, oil, etc.)"),
        ("CURRENCIES", "Foreign exchange markets"),
        ("CRYPTOCURRENCIES", "Cryptocurrency markets"),
    ]

    print("\n| Code | Description |")
    print("|------|-------------|")

    for code, desc in markets:
        print(f"| {code:<15} | {desc:<35} |")


if __name__ == "__main__":
    print_available_markets()
    fetch_us_market_status()
    fetch_asia_market_status()
    fetch_europe_market_status()
    fetch_gb_market_status()
    compare_all_markets()
    fetch_commodity_markets()
    fetch_currency_markets()
    fetch_crypto_markets()
    fetch_rates_markets()
