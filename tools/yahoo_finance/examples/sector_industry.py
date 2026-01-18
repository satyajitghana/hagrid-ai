"""Examples for sector and industry data from Yahoo Finance.

This script demonstrates how to:
- Fetch sector overview and performance data
- Get top companies in a sector
- Explore industries within sectors
- Navigate sector/industry hierarchy
"""

from tools.yahoo_finance import YFinanceClient


def fetch_sector_overview(sector_key: str = "technology"):
    """Fetch overview for a sector."""
    print("=" * 60)
    print(f"Sector Overview: {sector_key}")
    print("=" * 60)

    client = YFinanceClient()
    sector = client.get_sector(sector_key)

    print(f"\nKey: {sector.key}")
    print(f"Name: {sector.name}")
    print(f"Symbol: {sector.symbol}")

    print("\n--- Overview ---")
    if sector.overview:
        for key, value in list(sector.overview.items())[:10]:
            print(f"{key}: {value}")
    else:
        print("No overview data available")


def fetch_sector_top_companies(sector_key: str = "technology"):
    """Fetch top companies in a sector."""
    print("\n" + "=" * 60)
    print(f"Top Companies in {sector_key.title()} Sector")
    print("=" * 60)

    client = YFinanceClient()
    sector = client.get_sector(sector_key)

    if not sector.top_companies:
        print("No company data available")
        return

    print(f"\nTotal companies: {len(sector.top_companies)}")

    print("\n| Symbol | Name | Market Cap |")
    print("|--------|------|------------|")

    for company in sector.top_companies[:15]:
        symbol = company.get('symbol', 'N/A')
        name = company.get('shortName', company.get('name', 'N/A'))
        if name and len(name) > 25:
            name = name[:22] + "..."
        mcap = company.get('marketCap', 0)
        if mcap >= 1e12:
            mcap_str = f"${mcap/1e12:.2f}T"
        elif mcap >= 1e9:
            mcap_str = f"${mcap/1e9:.1f}B"
        elif mcap >= 1e6:
            mcap_str = f"${mcap/1e6:.1f}M"
        else:
            mcap_str = "N/A"

        print(f"| {symbol:<6} | {name:<25} | {mcap_str:>10} |")


def fetch_sector_etfs(sector_key: str = "technology"):
    """Fetch top ETFs for a sector."""
    print("\n" + "=" * 60)
    print(f"Top ETFs in {sector_key.title()} Sector")
    print("=" * 60)

    client = YFinanceClient()
    sector = client.get_sector(sector_key)

    if not sector.top_etfs:
        print("No ETF data available")
        return

    print(f"\nTotal ETFs: {len(sector.top_etfs)}")

    print("\n| Symbol | Name |")
    print("|--------|------|")

    for etf in sector.top_etfs[:10]:
        symbol = etf.get('symbol', 'N/A')
        name = etf.get('shortName', etf.get('name', 'N/A'))
        if name and len(name) > 40:
            name = name[:37] + "..."

        print(f"| {symbol:<6} | {name:<40} |")


def fetch_sector_industries(sector_key: str = "technology"):
    """Fetch industries within a sector."""
    print("\n" + "=" * 60)
    print(f"Industries in {sector_key.title()} Sector")
    print("=" * 60)

    client = YFinanceClient()
    sector = client.get_sector(sector_key)

    if not sector.industries:
        print("No industry data available")
        return

    print(f"\nTotal industries: {len(sector.industries)}")

    print("\n| Industry Key | Name |")
    print("|--------------|------|")

    for industry in sector.industries[:20]:
        key = industry.get('key', industry.get('industryKey', 'N/A'))
        name = industry.get('name', industry.get('industryName', 'N/A'))
        if name and len(name) > 35:
            name = name[:32] + "..."

        print(f"| {key:<25} | {name:<35} |")


def fetch_industry_overview(industry_key: str = "software-infrastructure"):
    """Fetch overview for an industry."""
    print("\n" + "=" * 60)
    print(f"Industry Overview: {industry_key}")
    print("=" * 60)

    client = YFinanceClient()
    industry = client.get_industry(industry_key)

    print(f"\nKey: {industry.key}")
    print(f"Name: {industry.name}")
    print(f"Symbol: {industry.symbol}")
    print(f"Sector: {industry.sector_name} ({industry.sector_key})")

    print("\n--- Overview ---")
    if industry.overview:
        for key, value in list(industry.overview.items())[:10]:
            print(f"{key}: {value}")


def fetch_industry_top_companies(industry_key: str = "software-infrastructure"):
    """Fetch top companies in an industry."""
    print("\n" + "=" * 60)
    print(f"Top Companies in {industry_key}")
    print("=" * 60)

    client = YFinanceClient()
    industry = client.get_industry(industry_key)

    if not industry.top_companies:
        print("No company data available")
        return

    print(f"\nTotal companies: {len(industry.top_companies)}")

    print("\n| Symbol | Name | Price |")
    print("|--------|------|-------|")

    for company in industry.top_companies[:15]:
        symbol = company.get('symbol', 'N/A')
        name = company.get('shortName', company.get('name', 'N/A'))
        if name and len(name) > 30:
            name = name[:27] + "..."
        price = company.get('regularMarketPrice', 'N/A')
        price_str = f"${price:.2f}" if isinstance(price, (int, float)) else 'N/A'

        print(f"| {symbol:<6} | {name:<30} | {price_str:>8} |")


def fetch_industry_growth_companies(industry_key: str = "software-infrastructure"):
    """Fetch top growth companies in an industry."""
    print("\n" + "=" * 60)
    print(f"Top Growth Companies in {industry_key}")
    print("=" * 60)

    client = YFinanceClient()
    industry = client.get_industry(industry_key)

    if not industry.top_growth_companies:
        print("No growth company data available")
        return

    print(f"\nTotal growth companies: {len(industry.top_growth_companies)}")

    print("\n| Symbol | Name |")
    print("|--------|------|")

    for company in industry.top_growth_companies[:10]:
        symbol = company.get('symbol', 'N/A')
        name = company.get('shortName', company.get('name', 'N/A'))
        if name and len(name) > 35:
            name = name[:32] + "..."

        print(f"| {symbol:<8} | {name:<35} |")


def compare_sectors():
    """Compare multiple sectors."""
    print("\n" + "=" * 60)
    print("Sector Comparison")
    print("=" * 60)

    client = YFinanceClient()

    sectors = [
        "technology",
        "healthcare",
        "financial-services",
        "consumer-cyclical",
        "industrials",
        "energy",
    ]

    print("\n| Sector | Top Company | Industries |")
    print("|--------|-------------|------------|")

    for sector_key in sectors:
        sector = client.get_sector(sector_key)

        if sector.top_companies:
            top = sector.top_companies[0].get('symbol', 'N/A')
        else:
            top = "N/A"

        ind_count = len(sector.industries) if sector.industries else 0

        print(f"| {sector_key:<20} | {top:<11} | {ind_count:>10} |")


def explore_healthcare_sector():
    """Deep dive into healthcare sector and its industries."""
    print("\n" + "=" * 60)
    print("Healthcare Sector Deep Dive")
    print("=" * 60)

    client = YFinanceClient()
    sector = client.get_sector("healthcare")

    print(f"\nSector: {sector.name}")

    # List all industries
    if sector.industries:
        print("\n--- Healthcare Industries ---")
        for ind in sector.industries[:10]:
            ind_key = ind.get('key', ind.get('industryKey', 'N/A'))
            ind_name = ind.get('name', ind.get('industryName', 'N/A'))
            print(f"  {ind_key}: {ind_name}")

    # Show top companies
    print("\n--- Top Healthcare Companies ---")
    for company in sector.top_companies[:5]:
        symbol = company.get('symbol', 'N/A')
        name = company.get('shortName', 'N/A')
        print(f"  {symbol}: {name}")


def list_available_sectors():
    """List all available sector keys."""
    print("\n" + "=" * 60)
    print("Available Sector Keys")
    print("=" * 60)

    sectors = [
        ("technology", "Technology"),
        ("healthcare", "Healthcare"),
        ("financial-services", "Financial Services"),
        ("consumer-cyclical", "Consumer Cyclical"),
        ("consumer-defensive", "Consumer Defensive"),
        ("industrials", "Industrials"),
        ("energy", "Energy"),
        ("utilities", "Utilities"),
        ("real-estate", "Real Estate"),
        ("basic-materials", "Basic Materials"),
        ("communication-services", "Communication Services"),
    ]

    print("\n| Key | Name |")
    print("|-----|------|")

    for key, name in sectors:
        print(f"| {key:<25} | {name:<25} |")


def navigate_sector_to_company():
    """Navigate from sector to industry to company."""
    print("\n" + "=" * 60)
    print("Sector -> Industry -> Company Navigation")
    print("=" * 60)

    client = YFinanceClient()

    # Start with Technology sector
    print("\n1. Get Technology Sector")
    sector = client.get_sector("technology")
    print(f"   Sector: {sector.name}")
    print(f"   Industries: {len(sector.industries)}")

    # Get first industry
    if sector.industries:
        ind_key = sector.industries[0].get('key', sector.industries[0].get('industryKey'))
        print(f"\n2. Navigate to Industry: {ind_key}")

        industry = client.get_industry(ind_key)
        print(f"   Industry: {industry.name}")
        print(f"   Companies: {len(industry.top_companies)}")

        # Get first company
        if industry.top_companies:
            company = industry.top_companies[0]
            symbol = company.get('symbol')
            print(f"\n3. Top Company: {symbol}")

            # Get full company info
            info = client.get_ticker_info(symbol)
            print(f"   Name: {info.info.get('shortName')}")
            print(f"   Price: ${info.info.get('currentPrice', 'N/A')}")
            print(f"   Market Cap: ${info.info.get('marketCap', 0)/1e9:.1f}B")


if __name__ == "__main__":
    fetch_sector_overview("technology")
    fetch_sector_top_companies("technology")
    fetch_sector_etfs("technology")
    fetch_sector_industries("technology")
    fetch_industry_overview("software-infrastructure")
    fetch_industry_top_companies("software-infrastructure")
    fetch_industry_growth_companies("software-infrastructure")
    compare_sectors()
    explore_healthcare_sector()
    list_available_sectors()
    navigate_sector_to_company()
