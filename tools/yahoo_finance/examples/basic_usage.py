"""Basic usage examples for Yahoo Finance client.

This script demonstrates how to:
- Get comprehensive ticker information
- Compare ticker info across different markets
- Access key valuation metrics
- Generate markdown reports
"""

from tools.yahoo_finance import YFinanceClient


def fetch_ticker_info(symbol: str = "AAPL"):
    """Fetch comprehensive information for a ticker."""
    print("=" * 60)
    print(f"Ticker Information for {symbol}")
    print("=" * 60)

    client = YFinanceClient()
    info = client.get_ticker_info(symbol)
    i = info.info

    print(f"\n--- Basic Info ---")
    print(f"Symbol: {info.symbol}")
    print(f"Name: {i.get('shortName', 'N/A')}")
    print(f"Long Name: {i.get('longName', 'N/A')}")
    print(f"Sector: {i.get('sector', 'N/A')}")
    print(f"Industry: {i.get('industry', 'N/A')}")
    print(f"Country: {i.get('country', 'N/A')}")
    print(f"Currency: {i.get('currency', 'N/A')}")
    print(f"Exchange: {i.get('exchange', 'N/A')}")
    print(f"Website: {i.get('website', 'N/A')}")

    print(f"\n--- Market Data ---")
    print(f"Current Price: {i.get('currentPrice', 'N/A')}")
    print(f"Previous Close: {i.get('previousClose', 'N/A')}")
    print(f"Open: {i.get('open', 'N/A')}")
    print(f"Day High: {i.get('dayHigh', 'N/A')}")
    print(f"Day Low: {i.get('dayLow', 'N/A')}")
    print(f"Volume: {i.get('volume', 'N/A'):,}" if i.get('volume') else "Volume: N/A")
    print(f"Average Volume: {i.get('averageVolume', 'N/A'):,}" if i.get('averageVolume') else "Average Volume: N/A")

    print(f"\n--- 52 Week Range ---")
    print(f"52 Week High: {i.get('fiftyTwoWeekHigh', 'N/A')}")
    print(f"52 Week Low: {i.get('fiftyTwoWeekLow', 'N/A')}")
    print(f"52 Week Change: {i.get('52WeekChange', 'N/A'):.2%}" if i.get('52WeekChange') else "52 Week Change: N/A")

    print(f"\n--- Market Cap & Shares ---")
    market_cap = i.get('marketCap')
    if market_cap:
        if market_cap >= 1e12:
            print(f"Market Cap: ${market_cap/1e12:.2f}T")
        elif market_cap >= 1e9:
            print(f"Market Cap: ${market_cap/1e9:.2f}B")
        else:
            print(f"Market Cap: ${market_cap/1e6:.2f}M")
    else:
        print("Market Cap: N/A")
    print(f"Shares Outstanding: {i.get('sharesOutstanding', 'N/A'):,}" if i.get('sharesOutstanding') else "Shares Outstanding: N/A")
    print(f"Float Shares: {i.get('floatShares', 'N/A'):,}" if i.get('floatShares') else "Float Shares: N/A")


def fetch_valuation_metrics(symbol: str = "MSFT"):
    """Fetch key valuation metrics for a ticker."""
    print("\n" + "=" * 60)
    print(f"Valuation Metrics for {symbol}")
    print("=" * 60)

    client = YFinanceClient()
    info = client.get_ticker_info(symbol)
    i = info.info

    print(f"\n--- Price Ratios ---")
    print(f"P/E (Trailing): {i.get('trailingPE', 'N/A'):.2f}" if i.get('trailingPE') else "P/E (Trailing): N/A")
    print(f"P/E (Forward): {i.get('forwardPE', 'N/A'):.2f}" if i.get('forwardPE') else "P/E (Forward): N/A")
    print(f"PEG Ratio: {i.get('pegRatio', 'N/A'):.2f}" if i.get('pegRatio') else "PEG Ratio: N/A")
    print(f"Price/Sales: {i.get('priceToSalesTrailing12Months', 'N/A'):.2f}" if i.get('priceToSalesTrailing12Months') else "Price/Sales: N/A")
    print(f"Price/Book: {i.get('priceToBook', 'N/A'):.2f}" if i.get('priceToBook') else "Price/Book: N/A")
    print(f"Enterprise Value/EBITDA: {i.get('enterpriseToEbitda', 'N/A'):.2f}" if i.get('enterpriseToEbitda') else "Enterprise Value/EBITDA: N/A")

    print(f"\n--- Profitability ---")
    print(f"Profit Margin: {i.get('profitMargins', 0)*100:.2f}%" if i.get('profitMargins') else "Profit Margin: N/A")
    print(f"Operating Margin: {i.get('operatingMargins', 0)*100:.2f}%" if i.get('operatingMargins') else "Operating Margin: N/A")
    print(f"Gross Margin: {i.get('grossMargins', 0)*100:.2f}%" if i.get('grossMargins') else "Gross Margin: N/A")
    print(f"ROE: {i.get('returnOnEquity', 0)*100:.2f}%" if i.get('returnOnEquity') else "ROE: N/A")
    print(f"ROA: {i.get('returnOnAssets', 0)*100:.2f}%" if i.get('returnOnAssets') else "ROA: N/A")

    print(f"\n--- Dividends ---")
    print(f"Dividend Rate: {i.get('dividendRate', 'N/A')}")
    print(f"Dividend Yield: {i.get('dividendYield', 0)*100:.2f}%" if i.get('dividendYield') else "Dividend Yield: N/A")
    print(f"Payout Ratio: {i.get('payoutRatio', 0)*100:.2f}%" if i.get('payoutRatio') else "Payout Ratio: N/A")
    print(f"Ex-Dividend Date: {i.get('exDividendDate', 'N/A')}")


def compare_us_stocks():
    """Compare key metrics across major US tech stocks."""
    print("\n" + "=" * 60)
    print("US Tech Giants Comparison")
    print("=" * 60)

    symbols = ["AAPL", "MSFT", "GOOGL", "AMZN", "NVDA"]
    client = YFinanceClient()

    print("\n| Symbol | Price      | Market Cap  | P/E    | Div Yield |")
    print("|--------|------------|-------------|--------|-----------|")

    for symbol in symbols:
        try:
            info = client.get_ticker_info(symbol)
            i = info.info

            price = i.get('currentPrice', 0)
            market_cap = i.get('marketCap', 0)
            pe = i.get('trailingPE', 0)
            div_yield = i.get('dividendYield', 0)

            # Format market cap
            if market_cap >= 1e12:
                mc_str = f"${market_cap/1e12:.2f}T"
            elif market_cap >= 1e9:
                mc_str = f"${market_cap/1e9:.1f}B"
            else:
                mc_str = "N/A"

            pe_str = f"{pe:.1f}" if pe else "N/A"
            div_str = f"{div_yield*100:.2f}%" if div_yield else "0.00%"

            print(f"| {symbol:<6} | ${price:>9.2f} | {mc_str:>11} | {pe_str:>6} | {div_str:>9} |")
        except Exception as e:
            print(f"| {symbol:<6} | Error: {str(e)[:30]} |")


def compare_indian_stocks():
    """Compare key metrics across major Indian stocks."""
    print("\n" + "=" * 60)
    print("Indian Blue Chips Comparison (NSE)")
    print("=" * 60)

    # Indian stocks have .NS suffix for NSE
    symbols = ["RELIANCE.NS", "TCS.NS", "INFY.NS", "HDFCBANK.NS", "ICICIBANK.NS"]
    client = YFinanceClient()

    print("\n| Symbol        | Price (INR) | Market Cap   | P/E    | Sector       |")
    print("|---------------|-------------|--------------|--------|--------------|")

    for symbol in symbols:
        try:
            info = client.get_ticker_info(symbol)
            i = info.info

            price = i.get('currentPrice', 0)
            market_cap = i.get('marketCap', 0)
            pe = i.get('trailingPE', 0)
            sector = i.get('sector', 'N/A')[:12]

            # Format market cap in INR
            if market_cap >= 1e12:
                mc_str = f"₹{market_cap/1e12:.2f}T"
            elif market_cap >= 1e9:
                mc_str = f"₹{market_cap/1e9:.0f}B"
            else:
                mc_str = "N/A"

            pe_str = f"{pe:.1f}" if pe else "N/A"
            short_symbol = symbol.replace(".NS", "")

            print(f"| {short_symbol:<13} | {price:>11,.2f} | {mc_str:>12} | {pe_str:>6} | {sector:<12} |")
        except Exception as e:
            print(f"| {symbol:<13} | Error: {str(e)[:30]} |")


def fetch_company_description(symbol: str = "TSLA"):
    """Fetch and display company business summary."""
    print("\n" + "=" * 60)
    print(f"Company Description for {symbol}")
    print("=" * 60)

    client = YFinanceClient()
    info = client.get_ticker_info(symbol)
    i = info.info

    print(f"\n{i.get('shortName', symbol)}")
    print(f"Sector: {i.get('sector', 'N/A')} | Industry: {i.get('industry', 'N/A')}")
    print(f"Employees: {i.get('fullTimeEmployees', 'N/A'):,}" if i.get('fullTimeEmployees') else "Employees: N/A")
    print()

    summary = i.get('longBusinessSummary', 'No description available.')
    # Word wrap the summary
    words = summary.split()
    line = ""
    for word in words:
        if len(line) + len(word) + 1 <= 80:
            line += word + " "
        else:
            print(line.strip())
            line = word + " "
    if line:
        print(line.strip())


def generate_markdown_report(symbol: str = "AAPL"):
    """Generate a comprehensive markdown report for a ticker."""
    print("\n" + "=" * 60)
    print(f"Markdown Report for {symbol}")
    print("=" * 60)

    client = YFinanceClient()
    report = client.get_ticker_markdown(symbol)

    # Print first 2000 chars to show structure
    print("\n" + report[:2000])
    if len(report) > 2000:
        print("\n... [Report truncated for display]")


if __name__ == "__main__":
    # Run all examples
    fetch_ticker_info("AAPL")
    fetch_valuation_metrics("MSFT")
    compare_us_stocks()
    compare_indian_stocks()
    fetch_company_description("TSLA")
    generate_markdown_report("GOOGL")
