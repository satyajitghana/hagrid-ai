# Screener.in SDK

Python client for accessing Screener.in stock fundamentals data.

## Features

- **Company Search**: Search for companies by name or symbol
- **Historical Charts**: Access price, PE, EPS, margins, and other historical data via API
- **Fundamentals Page**: Fetch company fundamentals page as markdown (suitable for LLM consumption)
- **Typed Models**: Full Pydantic models for type safety and IDE support

## Installation

The SDK is part of the hagrid-ai project. Ensure you have the following dependencies:

```bash
uv add httpx pydantic markdownify
```

## Quick Start

```python
from tools.screener import ScreenerClient

# Create client
client = ScreenerClient()

# Search for a company
results = client.search("reliance")
company = results.first
print(f"Found: {company.name} (ID: {company.id})")

# Get price chart with moving averages
chart = client.get_price_chart(company.id, days=365)
print(f"Latest price: ₹{chart.price.latest_value}")
print(f"50 DMA: ₹{chart.dma50.latest_value}")
print(f"200 DMA: ₹{chart.dma200.latest_value}")

# Get company fundamentals as markdown
markdown = client.get_company_page("RELIANCE")
print(markdown)

# Clean up
client.close()
```

## API Reference

### ScreenerClient

Main client class for interacting with Screener.in.

#### Constructor

```python
client = ScreenerClient(timeout=30.0)
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `timeout` | `float` | `30.0` | Request timeout in seconds |

### Search Methods

#### `search(query, version=3, full_text_search=True)`

Search for companies by name or symbol.

```python
results = client.search("reliance")
for company in results.companies:
    print(f"{company.name}: {company.symbol}")
```

**Returns:** `CompanySearchResponse` with list of matching companies

#### `search_first(query)`

Search and return only the first matching company.

```python
company = client.search_first("reliance industries")
if company:
    print(f"ID: {company.id}, Symbol: {company.symbol}")
```

**Returns:** `CompanySearchResult | None`

### Chart Methods

#### `get_chart(company_id, query, days=365, consolidated=True)`

Get custom chart data for a company.

```python
chart = client.get_chart(
    company_id=2726,
    query="Price-DMA50-DMA200-Volume",
    days=365
)
```

#### `get_price_chart(company_id, days=365, consolidated=True)`

Get price chart with moving averages and volume.

```python
chart = client.get_price_chart(2726, days=365)
price = chart.price  # ChartDataset
print(f"Latest: ₹{price.latest_value} on {price.latest_date}")
```

**Returns:** `ChartResponse` with Price, DMA50, DMA200, Volume datasets

#### `get_valuation_chart(company_id, days=10000, consolidated=True)`

Get PE ratio and EPS chart.

```python
chart = client.get_valuation_chart(2726)
print(f"Current PE: {chart.pe_ratio.latest_value}")
print(f"TTM EPS: {chart.eps.latest_value}")
```

**Returns:** `ChartResponse` with PE, Median PE, EPS datasets

#### `get_margin_chart(company_id, days=10000, consolidated=True)`

Get profit margin chart (GPM, OPM, NPM).

```python
chart = client.get_margin_chart(2726)
print(f"GPM: {chart.gpm.latest_value}%")
print(f"OPM: {chart.opm.latest_value}%")
print(f"NPM: {chart.npm.latest_value}%")
```

**Returns:** `ChartResponse` with GPM, OPM, NPM, Quarter Sales datasets

#### `get_market_cap_chart(company_id, days=10000, consolidated=True)`

Get market cap to sales ratio chart.

```python
chart = client.get_market_cap_chart(2726)
```

**Returns:** `ChartResponse` with Market Cap/Sales, Median, Sales datasets

### Company Page Methods

#### `get_company_page(symbol, consolidated=True)`

Fetch company fundamentals page as markdown.

```python
markdown = client.get_company_page("RELIANCE")
# Contains: About, Key Ratios, Quarterly Results, P&L, Balance Sheet, etc.
```

**Returns:** `str` - Markdown content of the company page

#### `get_company_page_raw(symbol, consolidated=True)`

Get company page as raw HTML.

```python
html = client.get_company_page_raw("TCS")
```

**Returns:** `str` - Raw HTML content

### Convenience Methods

#### `get_company_fundamentals(query)`

Search for a company and get its fundamentals page in one call.

```python
fundamentals = client.get_company_fundamentals("reliance industries")
```

#### `get_all_chart_data(company_id, days=365, consolidated=True)`

Get all chart data (price, valuation, margin) for a company.

```python
charts = client.get_all_chart_data(2726)
print(f"Price: ₹{charts['price'].price.latest_value}")
print(f"PE: {charts['valuation'].pe_ratio.latest_value}")
print(f"OPM: {charts['margin'].opm.latest_value}%")
```

#### `get_company_summary(query, price_days=365)`

Get a complete summary combining search, charts, and fundamentals.

```python
summary = client.get_company_summary("reliance")
print(f"Company: {summary['company'].name}")
print(f"PE: {summary['charts']['valuation'].pe_ratio.latest_value}")
print(summary['fundamentals_markdown'][:500])
```

## Models

### CompanySearchResult

```python
class CompanySearchResult:
    id: int | None        # Company ID in Screener database
    name: str             # Company name
    url: str              # URL path to company page
    
    # Properties
    symbol: str | None    # Stock symbol extracted from URL
    is_consolidated: bool # Whether consolidated view
```

### ChartDataset

```python
class ChartDataset:
    metric: str           # Metric identifier
    label: str            # Display label
    values: list[ChartDataPoint]  # Data points
    meta: dict            # Additional metadata
    
    # Properties
    latest_value: float | None
    latest_date: date | None
```

### ChartDataPoint

```python
class ChartDataPoint:
    date: date            # Date of the data point
    value: float | None   # Value at this date
    extra: dict | None    # Additional data (e.g., delivery % for volume)
```

## Available Chart Queries

### Price Queries
- `Price-DMA50-DMA200-Volume` - Price with moving averages and volume
- `Price` - Price only
- `Price-Volume` - Price with volume

### Valuation Queries
- `Price+to+Earning-Median+PE-EPS` - PE ratio and EPS
- `Market+Cap+to+Sales-Median+Market+Cap+to+Sales-Sales` - Market cap ratio

### Margin Queries
- `GPM-OPM-NPM-Quarter+Sales` - All margin metrics

## Error Handling

```python
from tools.screener import (
    ScreenerClient,
    ScreenerError,
    ScreenerNotFoundError,
    ScreenerConnectionError,
    ScreenerRateLimitError,
)

client = ScreenerClient()

try:
    results = client.search("xyz unknown company")
    if not results.companies:
        print("No companies found")
        
except ScreenerNotFoundError as e:
    print(f"Not found: {e}")
    
except ScreenerRateLimitError as e:
    print(f"Rate limited. Retry after: {e.retry_after}s")
    
except ScreenerConnectionError as e:
    print(f"Connection failed: {e}")
    
except ScreenerError as e:
    print(f"General error: {e}")
```

## Context Manager

```python
with ScreenerClient() as client:
    results = client.search("reliance")
    # Client automatically closed when exiting context
```

## API Endpoints

The SDK uses these Screener.in endpoints:

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/company/search/` | GET | Search companies |
| `/api/company/{id}/chart/` | GET | Historical chart data |
| `/company/{symbol}/` | GET | Company page (HTML) |
| `/company/{symbol}/consolidated/` | GET | Consolidated company page |

## Rate Limiting

Screener.in has rate limits in place. The SDK will raise `ScreenerRateLimitError` if exceeded. Consider adding delays between requests:

```python
import time

for symbol in symbols:
    data = client.get_company_page(symbol)
    time.sleep(1)  # Wait 1 second between requests
```

## Use Cases

### For LLM Analysis

```python
# Get company fundamentals as markdown for LLM analysis
markdown = client.get_company_page("RELIANCE")

# Pass to LLM
response = llm.chat(f"""
Analyze this company's fundamentals:

{markdown}

Key questions:
1. What is the company's business model?
2. How are the margins trending?
3. Is the valuation reasonable?
""")
```

### For Data Analysis

```python
import pandas as pd

# Get historical PE data
chart = client.get_valuation_chart(2726)
pe_data = chart.pe_ratio

# Convert to DataFrame
df = pd.DataFrame([
    {"date": p.date, "pe": p.value}
    for p in pe_data.values
])
df.set_index("date", inplace=True)

# Analyze
print(f"Mean PE: {df['pe'].mean():.2f}")
print(f"Current PE: {df['pe'].iloc[-1]:.2f}")
```

## License

Part of the hagrid-ai project.