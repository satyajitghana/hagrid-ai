# NSE India API Examples

This folder contains example scripts demonstrating how to use the NSE India client and toolkit.

## Quick Start

```python
from tools.nse_india import NSEIndiaClient, NSEIndiaToolkit, AnnouncementIndex

# Using the client directly
client = NSEIndiaClient()
announcements = client.get_announcements(AnnouncementIndex.EQUITIES)
print(f"Found {len(announcements)} announcements")
client.close()

# Using the toolkit (for AI agents)
toolkit = NSEIndiaToolkit()
result = toolkit.get_symbol_summary("RELIANCE")
print(result)
```

## Examples

### 1. Corporate Announcements (`announcements.py`)

Demonstrates fetching corporate announcements:

```python
python -m tools.nse_india.examples.announcements
```

Features:
- Fetch equity/debt announcements
- Filter by symbol and date range
- Track new (unprocessed) announcements
- Download PDF attachments

### 2. Annual Reports (`annual_reports.py`)

Demonstrates fetching annual reports:

```python
python -m tools.nse_india.examples.annual_reports
```

Features:
- Get annual report list for a company
- Download PDF/ZIP files
- Compare reports across companies

### 3. Shareholding Patterns (`shareholding.py`)

Demonstrates shareholding pattern analysis:

```python
python -m tools.nse_india.examples.shareholding
```

Features:
- Historical shareholding pattern (quarterly)
- Detailed shareholding with shareholder names
- Promoter vs public trend analysis
- Significant beneficial owners
- Institutional holders

### 4. Symbol Summary (`symbol_summary.py`)

Demonstrates comprehensive stock data:

```python
python -m tools.nse_india.examples.symbol_summary
```

Features:
- Price and trading information
- 52-week high/low
- Performance vs index
- Financials (quarterly)
- Derivatives data (for F&O stocks)
- Option chain analysis

### 5. Toolkit Usage (`toolkit_usage.py`)

Demonstrates using the toolkit for AI agents:

```python
python -m tools.nse_india.examples.toolkit_usage
```

Features:
- Basic toolkit methods
- Formatted output for LLMs
- Agno agent integration

### 6. Financial Results Comparison (`financial_results.py`)

Demonstrates quarterly financial results analysis:

```python
python -m tools.nse_india.examples.financial_results
```

Features:
- Quarterly financial comparison across periods
- Revenue, profit, EPS trends
- QoQ and YoY growth calculations
- Expense breakdown (raw materials, staff, depreciation, etc.)
- Financial ratios (debt/equity, interest coverage)
- Compare metrics across multiple companies

### 7. Option Chain Analysis (`option_chain.py`)

Demonstrates option chain data and analysis:

```python
python -m tools.nse_india.examples.option_chain
```

Features:

- Fetch option contract info (expiry dates and strikes)
- Get full option chain data with OI, IV, LTP
- Put-Call Ratio (PCR) analysis
- Max OI strikes for support/resistance levels
- ATM and near-ATM strike analysis
- ITM/OTM option breakdown
- Compare PCR across expiries
- Market sentiment analysis

### 8. Advances/Declines (`advances_declines.py`)

Demonstrates market breadth analysis:

```python
python -m tools.nse_india.examples.advances_declines
```

Features:

- Fetch advancing and declining stocks
- Market breadth statistics (advances, declines, unchanged)
- Advance/Decline ratio calculation
- Market sentiment analysis
- Top gainers and losers by % change
- Sort by traded value or volume
- Intraday breadth signals

### 9. Pre-Open Market (`pre_open.py`)

Demonstrates pre-open market data analysis:

```python
python -m tools.nse_india.examples.pre_open
```

Features:

- Fetch pre-open data for NIFTY 50, Bank NIFTY, F&O securities
- Indicative Equilibrium Price (IEP) analysis
- Gap up/down stock identification
- Order imbalance analysis (buy/sell pressure)
- Pre-open sentiment analysis
- Order book data for individual stocks
- Trading signals based on pre-open data

### 10. Index Constituents (`index_constituents.py`)

Demonstrates fetching index constituents and analysis:

```python
python -m tools.nse_india.examples.index_constituents
```

Features:

- Get master list of all available indices on NSE
- Fetch constituents of any index (NIFTY 50, Bank NIFTY, sectoral, etc.)
- Index breadth analysis (advances, declines, A/D ratio)
- Top gainers and losers within an index
- Stocks near 52-week highs/lows
- Yearly performance analysis
- Filter by industry, market cap, volume
- Check symbol membership in indices
- F&O eligible securities list

## Client API Reference

### NSEIndiaClient

```python
client = NSEIndiaClient(
    timeout=30.0,                    # HTTP timeout
    db_path="nse_announcements.db",  # SQLite for tracking
    attachments_dir="./attachments", # PDF download folder
)

# Corporate Announcements
announcements = client.get_announcements(
    index=AnnouncementIndex.EQUITIES,  # or DEBT, SME, MF, SLB
    from_date=date(2025, 1, 1),        # optional
    to_date=date(2025, 1, 18),         # optional
    symbol="RELIANCE",                  # optional
)

# New announcements only (not processed before)
new = client.get_new_announcements(AnnouncementIndex.EQUITIES)

# Process and mark as processed
processed = client.process_announcements(
    AnnouncementIndex.EQUITIES,
    download_attachments=True,
)

# Annual Reports
reports = client.get_annual_reports(symbol="RELIANCE")

# Shareholding Patterns
history = client.get_shareholding_patterns_history(symbol="RELIANCE")
detailed = client.get_latest_shareholding_details(symbol="RELIANCE")

# Comprehensive Summary Data
data = client.get_symbol_summary_data(symbol="RELIANCE")

# Individual Quote APIs
client.get_symbol_name(symbol)
client.get_metadata(symbol)
client.get_symbol_data(symbol)
client.get_shareholding_pattern(symbol)
client.get_financial_status(symbol)
client.get_yearwise_data(symbol)
client.get_corp_actions(symbol)
client.get_board_meetings(symbol)
client.get_derivatives_most_active(symbol, "C")  # C=calls, P=puts
client.get_option_chain_data(symbol, expiry_date)
client.get_index_list(symbol)

# Event Calendar
events = client.get_event_calendar(symbol)
upcoming = client.get_upcoming_events(symbol, days_ahead=90)

# Insider Trading (PIT)
plans = client.get_insider_trading_plans()  # All trading plans
response = client.get_insider_transactions(symbol)  # Transactions for symbol
buys = client.get_recent_insider_buys(symbol, limit=10)
sells = client.get_recent_insider_sells(symbol, limit=10)
promoter_txns = client.get_promoter_transactions(symbol, limit=10)

# Option Chain Data
contract_info = client.get_option_contract_info(symbol)  # Expiry dates & strikes
chain = client.get_option_chain(symbol, expiry="27-Jan-2026")  # Full option chain
analysis = client.get_option_chain_analysis(symbol, expiry)  # Analysis summary
near_month = client.get_near_month_option_chain(symbol)  # Near month data
pcr_data = client.get_option_chain_pcr(symbol)  # PCR data
max_pain = client.get_max_pain(symbol)  # Support/resistance levels

# Financial Results Comparison
comparison = client.get_financial_results_comparison(symbol)  # All quarters
trends = client.get_results_comparison_trend(symbol, num_quarters=8)  # Trend data
summary = client.get_latest_quarter_comparison(symbol)  # Latest quarter with growth

# Advances/Declines (Market Breadth)
advances = client.get_advances()  # Advancing stocks with breadth data
declines = client.get_declines()  # Declining stocks with breadth data
snapshot = client.get_market_breadth_snapshot()  # Combined advances & declines
gainers = client.get_top_gainers(limit=20)  # Top gaining stocks
losers = client.get_top_losers(limit=20)  # Top losing stocks
ad_ratio = client.get_advance_decline_ratio()  # A/D ratio and sentiment
stock_data = client.get_symbol_advance_decline_data(symbol)  # Check specific symbol

# Pre-Open Market Data
pre_open = client.get_pre_open_data("NIFTY")  # Pre-open data for index
nifty_pre = client.get_nifty_pre_open()  # NIFTY 50 pre-open
bank_pre = client.get_bank_nifty_pre_open()  # Bank NIFTY pre-open
fo_pre = client.get_fo_pre_open()  # F&O securities pre-open
pre_gainers = client.get_pre_open_gainers("NIFTY", limit=20)  # Top gainers in pre-open
pre_losers = client.get_pre_open_losers("NIFTY", limit=20)  # Top losers in pre-open
sentiment = client.get_pre_open_sentiment("NIFTY")  # Pre-open sentiment analysis
gaps = client.get_pre_open_gaps("NIFTY", min_gap_pct=1.0)  # Gap up/down stocks
symbol_pre = client.get_symbol_pre_open_data(symbol, "NIFTY")  # Specific symbol pre-open
pre_snapshot = client.get_pre_open_snapshot()  # All indices pre-open
buy_pressure = client.get_pre_open_buy_pressure("NIFTY", min_ratio=1.5)  # Buy pressure stocks
sell_pressure = client.get_pre_open_sell_pressure("NIFTY", max_ratio=0.67)  # Sell pressure stocks

# Index Constituents
master = client.get_index_master()  # All available indices on NSE
constituents = client.get_index_constituents("NIFTY 50")  # Get index constituents
nifty50 = client.get_nifty50_constituents()  # NIFTY 50 constituents
nifty_bank = client.get_nifty_bank_constituents()  # Bank NIFTY constituents
nifty_it = client.get_nifty_it_constituents()  # NIFTY IT constituents
nifty100 = client.get_nifty100_constituents()  # NIFTY 100 constituents
nifty500 = client.get_nifty500_constituents()  # NIFTY 500 constituents
symbols = client.get_index_symbols("NIFTY 50")  # List of symbols in index
gainers = client.get_index_gainers("NIFTY 50", limit=10)  # Top gainers in index
losers = client.get_index_losers("NIFTY 50", limit=10)  # Top losers in index
breadth = client.get_index_breadth("NIFTY 50")  # Index breadth analysis
near_highs = client.get_index_near_52_week_highs("NIFTY 50")  # Stocks near 52W high
near_lows = client.get_index_near_52_week_lows("NIFTY 50")  # Stocks near 52W low
top_mcap = client.get_index_top_by_market_cap("NIFTY 50", limit=10)  # Top by market cap
top_vol = client.get_index_top_by_volume("NIFTY 50", limit=10)  # Top by volume
performers = client.get_index_yearly_performers("NIFTY 50", limit=10)  # Yearly performers
is_member = client.is_symbol_in_index("RELIANCE", "NIFTY 50")  # Check index membership
stock_data = client.get_symbol_index_data("RELIANCE", "NIFTY 50")  # Get symbol data from index
fno = client.get_fno_securities()  # All F&O eligible securities
```

### NSEIndiaToolkit

For use with AI agents (returns formatted strings):

```python
toolkit = NSEIndiaToolkit()

# Announcements
toolkit.get_equity_announcements(limit=50)
toolkit.get_debt_announcements(limit=50)
toolkit.get_symbol_announcements(symbol, from_date, to_date, limit)
toolkit.get_new_announcements(index, limit)

# Reports
toolkit.get_annual_reports(symbol)

# Shareholding
toolkit.get_shareholding_patterns(symbol, limit)
toolkit.get_detailed_shareholding(symbol)

# Financial Results
toolkit.get_financial_results_comparison(symbol, num_quarters=8)

# Summary
toolkit.get_symbol_summary(symbol)
```

## Data Models

### Announcements

```python
from tools.nse_india import EquityAnnouncement, DebtAnnouncement

# EquityAnnouncement fields
ann.symbol          # "RELIANCE"
ann.company_name    # "Reliance Industries Limited"
ann.subject         # "Outcome of Board Meeting"
ann.details         # Full text
ann.broadcast_datetime  # datetime
ann.attachment_url  # PDF URL or None
ann.has_attachment  # bool
ann.unique_id       # For tracking
```

### Shareholding

```python
from tools.nse_india.models.shareholding import (
    DetailedShareholdingPattern,
    ShareholderDetail,
    BeneficialOwner,
)

# DetailedShareholdingPattern
details.symbol
details.company_name
details.period_ended
details.summary              # List[ShareholdingSummary]
details.promoter_indian      # List[ShareholderDetail]
details.promoter_foreign     # List[ShareholderDetail]
details.public_institutions  # List[ShareholderDetail]
details.beneficial_owners    # List[BeneficialOwner]
details.top_promoters        # Computed property
details.top_beneficial_owners  # Computed property

# ShareholderDetail
sh.name                  # "Srichakra Commercials LLP"
sh.entity_type           # "Promoter Group"
sh.total_shares          # 1479199658
sh.shareholding_percentage  # 11.13

# BeneficialOwner
bo.sbo_name              # "Mukesh Ambani Nita Ambani..."
bo.registered_owner_name # "Srichakra Commercials LLP"
bo.shareholding_percentage  # 10.93
bo.voting_rights_percentage # 10.93
```

## Notes

- NSE requires browser-like headers; the client handles this automatically
- Date format in API: `DD-MM-YYYY`
- The tracker database prevents reprocessing announcements
- Detailed shareholding uses `recordId` from history to fetch data
