"""Examples for search and lookup functionality from Yahoo Finance.

This script demonstrates how to:
- Search for tickers by company name or keyword
- Lookup securities by type (stocks, ETFs, mutual funds, etc.)
- Find related news from search results
- Navigate from company name to ticker symbol
"""

from tools.yahoo_finance import YFinanceClient


def search_by_company_name(query: str = "Apple"):
    """Search for a company by name."""
    print("=" * 60)
    print(f"Search Results for: '{query}'")
    print("=" * 60)

    client = YFinanceClient()
    results = client.search(query, max_results=10)

    print(f"\nQuery: {results.query}")
    print(f"Quotes found: {len(results.quotes)}")
    print(f"News found: {len(results.news)}")

    if not results.quotes:
        print("No quote results found")
        return

    print("\n--- Quote Results ---")
    print("| Symbol | Name | Type | Exchange |")
    print("|--------|------|------|----------|")

    for quote in results.quotes:
        symbol = quote.get('symbol', 'N/A')
        name = quote.get('shortname', quote.get('longname', 'N/A'))
        if name and len(name) > 25:
            name = name[:22] + "..."
        qtype = quote.get('quoteType', quote.get('typeDisp', 'N/A'))
        exchange = quote.get('exchange', 'N/A')

        print(f"| {symbol:<6} | {name:<25} | {qtype:<8} | {exchange:<8} |")


def search_with_news(query: str = "Tesla"):
    """Search and get related news."""
    print("\n" + "=" * 60)
    print(f"Search with News for: '{query}'")
    print("=" * 60)

    client = YFinanceClient()
    results = client.search(query, max_results=5, news_count=10)

    print(f"\nQuotes: {len(results.quotes)}")
    print(f"News: {len(results.news)}")

    if results.news:
        print("\n--- Related News ---")
        for news in results.news[:10]:
            title = news.get('title', 'N/A')
            if len(title) > 60:
                title = title[:57] + "..."
            publisher = news.get('publisher', 'N/A')
            print(f"  [{publisher}] {title}")


def search_international_companies():
    """Search for international companies."""
    print("\n" + "=" * 60)
    print("International Company Search")
    print("=" * 60)

    client = YFinanceClient()

    searches = [
        ("Reliance India", "India"),
        ("Toyota", "Japan"),
        ("Samsung", "Korea"),
        ("Volkswagen", "Germany"),
        ("HSBC", "UK"),
    ]

    for query, country in searches:
        print(f"\n--- {country}: '{query}' ---")
        results = client.search(query, max_results=3)

        for quote in results.quotes[:3]:
            symbol = quote.get('symbol', 'N/A')
            name = quote.get('shortname', 'N/A')
            exchange = quote.get('exchange', 'N/A')
            print(f"  {symbol}: {name} ({exchange})")


def lookup_all_types(query: str = "AAPL"):
    """Lookup a symbol across all security types."""
    print("\n" + "=" * 60)
    print(f"Lookup All Types for: '{query}'")
    print("=" * 60)

    client = YFinanceClient()
    results = client.lookup(query, count=5)

    print(f"\nQuery: {results.query}")

    categories = [
        ("all", "All Results"),
        ("stocks", "Stocks"),
        ("etfs", "ETFs"),
        ("mutual_funds", "Mutual Funds"),
        ("indices", "Indices"),
        ("futures", "Futures"),
        ("currencies", "Currencies"),
        ("cryptocurrencies", "Cryptocurrencies"),
    ]

    for attr, label in categories:
        items = getattr(results, attr, [])
        if items:
            print(f"\n--- {label} ({len(items)}) ---")
            for item in items[:5]:
                symbol = item.get('symbol', 'N/A')
                name = item.get('shortName', item.get('name', 'N/A'))
                if name and len(name) > 30:
                    name = name[:27] + "..."
                print(f"  {symbol}: {name}")


def lookup_stocks(query: str = "tech"):
    """Lookup stocks matching a query."""
    print("\n" + "=" * 60)
    print(f"Stock Lookup for: '{query}'")
    print("=" * 60)

    client = YFinanceClient()
    results = client.lookup(query, count=10)

    stocks = results.stocks
    if not stocks:
        print("No stocks found")
        return

    print(f"\nFound {len(stocks)} stocks")

    print("\n| Symbol | Name | Exchange |")
    print("|--------|------|----------|")

    for stock in stocks[:15]:
        symbol = stock.get('symbol', 'N/A')
        name = stock.get('shortName', stock.get('name', 'N/A'))
        if name and len(name) > 30:
            name = name[:27] + "..."
        exchange = stock.get('exchange', 'N/A')

        print(f"| {symbol:<8} | {name:<30} | {exchange:<10} |")


def lookup_etfs(query: str = "S&P"):
    """Lookup ETFs matching a query."""
    print("\n" + "=" * 60)
    print(f"ETF Lookup for: '{query}'")
    print("=" * 60)

    client = YFinanceClient()
    results = client.lookup(query, count=10)

    etfs = results.etfs
    if not etfs:
        print("No ETFs found")
        return

    print(f"\nFound {len(etfs)} ETFs")

    print("\n| Symbol | Name |")
    print("|--------|------|")

    for etf in etfs[:10]:
        symbol = etf.get('symbol', 'N/A')
        name = etf.get('shortName', etf.get('name', 'N/A'))
        if name and len(name) > 40:
            name = name[:37] + "..."

        print(f"| {symbol:<8} | {name:<40} |")


def lookup_mutual_funds(query: str = "Vanguard"):
    """Lookup mutual funds matching a query."""
    print("\n" + "=" * 60)
    print(f"Mutual Fund Lookup for: '{query}'")
    print("=" * 60)

    client = YFinanceClient()
    results = client.lookup(query, count=10)

    funds = results.mutual_funds
    if not funds:
        print("No mutual funds found")
        return

    print(f"\nFound {len(funds)} mutual funds")

    print("\n| Symbol | Name |")
    print("|--------|------|")

    for fund in funds[:10]:
        symbol = fund.get('symbol', 'N/A')
        name = fund.get('shortName', fund.get('name', 'N/A'))
        if name and len(name) > 45:
            name = name[:42] + "..."

        print(f"| {symbol:<10} | {name:<45} |")


def lookup_indices(query: str = "Dow"):
    """Lookup indices matching a query."""
    print("\n" + "=" * 60)
    print(f"Index Lookup for: '{query}'")
    print("=" * 60)

    client = YFinanceClient()
    results = client.lookup(query, count=10)

    indices = results.indices
    if not indices:
        print("No indices found")
        return

    print(f"\nFound {len(indices)} indices")

    print("\n| Symbol | Name |")
    print("|--------|------|")

    for idx in indices[:10]:
        symbol = idx.get('symbol', 'N/A')
        name = idx.get('shortName', idx.get('name', 'N/A'))
        if name and len(name) > 40:
            name = name[:37] + "..."

        print(f"| {symbol:<12} | {name:<40} |")


def lookup_crypto(query: str = "Bitcoin"):
    """Lookup cryptocurrencies matching a query."""
    print("\n" + "=" * 60)
    print(f"Crypto Lookup for: '{query}'")
    print("=" * 60)

    client = YFinanceClient()
    results = client.lookup(query, count=10)

    cryptos = results.cryptocurrencies
    if not cryptos:
        print("No cryptocurrencies found")
        return

    print(f"\nFound {len(cryptos)} cryptocurrencies")

    print("\n| Symbol | Name |")
    print("|--------|------|")

    for crypto in cryptos[:10]:
        symbol = crypto.get('symbol', 'N/A')
        name = crypto.get('shortName', crypto.get('name', 'N/A'))
        if name and len(name) > 35:
            name = name[:32] + "..."

        print(f"| {symbol:<12} | {name:<35} |")


def lookup_currencies(query: str = "EUR"):
    """Lookup currencies matching a query."""
    print("\n" + "=" * 60)
    print(f"Currency Lookup for: '{query}'")
    print("=" * 60)

    client = YFinanceClient()
    results = client.lookup(query, count=10)

    currencies = results.currencies
    if not currencies:
        print("No currencies found")
        return

    print(f"\nFound {len(currencies)} currencies")

    print("\n| Symbol | Name |")
    print("|--------|------|")

    for curr in currencies[:10]:
        symbol = curr.get('symbol', 'N/A')
        name = curr.get('shortName', curr.get('name', 'N/A'))
        if name and len(name) > 35:
            name = name[:32] + "..."

        print(f"| {symbol:<12} | {name:<35} |")


def find_ticker_by_name():
    """Find ticker symbols for company names."""
    print("\n" + "=" * 60)
    print("Find Ticker by Company Name")
    print("=" * 60)

    client = YFinanceClient()

    companies = [
        "Microsoft",
        "Alphabet",
        "Berkshire Hathaway",
        "Johnson & Johnson",
        "Tata Motors",
    ]

    print("\n| Company | Symbol | Exchange |")
    print("|---------|--------|----------|")

    for company in companies:
        results = client.search(company, max_results=1)

        if results.quotes:
            quote = results.quotes[0]
            symbol = quote.get('symbol', 'N/A')
            exchange = quote.get('exchange', 'N/A')
        else:
            symbol = "Not found"
            exchange = "-"

        print(f"| {company:<20} | {symbol:<8} | {exchange:<10} |")


if __name__ == "__main__":
    search_by_company_name("Apple")
    search_with_news("Tesla")
    search_international_companies()
    lookup_all_types("AAPL")
    lookup_stocks("tech")
    lookup_etfs("S&P")
    lookup_mutual_funds("Vanguard")
    lookup_indices("Dow")
    lookup_crypto("Bitcoin")
    lookup_currencies("EUR")
    find_ticker_by_name()
