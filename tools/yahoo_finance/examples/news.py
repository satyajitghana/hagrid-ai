"""Examples for fetching news from Yahoo Finance.

This script demonstrates how to:
- Fetch latest news for a ticker
- Get news across multiple stocks
- Analyze news sources
- Filter news by recency
"""

from datetime import datetime, timedelta
from tools.yahoo_finance import YFinanceClient


def extract_article_data(article: dict) -> dict:
    """Extract article data handling both old and new API structures.

    The yfinance API sometimes returns nested data under 'content' key.
    This helper normalizes the data structure.
    """
    # Check if data is nested under 'content'
    if 'content' in article and isinstance(article['content'], dict):
        content = article['content']
        return {
            'title': content.get('title', 'No Title'),
            'publisher': content.get('provider', {}).get('displayName', 'Unknown') if isinstance(content.get('provider'), dict) else 'Unknown',
            'link': content.get('canonicalUrl', {}).get('url', '#') if isinstance(content.get('canonicalUrl'), dict) else '#',
            'pubDate': content.get('pubDate', ''),
            'thumbnail': content.get('thumbnail', {}),
            'summary': content.get('summary', ''),
        }
    else:
        # Old structure - data is at top level
        return {
            'title': article.get('title', 'No Title'),
            'publisher': article.get('publisher', 'Unknown'),
            'link': article.get('link', '#'),
            'providerPublishTime': article.get('providerPublishTime', 0),
            'thumbnail': article.get('thumbnail', {}),
            'relatedTickers': article.get('relatedTickers', []),
        }


def parse_pub_date(article_data: dict) -> datetime | None:
    """Parse publication date from article data."""
    # Try ISO format date string first (new format)
    pub_date = article_data.get('pubDate', '')
    if pub_date:
        try:
            # Handle ISO format like '2026-01-18T16:05:56Z'
            return datetime.fromisoformat(pub_date.replace('Z', '+00:00')).replace(tzinfo=None)
        except (ValueError, AttributeError):
            pass

    # Try timestamp (old format)
    pub_time = article_data.get('providerPublishTime', 0)
    if pub_time:
        try:
            return datetime.fromtimestamp(pub_time)
        except (ValueError, OSError):
            pass

    return None


def fetch_ticker_news(symbol: str = "AAPL"):
    """Fetch latest news for a ticker."""
    print("=" * 60)
    print(f"Latest News for {symbol}")
    print("=" * 60)

    client = YFinanceClient()
    news = client.get_news(symbol)

    if not news:
        print("\nNo news available")
        return

    print(f"\nTotal news items: {len(news)}")
    print()

    for i, article in enumerate(news[:10], 1):
        data = extract_article_data(article)
        title = data['title']
        publisher = data['publisher']
        link = data['link']

        # Parse publication time
        dt = parse_pub_date(data)
        if dt:
            time_str = dt.strftime('%Y-%m-%d %H:%M')
            time_ago = datetime.now() - dt
            if time_ago.days > 0:
                ago_str = f"{time_ago.days}d ago"
            elif time_ago.seconds > 3600:
                ago_str = f"{time_ago.seconds // 3600}h ago"
            else:
                ago_str = f"{time_ago.seconds // 60}m ago"
        else:
            time_str = "Unknown"
            ago_str = ""

        print(f"{i}. {title}")
        print(f"   Publisher: {publisher} | {time_str} ({ago_str})")
        print(f"   Link: {link[:80]}...")
        print()


def fetch_news_multiple_stocks():
    """Fetch news across multiple stocks."""
    print("\n" + "=" * 60)
    print("News Across Major Tech Stocks")
    print("=" * 60)

    client = YFinanceClient()
    symbols = ["AAPL", "MSFT", "GOOGL", "AMZN", "META"]

    for symbol in symbols:
        news = client.get_news(symbol)

        print(f"\n--- {symbol} ({len(news) if news else 0} articles) ---")

        if news:
            # Show top 3 for each
            for article in news[:3]:
                data = extract_article_data(article)
                title = data['title'][:60]
                publisher = data['publisher']
                print(f"  - {title}...")
                print(f"    ({publisher})")
        else:
            print("  No news available")


def analyze_news_sources(symbol: str = "TSLA"):
    """Analyze news sources for a ticker."""
    print("\n" + "=" * 60)
    print(f"News Source Analysis for {symbol}")
    print("=" * 60)

    client = YFinanceClient()
    news = client.get_news(symbol)

    if not news:
        print("\nNo news available")
        return

    # Count sources
    sources = {}
    for article in news:
        data = extract_article_data(article)
        publisher = data['publisher']
        sources[publisher] = sources.get(publisher, 0) + 1

    # Sort by count
    sorted_sources = sorted(sources.items(), key=lambda x: x[1], reverse=True)

    print(f"\nTotal articles: {len(news)}")
    print(f"Unique sources: {len(sources)}")
    print()

    print("| Source                          | Articles |")
    print("|---------------------------------|----------|")

    for source, count in sorted_sources[:15]:
        print(f"| {source:<31} | {count:>8} |")


def fetch_news_with_thumbnails(symbol: str = "NVDA"):
    """Fetch news including thumbnail information."""
    print("\n" + "=" * 60)
    print(f"News with Media Info for {symbol}")
    print("=" * 60)

    client = YFinanceClient()
    news = client.get_news(symbol)

    if not news:
        print("\nNo news available")
        return

    print()
    for i, article in enumerate(news[:5], 1):
        data = extract_article_data(article)
        title = data['title']
        publisher = data['publisher']
        link = data['link']

        # Check for thumbnail
        thumbnail = data.get('thumbnail', {})
        resolutions = thumbnail.get('resolutions', []) if thumbnail else []
        has_image = len(resolutions) > 0 if resolutions else False

        print(f"{i}. {title}")
        print(f"   Publisher: {publisher}")
        print(f"   Has Image: {'Yes' if has_image else 'No'}")
        print(f"   Link: {link[:70]}...")
        print()


def fetch_recent_news_only(symbol: str = "META", hours: int = 24):
    """Fetch only news from the last N hours."""
    print("\n" + "=" * 60)
    print(f"News from Last {hours} Hours for {symbol}")
    print("=" * 60)

    client = YFinanceClient()
    news = client.get_news(symbol)

    if not news:
        print("\nNo news available")
        return

    cutoff = datetime.now() - timedelta(hours=hours)

    recent_news = []
    for article in news:
        data = extract_article_data(article)
        dt = parse_pub_date(data)
        if dt and dt > cutoff:
            recent_news.append((article, data, dt))

    print(f"\nTotal news: {len(news)}")
    print(f"Recent news (last {hours}h): {len(recent_news)}")
    print()

    if not recent_news:
        print(f"No news in the last {hours} hours")
        return

    for i, (article, data, dt) in enumerate(recent_news[:10], 1):
        title = data['title']
        publisher = data['publisher']

        time_ago = datetime.now() - dt
        if time_ago.seconds > 3600:
            ago_str = f"{time_ago.seconds // 3600}h {(time_ago.seconds % 3600) // 60}m ago"
        else:
            ago_str = f"{time_ago.seconds // 60}m ago"

        print(f"{i}. {title}")
        print(f"   {publisher} - {ago_str}")
        print()


def compare_news_volume():
    """Compare news volume across stocks."""
    print("\n" + "=" * 60)
    print("News Volume Comparison")
    print("=" * 60)

    client = YFinanceClient()

    symbols = ["AAPL", "MSFT", "GOOGL", "AMZN", "META", "NVDA", "TSLA"]

    print("\n| Symbol | Total News | Last 24h | Top Source              |")
    print("|--------|------------|----------|-------------------------|")

    cutoff = datetime.now() - timedelta(hours=24)

    for symbol in symbols:
        try:
            news = client.get_news(symbol)

            total = len(news) if news else 0

            # Count last 24h
            recent = 0
            sources = {}
            for article in (news or []):
                data = extract_article_data(article)
                dt = parse_pub_date(data)
                if dt and dt > cutoff:
                    recent += 1

                publisher = data['publisher']
                sources[publisher] = sources.get(publisher, 0) + 1

            # Top source
            top_source = max(sources.items(), key=lambda x: x[1])[0] if sources else "N/A"
            top_source = top_source[:23]

            print(f"| {symbol:<6} | {total:>10} | {recent:>8} | {top_source:<23} |")
        except Exception as e:
            print(f"| {symbol:<6} | Error: {str(e)[:35]} |")


def fetch_index_news():
    """Fetch news for major indexes."""
    print("\n" + "=" * 60)
    print("Index-Related News")
    print("=" * 60)

    client = YFinanceClient()

    # SPY tracks S&P 500, QQQ tracks NASDAQ
    symbols = [
        ("SPY", "S&P 500 (SPY)"),
        ("QQQ", "NASDAQ (QQQ)"),
        ("DIA", "Dow Jones (DIA)"),
    ]

    for symbol, name in symbols:
        news = client.get_news(symbol)

        print(f"\n--- {name} ---")

        if news:
            for article in news[:3]:
                data = extract_article_data(article)
                title = data['title'][:55]
                publisher = data['publisher']
                print(f"  - {title}...")
                print(f"    ({publisher})")
        else:
            print("  No news available")


def fetch_indian_stock_news():
    """Fetch news for Indian stocks."""
    print("\n" + "=" * 60)
    print("Indian Stock News")
    print("=" * 60)

    client = YFinanceClient()

    symbols = [
        ("RELIANCE.NS", "Reliance Industries"),
        ("TCS.NS", "Tata Consultancy Services"),
        ("INFY.NS", "Infosys"),
        ("HDFCBANK.NS", "HDFC Bank"),
    ]

    for symbol, name in symbols:
        news = client.get_news(symbol)

        print(f"\n--- {name} ---")

        if news:
            for article in news[:3]:
                data = extract_article_data(article)
                title = data['title'][:55]
                publisher = data['publisher']
                print(f"  - {title}...")
                print(f"    ({publisher})")
        else:
            print("  No news available")


def get_news_summary(symbol: str = "AMZN"):
    """Get a formatted news summary for a ticker."""
    print("\n" + "=" * 60)
    print(f"News Summary for {symbol}")
    print("=" * 60)

    client = YFinanceClient()

    # Get ticker info for context
    info = client.get_ticker_info(symbol)
    company_name = info.info.get('shortName', symbol)
    current_price = info.info.get('currentPrice', 0)
    change = info.info.get('regularMarketChange', 0)
    change_pct = info.info.get('regularMarketChangePercent', 0)

    news = client.get_news(symbol)

    print(f"\n{company_name} ({symbol})")
    if current_price:
        print(f"Price: ${current_price:.2f} ({change:+.2f}, {change_pct:+.2f}%)")
    print()

    if not news:
        print("No recent news available")
        return

    print(f"--- Latest {min(5, len(news))} Headlines ---")
    print()

    for article in news[:5]:
        data = extract_article_data(article)
        title = data['title']
        publisher = data['publisher']

        dt = parse_pub_date(data)
        if dt:
            time_str = dt.strftime('%b %d, %H:%M')
        else:
            time_str = "Unknown"

        print(f"- {title}")
        print(f"  {publisher} | {time_str}")
        print()


def search_news_keywords(symbol: str = "TSLA", keywords: list[str] | None = None):
    """Search news for specific keywords."""
    print("\n" + "=" * 60)
    print(f"Keyword Search in {symbol} News")
    print("=" * 60)

    if keywords is None:
        keywords = ["earnings", "revenue", "CEO", "lawsuit", "recall"]

    client = YFinanceClient()
    news = client.get_news(symbol)

    if not news:
        print("\nNo news available")
        return

    print(f"\nSearching {len(news)} articles for keywords: {', '.join(keywords)}")
    print()

    for keyword in keywords:
        matches = []
        for article in news:
            data = extract_article_data(article)
            title = data['title'].lower()
            if keyword.lower() in title:
                matches.append(data)

        print(f"--- '{keyword}' ({len(matches)} matches) ---")
        if matches:
            for data in matches[:3]:
                title = data['title'][:60]
                print(f"  - {title}...")
        else:
            print("  No matches")
        print()


if __name__ == "__main__":
    # Run all examples
    fetch_ticker_news("AAPL")
    fetch_news_multiple_stocks()
    analyze_news_sources("TSLA")
    fetch_news_with_thumbnails("NVDA")
    fetch_recent_news_only("META", hours=24)
    compare_news_volume()
    fetch_index_news()
    fetch_indian_stock_news()
    get_news_summary("AMZN")
    search_news_keywords("TSLA", ["earnings", "Model", "Musk", "price"])
