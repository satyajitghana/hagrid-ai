# Cogencis SDK

Python SDK for the Cogencis Market Data API with full Pydantic typing support.

## Installation

The SDK requires `httpx` and `pydantic` as dependencies:

```bash
pip install httpx pydantic
```

## Quick Start

```python
from tools.cogencis import CogencisClient, SearchOn

# Initialize the client with your bearer token
client = CogencisClient(bearer_token="your_jwt_token")

# Search for symbols
symbols = client.symbol_lookup("reliance")
for symbol in symbols:
    print(f"{symbol.company_name}: ₹{symbol.last_price}")
    print(f"  ISIN: {symbol.isin}")

# Get corporate actions
actions = client.get_corporate_actions(symbols[0].path)
for action in actions:
    if action.is_dividend:
        print(f"Dividend: ₹{action.dividend_amount} (Ex-date: {action.ex_date_parsed})")
```

## Features

- **Type-safe**: Full Pydantic model support for all API responses
- **Intuitive API**: Clean, Pythonic interface
- **Error handling**: Custom exceptions for different error types
- **Context manager support**: Automatic resource cleanup
- **11 API endpoints** covering comprehensive market data

---

## API Reference

### CogencisClient

Main client class for interacting with the Cogencis API.

#### Initialization

```python
client = CogencisClient(
    bearer_token="your_token",  # Required: JWT bearer token
    base_url=None,              # Optional: Custom base URL
    timeout=30.0,               # Optional: Request timeout in seconds
)
```

---

### 1. Symbol Lookup

Search for symbols by name, ISIN, or symbol code:

```python
from tools.cogencis import SearchOn

# Basic search
symbols = client.symbol_lookup("reliance")

# Search by ISIN
symbols = client.symbol_lookup("INE002A01018", search_on=SearchOn.ISIN)

# Get full response with pagination
response = client.symbol_lookup_response("reliance", page_size=20)
print(f"Total: {response.total_results}")
```

**SymbolData Properties:**
- `symbol`, `isin`, `company_name`, `last_price`, `price_change`, `percent_change`
- `ticker`, `exchange`, `path`

---

### 2. News

Get news stories for specific ISINs:

```python
news = client.get_news("ine002a01018", page_size=10)
for story in news:
    print(f"{story.headline} - {story.source_name}")
```

**NewsStory Properties:**
- `headline`, `synopsis`, `source_name`, `source_link`
- `source_datetime_parsed`, `isin_list`, `sections_list`

---

### 3. Auditors

Get auditor information:

```python
auditors = client.get_auditors(symbol.path)
for a in auditors:
    print(f"{a.auditor_personnel}: {a.appointment_date}")
```

---

### 4. Key Shareholders

Get shareholding patterns with historical data:

```python
shareholders = client.get_key_shareholders(symbol.path)
for sh in shareholders:
    if sh.is_promoter and not sh.is_group:
        holding = sh.get_latest_holding()
        if holding:
            print(f"{sh.description}: {holding.percentage}%")
```

**KeyShareholder Properties:**
- `description`, `is_group`, `is_promoter`, `is_public`
- `get_latest_holding()`, `get_holding(period)`

---

### 5. Block Deals & Bulk Deals

Get block and bulk deal information:

```python
from tools.cogencis import BlockDealType

# Block deals (type=1)
block_deals = client.get_block_deals(symbol.path)

# Bulk deals (type=2)
bulk_deals = client.get_bulk_deals(symbol.path)

for deal in block_deals:
    print(f"{deal.client_name}: {deal.transaction_type}")
    print(f"  {deal.quantity:,} @ ₹{deal.weighted_avg_price}")
```

**BlockDeal Properties:**
- `client_name`, `transaction_type`, `quantity`, `weighted_avg_price`
- `date`, `date_parsed`, `is_buy`, `is_sell`, `deal_value`

---

### 6. Insider Trading

Get insider trading transactions:

```python
trades = client.get_insider_trades(symbol.path)
for trade in trades:
    print(f"{trade.acquirer_name}: {trade.transaction_type}")
    print(f"  {trade.quantity:,} shares ({trade.category})")
    print(f"  Mode: {trade.acquisition_mode}")
```

**InsiderTrade Properties:**
- `acquirer_name`, `category`, `transaction_type`, `quantity`
- `shares_before`, `percentage_before`, `shares_after`, `percentage_after`
- `acquisition_mode`, `is_buy`, `is_sell`, `is_pledge`, `is_promoter`

---

### 7. SAST (Substantial Acquisition)

Get SAST transactions:

```python
transactions = client.get_sast(symbol.path)
for txn in transactions:
    print(f"{txn.acquirer_name}: {txn.transaction_type}")
    print(f"  {txn.quantity:,} shares -> {txn.shares_post:,} post")
```

**SASTTransaction Properties:**
- `acquirer_name`, `transaction_type`, `quantity`, `shares_post`
- `acquisition_mode`, `acquisition_type`
- `is_acquisition`, `is_sale`, `date_parsed`

---

### 8. Capital History

Get capital structure changes (bonus, splits, ESOP, etc.):

```python
history = client.get_capital_history(symbol.path)
for entry in history:
    print(f"{entry.date}: {entry.event_type}")
    if entry.change_in_shares:
        print(f"  Change: {entry.change_in_shares:,.0f} shares")
```

**CapitalHistoryEntry Properties:**
- `date`, `event_type`, `current_shares`, `outstanding_shares`
- `face_value_old`, `face_value_new`, `change_in_shares`
- `is_bonus`, `is_split`, `is_esop`, `is_rights`

---

### 9. Announcements

Get company announcements:

```python
announcements = client.get_announcements(symbol.path)
for ann in announcements:
    print(f"{ann.datetime_parsed}: {ann.details}")
    if ann.has_pdf:
        print(f"  PDF: {ann.pdf_link}")
```

**Announcement Properties:**
- `datetime_str`, `datetime_parsed`, `details`, `pdf_link`
- `is_board_meeting`, `is_credit_rating`, `is_dividend`, `is_result`
- `is_investor_presentation`, `has_pdf`

---

### 10. Corporate Actions

Get corporate actions (dividends, bonus, rights, splits):

```python
actions = client.get_corporate_actions(symbol.path)
for action in actions:
    print(f"{action.purpose}")
    print(f"  Ex-date: {action.ex_date_parsed}")
    
    if action.is_dividend:
        print(f"  Dividend: ₹{action.dividend_amount}")
    elif action.is_bonus:
        print(f"  Bonus ratio: {action.bonus_ratio}")
```

**CorporateAction Properties:**
- `purpose`, `ex_date`, `ex_date_parsed`, `record_date`, `record_date_parsed`
- `face_value`, `isin`, `exchange_symbol`
- `is_dividend`, `is_bonus`, `is_rights`, `is_split`, `is_demerger`
- `dividend_amount`, `bonus_ratio`

---

### 11. Tribunal Cases

Get tribunal cases (NCLT, NCLAT, SAT, NGT, etc.):

```python
# Note: Uses ISIN instead of path
cases = client.get_tribunal_cases("ine002a01018")
for case in cases:
    print(f"{case.date}: {case.tribunal_name} ({case.tribunal_bench})")
    print(f"  {case.case_title}")
    print(f"  Order: {case.order_type}")
```

**TribunalCase Properties:**
- `date`, `date_parsed`, `tribunal_name`, `tribunal_bench`
- `order_type`, `case_type`, `case_title`, `link`
- `is_interim`, `is_final`, `is_nclt`, `is_nclat`, `is_sat`, `is_ngt`

---

### Convenience Methods

```python
# Get news directly for a company name
news = client.get_news_for_symbol("reliance industries")

# Get comprehensive company info
info = client.get_company_info("reliance")
print(f"Company: {info['symbol'].company_name}")
print(f"Promoter holding: {info['promoter_holding']}%")
```

---

### Error Handling

```python
from tools.cogencis import (
    CogencisClient,
    CogencisError,
    CogencisAPIError,
    CogencisAuthError,
    CogencisConnectionError,
    CogencisRateLimitError,
    CogencisValidationError,
)

try:
    client = CogencisClient(bearer_token="invalid")
    symbols = client.symbol_lookup("reliance")
except CogencisAuthError as e:
    print(f"Auth failed: {e}")
except CogencisRateLimitError as e:
    print(f"Rate limited. Retry after: {e.retry_after}s")
except CogencisAPIError as e:
    print(f"API error {e.status_code}: {e.response_body}")
```

---

### Context Manager

```python
with CogencisClient(bearer_token="your_token") as client:
    symbols = client.symbol_lookup("reliance")
    news = client.get_news(symbols[0].isin)
# Client automatically closed
```

---

## Folder Structure

```
tools/cogencis/
├── __init__.py              # Main exports (v0.3.0)
├── client.py                # CogencisClient with 11 API categories
├── README.md                # This file
├── core/
│   ├── __init__.py
│   ├── exceptions.py        # 6 exception types
│   └── http_client.py       # HTTP client with Bearer auth
└── models/
    ├── __init__.py
    ├── common.py            # PagingInfo, ColumnDefinition
    ├── symbol.py            # SymbolData, SearchOn
    ├── auditor.py           # AuditorData
    ├── news.py              # NewsStory
    ├── shareholder.py       # KeyShareholder, ShareholdingValue
    ├── block_deal.py        # BlockDeal, BlockDealType
    ├── insider_trading.py   # InsiderTrade
    ├── sast.py              # SASTTransaction
    ├── capital_history.py   # CapitalHistoryEntry
    ├── announcement.py      # Announcement
    ├── corporate_action.py  # CorporateAction
    └── tribunal.py          # TribunalCase
```

---

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/marketdata/symbollookup` | GET | Search for symbols |
| `/auditors` | GET | Get auditor information |
| `/web/news/stories` | GET | Get news stories |
| `/keyshareholders` | GET | Get key shareholder information |
| `/blockdeals` | GET | Get block/bulk deals (type=1/2) |
| `/insidertrading` | GET | Get insider trading information |
| `/sast` | GET | Get SAST transactions |
| `/capitalhistory` | GET | Get capital history |
| `/announcements` | GET | Get company announcements |
| `/corporateaction` | GET | Get corporate actions |
| `/tribunals` | GET | Get tribunal cases |

---

## License

Part of the hagrid-ai project.