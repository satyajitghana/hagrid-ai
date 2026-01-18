"""Examples for bulk data download from Yahoo Finance.

This script demonstrates how to:
- Download historical data for multiple tickers at once
- Efficiently fetch data for portfolio analysis
- Compare multiple stocks using bulk download
- Download data with different periods and intervals
"""

from tools.yahoo_finance import YFinanceClient


def bulk_download_tech_giants():
    """Bulk download data for tech giants."""
    print("=" * 60)
    print("Bulk Download - Tech Giants")
    print("=" * 60)

    client = YFinanceClient()

    symbols = ["AAPL", "MSFT", "GOOGL", "AMZN", "META", "NVDA"]

    result = client.download(
        tickers=symbols,
        period="1mo",
        interval="1d"
    )

    print(f"\nSymbols: {result.symbols}")
    print(f"Period: {result.period}")
    print(f"Interval: {result.interval}")
    print(f"Data points: {len(result.data)}")

    if not result.data:
        print("No data downloaded")
        return

    print("\n--- Recent Data Sample ---")
    print("| Date | Symbol | Close | Volume |")
    print("|------|--------|-------|--------|")

    # Show last 10 entries
    for entry in result.data[-15:]:
        date = entry.get('Date', 'N/A')
        if hasattr(date, 'strftime'):
            date_str = date.strftime('%Y-%m-%d')
        else:
            date_str = str(date)[:10]

        # Find any close price column
        close = None
        volume = None
        symbol = None

        for key in entry.keys():
            if 'Close' in str(key):
                close = entry[key]
                # Extract symbol from column name
                if '_' in str(key):
                    symbol = str(key).split('_')[0]
            if 'Volume' in str(key):
                volume = entry[key]

        if close:
            close_str = f"${close:.2f}"
            vol_str = f"{volume/1e6:.1f}M" if volume else "N/A"
            print(f"| {date_str} | {symbol or 'N/A':<6} | {close_str:>8} | {vol_str:>8} |")


def bulk_download_faang():
    """Bulk download FAANG stocks data."""
    print("\n" + "=" * 60)
    print("Bulk Download - FAANG Stocks")
    print("=" * 60)

    client = YFinanceClient()

    symbols = ["META", "AAPL", "AMZN", "NFLX", "GOOGL"]

    result = client.download(
        tickers=symbols,
        period="5d",
        interval="1h"
    )

    print(f"\nSymbols: {result.symbols}")
    print(f"Total data points: {len(result.data)}")

    if result.data:
        # Get column names
        cols = list(result.data[0].keys())
        print(f"Columns: {', '.join(cols[:8])}...")


def bulk_download_indices():
    """Bulk download major indices data."""
    print("\n" + "=" * 60)
    print("Bulk Download - Major Indices")
    print("=" * 60)

    client = YFinanceClient()

    # Major US indices
    symbols = ["^GSPC", "^DJI", "^IXIC", "^RUT", "^VIX"]

    result = client.download(
        tickers=symbols,
        period="1mo",
        interval="1d"
    )

    print(f"\nIndices downloaded: {result.symbols}")
    print(f"Data points: {len(result.data)}")


def bulk_download_etfs():
    """Bulk download popular ETFs data."""
    print("\n" + "=" * 60)
    print("Bulk Download - Popular ETFs")
    print("=" * 60)

    client = YFinanceClient()

    etfs = ["SPY", "QQQ", "DIA", "IWM", "VTI", "VOO"]

    result = client.download(
        tickers=etfs,
        period="3mo",
        interval="1d"
    )

    print(f"\nETFs: {result.symbols}")
    print(f"Data points: {len(result.data)}")

    if result.data:
        # Calculate simple returns for comparison
        print("\n--- Latest Prices ---")

        last_row = result.data[-1] if result.data else {}

        print("| ETF | Close |")
        print("|-----|-------|")

        for etf in etfs:
            close_col = f"{etf}_Close"
            close = last_row.get(close_col)
            if close:
                print(f"| {etf:<3} | ${close:>8.2f} |")


def bulk_download_indian_stocks():
    """Bulk download Indian stocks data."""
    print("\n" + "=" * 60)
    print("Bulk Download - Indian Stocks")
    print("=" * 60)

    client = YFinanceClient()

    symbols = [
        "RELIANCE.NS",
        "TCS.NS",
        "INFY.NS",
        "HDFCBANK.NS",
        "ICICIBANK.NS",
    ]

    result = client.download(
        tickers=symbols,
        period="1mo",
        interval="1d"
    )

    print(f"\nStocks: {result.symbols}")
    print(f"Data points: {len(result.data)}")


def bulk_download_with_dates():
    """Bulk download with specific date range."""
    print("\n" + "=" * 60)
    print("Bulk Download - Custom Date Range")
    print("=" * 60)

    client = YFinanceClient()

    symbols = ["AAPL", "MSFT", "GOOGL"]

    result = client.download(
        tickers=symbols,
        start="2024-01-01",
        end="2024-06-30",
        interval="1d"
    )

    print(f"\nSymbols: {result.symbols}")
    print(f"Start: {result.start}")
    print(f"End: {result.end}")
    print(f"Data points: {len(result.data)}")


def bulk_download_crypto():
    """Bulk download cryptocurrency data."""
    print("\n" + "=" * 60)
    print("Bulk Download - Cryptocurrencies")
    print("=" * 60)

    client = YFinanceClient()

    cryptos = ["BTC-USD", "ETH-USD", "SOL-USD", "ADA-USD", "DOT-USD"]

    result = client.download(
        tickers=cryptos,
        period="1mo",
        interval="1d"
    )

    print(f"\nCryptos: {result.symbols}")
    print(f"Data points: {len(result.data)}")


def bulk_download_currencies():
    """Bulk download currency pair data."""
    print("\n" + "=" * 60)
    print("Bulk Download - Currency Pairs")
    print("=" * 60)

    client = YFinanceClient()

    pairs = ["EURUSD=X", "GBPUSD=X", "USDJPY=X", "USDCAD=X", "AUDUSD=X"]

    result = client.download(
        tickers=pairs,
        period="1mo",
        interval="1d"
    )

    print(f"\nCurrency Pairs: {result.symbols}")
    print(f"Data points: {len(result.data)}")


def bulk_download_sector_etfs():
    """Bulk download sector ETF data for comparison."""
    print("\n" + "=" * 60)
    print("Bulk Download - Sector ETFs")
    print("=" * 60)

    client = YFinanceClient()

    sector_etfs = ["XLK", "XLF", "XLV", "XLE", "XLY", "XLP", "XLI", "XLU"]

    result = client.download(
        tickers=sector_etfs,
        period="3mo",
        interval="1d"
    )

    print(f"\nSector ETFs: {result.symbols}")
    print(f"Data points: {len(result.data)}")

    if result.data:
        # Show latest closes
        last_row = result.data[-1] if result.data else {}

        print("\n--- Latest Sector ETF Prices ---")
        print("| Sector ETF | Close |")
        print("|------------|-------|")

        for etf in sector_etfs:
            close_col = f"{etf}_Close"
            close = last_row.get(close_col)
            if close:
                print(f"| {etf:<10} | ${close:>8.2f} |")


def bulk_download_intraday():
    """Bulk download intraday data."""
    print("\n" + "=" * 60)
    print("Bulk Download - Intraday Data")
    print("=" * 60)

    client = YFinanceClient()

    symbols = ["AAPL", "MSFT", "GOOGL"]

    # 5-minute intervals for last 5 days
    result = client.download(
        tickers=symbols,
        period="5d",
        interval="5m"
    )

    print(f"\nSymbols: {result.symbols}")
    print(f"Interval: {result.interval}")
    print(f"Data points: {len(result.data)}")


def compare_portfolio():
    """Download and compare a sample portfolio."""
    print("\n" + "=" * 60)
    print("Portfolio Comparison")
    print("=" * 60)

    client = YFinanceClient()

    # Sample diversified portfolio
    portfolio = {
        "AAPL": 10,
        "MSFT": 8,
        "GOOGL": 5,
        "SPY": 15,
        "BND": 20,
    }

    result = client.download(
        tickers=list(portfolio.keys()),
        period="1mo",
        interval="1d"
    )

    print(f"\nPortfolio positions: {list(portfolio.keys())}")
    print(f"Data points: {len(result.data)}")

    if result.data and len(result.data) >= 2:
        first_row = result.data[0]
        last_row = result.data[-1]

        print("\n--- Portfolio Performance ---")
        print("| Symbol | Shares | Start | Current | Gain/Loss |")
        print("|--------|--------|-------|---------|-----------|")

        total_start = 0
        total_current = 0

        for symbol, shares in portfolio.items():
            close_col = f"{symbol}_Close"
            start_price = first_row.get(close_col, 0)
            current_price = last_row.get(close_col, 0)

            if start_price and current_price:
                start_val = start_price * shares
                current_val = current_price * shares
                total_start += start_val
                total_current += current_val
                gain = current_val - start_val
                gain_pct = (gain / start_val) * 100 if start_val else 0

                print(f"| {symbol:<6} | {shares:>6} | ${start_val:>7,.0f} | ${current_val:>7,.0f} | ${gain:>+8,.0f} ({gain_pct:+.1f}%) |")

        if total_start > 0:
            total_gain = total_current - total_start
            total_pct = (total_gain / total_start) * 100
            print("|--------|--------|-------|---------|-----------|")
            print(f"| TOTAL  |        | ${total_start:>7,.0f} | ${total_current:>7,.0f} | ${total_gain:>+8,.0f} ({total_pct:+.1f}%) |")


if __name__ == "__main__":
    bulk_download_tech_giants()
    bulk_download_faang()
    bulk_download_indices()
    bulk_download_etfs()
    bulk_download_indian_stocks()
    bulk_download_with_dates()
    bulk_download_crypto()
    bulk_download_currencies()
    bulk_download_sector_etfs()
    bulk_download_intraday()
    compare_portfolio()
