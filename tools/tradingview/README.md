# TradingView SDK

A Python SDK for accessing TradingView's public APIs to get stock fundamentals, technical indicators, news, and symbol information.

## Features

- **Symbol Search**: Search for stocks, futures, bonds, funds, and other instruments
- **News**: Get latest news for any symbol
- **Technical Indicators**: Access RSI, MACD, moving averages, pivot points, and more
- **Technical Recommendations**: Get buy/sell recommendations based on technical analysis
- **No Authentication Required**: Uses public TradingView endpoints

## Installation

The SDK uses `httpx` for HTTP requests and `pydantic` for data validation. Ensure these are installed:

```bash
pip install httpx pydantic
```

## Quick Start

```python
from tools.tradingview import TradingViewClient

# Create client
client = TradingViewClient()

# Search for a symbol
results = client.search_symbol("RELIANCE")
symbol = results.first_stock
print(f"Found: {symbol.full_symbol}")  # NSE:RELIANCE

# Get technical indicators
technicals = client.get_technicals("NSE:RELIANCE")
print(f"RSI: {technicals.rsi}")
print(f"Price: {technicals.close}")
print(f"Recommendation: {technicals.overall_recommendation}")

# Get news
news = client.get_news("NSE:RELIANCE")
for item in news.items[:5]:
    print(f"{item.published_date}: {item.title}")
```

## API Reference

### TradingViewClient

The main client class for interacting with TradingView APIs.

#### Symbol Search

```python
# Search for symbols
results = client.search_symbol("RELIANCE", exchange="NSE")

# Access results
for symbol in results.stocks:
    print(f"{symbol.full_symbol}: {symbol.clean_description}")

# Filter by exchange or country
nse_symbols = results.filter_by_exchange("NSE")
indian_symbols = results.filter_by_country("IN")

# Get first match
symbol = client.search_first("TCS", exchange="NSE")
stock = client.search_stock("INFY", exchange="NSE")
```

#### Technical Indicators

```python
# Get all technical indicators
technicals = client.get_technicals("NSE:RELIANCE")

# Key indicators
print(f"RSI: {technicals.rsi}")
print(f"MACD Line: {technicals.macd_macd}")
print(f"MACD Signal: {technicals.macd_signal}")
print(f"ADX: {technicals.adx}")
print(f"Close: {technicals.close}")

# Recommendations
print(f"Overall: {technicals.overall_recommendation}")  # STRONG_BUY, BUY, NEUTRAL, SELL, STRONG_SELL
print(f"MA Recommendation: {technicals.ma_recommendation}")

# Moving Averages
mas = technicals.get_all_moving_averages()
print(f"SMA200: {mas['SMA200']}")
print(f"EMA50: {mas['EMA50']}")

# Pivot Levels
pivots = technicals.get_classic_pivot_levels()
print(f"Pivot: {pivots['Pivot']}")
print(f"R1: {pivots['R1']}, S1: {pivots['S1']}")

# Helper properties
print(f"Is oversold: {technicals.is_oversold}")  # RSI < 30
print(f"Is overbought: {technicals.is_overbought}")  # RSI > 70
print(f"Is trending: {technicals.is_trending}")  # ADX > 25
print(f"Is above 200 SMA: {technicals.is_above_200_sma}")
```

#### News

```python
# Get news for a symbol
news = client.get_news("NSE:RELIANCE")

for item in news.items:
    print(f"Title: {item.title}")
    print(f"Provider: {item.provider_name}")
    print(f"Published: {item.published_datetime}")
    print(f"Link: {item.link}")
    
# Filter news
reuters_news = news.filter_by_provider("reuters")
exclusive_news = news.filter_exclusive()

# Get all symbols mentioned in news
all_symbols = news.get_all_symbols()
```

#### Convenience Methods

```python
# Get complete symbol overview
overview = client.get_symbol_overview("RELIANCE", exchange="NSE")
print(f"Symbol: {overview['symbol'].full_symbol}")
print(f"Price: {overview['technicals'].close}")
print(f"News count: {len(overview['news'].items)}")

# Get symbol with technicals in one call
result = client.get_symbol_with_technicals("TCS", exchange="NSE")
if result:
    symbol, technicals = result
    print(f"{symbol.clean_description}: RSI={technicals.rsi}")

# Get just the recommendation
rec = client.get_recommendation("NSE:RELIANCE")
print(f"Recommendation: {rec}")

# Get moving averages
mas = client.get_moving_averages("NSE:RELIANCE")

# Get pivot levels
pivots = client.get_pivot_levels("NSE:RELIANCE")
```

## Data Models

### Symbol

```python
symbol = results.first_stock

# Properties
symbol.symbol          # "RELIANCE"
symbol.exchange        # "NSE"
symbol.full_symbol     # "NSE:RELIANCE"
symbol.description     # Company name (may contain HTML)
symbol.clean_description  # Company name without HTML
symbol.isin            # "INE002A01018"
symbol.currency_code   # "INR"
symbol.country         # "IN"
symbol.type            # "stock"
symbol.is_stock        # True
symbol.is_primary_listing  # True
symbol.get_logo_url()  # URL to symbol's logo
```

### TechnicalIndicators

```python
technicals = client.get_technicals("NSE:RELIANCE")

# Recommendations (-1 to 1)
technicals.recommend_all    # Overall
technicals.recommend_ma     # Moving Averages
technicals.recommend_other  # Other indicators

# Oscillators
technicals.rsi              # Relative Strength Index
technicals.macd_macd        # MACD line
technicals.macd_signal      # MACD signal
technicals.stoch_k          # Stochastic %K
technicals.stoch_d          # Stochastic %D
technicals.cci20            # CCI (20)
technicals.adx              # ADX
technicals.williams_r       # Williams %R
technicals.uo               # Ultimate Oscillator
technicals.mom              # Momentum

# Moving Averages
technicals.ema10, technicals.ema20, technicals.ema50, technicals.ema100, technicals.ema200
technicals.sma10, technicals.sma20, technicals.sma50, technicals.sma100, technicals.sma200
technicals.vwma             # Volume Weighted MA
technicals.hull_ma9         # Hull MA

# Pivot Points
technicals.pivot_m_classic_middle  # Monthly Classic Pivot
technicals.pivot_m_classic_r1      # Resistance 1
technicals.pivot_m_classic_s1      # Support 1
# Also: Fibonacci, Camarilla, Woodie, DeMark pivots
```

### NewsItem

```python
news = client.get_news("NSE:RELIANCE")
item = news.items[0]

item.id                 # Unique ID
item.title              # Headline
item.published          # Unix timestamp
item.published_datetime # Python datetime
item.published_date     # "2024-01-10"
item.link               # External URL (if available)
item.story_path         # TradingView story path
item.provider_name      # "Reuters", "TradingView", etc.
item.is_exclusive       # Exclusive content flag
item.related_symbols    # List of mentioned symbols
```

## API Endpoints Used

The SDK uses these TradingView public endpoints:

| Service | Base URL | Purpose |
|---------|----------|---------|
| Symbol Search | `https://symbol-search.tradingview.com` | Search for symbols |
| News | `https://news-mediator.tradingview.com` | Get news for symbols |
| Scanner | `https://scanner.tradingview.com` | Technical indicators |
| Logos | `https://s3-symbol-logo.tradingview.com` | Symbol logos |

## Error Handling

```python
from tools.tradingview import (
    TradingViewClient,
    TradingViewError,
    TradingViewValidationError,
    TradingViewNotFoundError,
    TradingViewConnectionError,
)

client = TradingViewClient()

try:
    technicals = client.get_technicals("NSE:RELIANCE")
except TradingViewValidationError as e:
    print(f"Invalid input: {e}")
except TradingViewConnectionError as e:
    print(f"Connection failed: {e}")
except TradingViewError as e:
    print(f"API error: {e}")
```

## Context Manager

```python
with TradingViewClient() as client:
    results = client.search_symbol("RELIANCE")
    technicals = client.get_technicals("NSE:RELIANCE")
    # Client automatically closed when exiting context
```

## Examples

### Get Complete Stock Analysis

```python
from tools.tradingview import TradingViewClient

client = TradingViewClient()

# Search and analyze
symbol = client.search_stock("RELIANCE", exchange="NSE")
if symbol:
    full_symbol = symbol.full_symbol
    
    # Technical analysis
    tech = client.get_technicals(full_symbol)
    
    print(f"=== {symbol.clean_description} ({full_symbol}) ===")
    print(f"Price: ₹{tech.close:,.2f}")
    print(f"RSI: {tech.rsi:.2f}")
    print(f"MACD: {tech.macd_macd:.2f}")
    print(f"Recommendation: {tech.overall_recommendation.value}")
    print(f"Above 200 SMA: {tech.is_above_200_sma}")
    
    # Support/Resistance
    support = tech.get_nearest_support()
    resistance = tech.get_nearest_resistance()
    print(f"Nearest Support: ₹{support:,.2f}" if support else "")
    print(f"Nearest Resistance: ₹{resistance:,.2f}" if resistance else "")
```

### Monitor Multiple Stocks

```python
from tools.tradingview import TradingViewClient

client = TradingViewClient()

watchlist = ["NSE:RELIANCE", "NSE:TCS", "NSE:INFY", "NSE:HDFCBANK"]

for symbol in watchlist:
    tech = client.get_technicals(symbol)
    rec = tech.overall_recommendation.value
    print(f"{symbol}: ₹{tech.close:,.2f} | RSI: {tech.rsi:.1f} | {rec}")
```

### Get Latest News Summary

```python
from tools.tradingview import TradingViewClient

client = TradingViewClient()

news = client.get_news("NSE:RELIANCE")
print(f"Found {len(news.items)} news items\n")

for item in news.items[:10]:
    print(f"[{item.published_date}] {item.title}")
    print(f"  Source: {item.provider_name}")
    if item.link:
        print(f"  Link: {item.link}")
    print()
```

## Notes

- No authentication is required for these public APIs
- Rate limits may apply; add delays for bulk requests
- Data is provided as-is from TradingView
- Symbol format must include exchange (e.g., "NSE:RELIANCE", not just "RELIANCE")

## License

This SDK is for educational and personal use. Please respect TradingView's terms of service.