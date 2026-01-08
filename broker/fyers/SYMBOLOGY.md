# Fyers API Symbology and Data Structures

This document describes the Fyers API symbology format, exchange/segment codes, and various constants based on the official Fyers API documentation.

## Table of Contents
- [Fytoken Format](#fytoken-format)
- [Exchange and Segment Codes](#exchange-and-segment-codes)
- [Instrument Types](#instrument-types)
- [Symbology Format](#symbology-format)
- [Order and Position Constants](#order-and-position-constants)

---

## Fytoken Format

A **Fytoken** is a unique identifier for a trading symbol in the Fyers system. It consists of multiple components concatenated together:

| Component | Format | Description | Example |
|-----------|--------|-------------|---------|
| Exchange | 2 Digits | Exchange code | 10 (NSE) |
| Segment | 2 Digits | Segment code | 10 (Capital Market) |
| Expiry | 6 Digits | YYMMDD format | 200827 |
| Exchange Token | 2-6 Digits | Token assigned by exchange | 22 |

**Example Fytoken**: `10102008270000022` represents NSE Capital Market with expiry 27-Aug-2020 and exchange token 22.

---

## Exchange and Segment Codes

### Exchanges

| Code | Exchange | Description |
|------|----------|-------------|
| 10 | NSE | National Stock Exchange |
| 11 | MCX | Multi Commodity Exchange |
| 12 | BSE | Bombay Stock Exchange |

### Segments

| Code | Segment | Description |
|------|---------|-------------|
| 10 | Capital Market | Equity trading |
| 11 | Equity Derivatives | Futures & Options on equities |
| 12 | Currency Derivatives | Currency futures and options |
| 20 | Commodity Derivatives | Commodity futures and options |

### Available Exchange-Segment Combinations

| Exchange | Segment | Exchange Code | Segment Code | Example |
|----------|---------|---------------|--------------|---------|
| NSE | Capital Market | 10 | 10 | NSE:SBIN-EQ |
| NSE | Equity Derivatives | 10 | 11 | NSE:NIFTY24JANFUT |
| NSE | Currency Derivatives | 10 | 12 | NSE:USDINR24JANFUT |
| NSE | Commodity Derivatives | 10 | 20 | - |
| BSE | Capital Market | 12 | 10 | BSE:SBIN-A |
| BSE | Equity Derivatives | 12 | 11 | BSE:SENSEX24JANFUT |
| BSE | Currency Derivatives | 12 | 12 | - |
| MCX | Commodity Derivatives | 11 | 20 | MCX:CRUDEOIL24JANFUT |

---

## Instrument Types

### Capital Market (CM) Segment

| Code | Type | Description |
|------|------|-------------|
| 0 | EQ | Equity |
| 1 | PREFSHARES | Preference Shares |
| 2 | DEBENTURES | Debentures |
| 3 | WARRANTS | Warrants |
| 4 | MISC | Miscellaneous (NSE, BSE) |
| 5 | SGB | Sovereign Gold Bonds |
| 6 | G-Secs | Government Securities |
| 7 | T-Bills | Treasury Bills |
| 8 | MF | Mutual Funds |
| 9 | ETF | Exchange Traded Funds |
| 10 | INDEX | Index |
| 50 | MISC | Miscellaneous (BSE only) |

### Futures & Options (FO) Segment

| Code | Type | Description |
|------|------|-------------|
| 11 | FUTIDX | Index Futures |
| 12 | FUTIVX | Volatility Index Futures |
| 13 | FUTSTK | Stock Futures |
| 14 | OPTIDX | Index Options |
| 15 | OPTSTK | Stock Options |

### Currency Derivatives (CD) Segment

| Code | Type | Description |
|------|------|-------------|
| 16 | FUTCUR | Currency Futures |
| 17 | FUTIRT | Interest Rate Futures |
| 18 | FUTIRC | Interest Rate Currency Futures |
| 19 | OPTCUR | Currency Options |
| 20 | UNDCUR | Underlying Currency |
| 21 | UNDIRC | Underlying Interest Rate Currency |
| 22 | UNDIRT | Underlying Interest Rate |
| 23 | UNDIRD | Underlying Interest Rate Derivatives |
| 24 | INDEX_CD | Currency Index |
| 25 | FUTIRD | Interest Rate Derivatives Futures |

### Commodity (COM) Segment

| Code | Type | Description |
|------|------|-------------|
| 11 | FUTIDX | Index Futures (Commodity) |
| 30 | FUTCOM | Commodity Futures |
| 31 | OPTFUT | Options on Futures |
| 32 | OPTCOM | Commodity Options |
| 33 | FUTBAS | Commodity Futures (Basis) |
| 34 | FUTBLN | Commodity Futures (Blend) |
| 35 | FUTENR | Commodity Futures (Energy) |
| 36 | OPTBLN | Commodity Options (Blend) |
| 37 | OPTFUT | Options on Futures (NCOM) |

---

## Symbology Format

### General Format

Fyers uses a specific format for symbol representation:

```
{Exchange}:{ExchangeSymbol}-{Series/Strike/Expiry}
```

### Equity Symbols

**Format**: `{Ex}:{Ex_Symbol}-{Series}`

**Examples**:
- NSE equity: `NSE:SBIN-EQ`
- BSE equity: `BSE:SBIN-A`
- BE series (NSE): `NSE:MODIRUBBER-BE`
- T series (BSE): `BSE:MODIRUBBER-T`

### Equity Futures

**Format**: `{Ex}:{Ex_UnderlyingSymbol}{YY}{MMM}FUT`

**Examples**:
- Index futures: `NSE:NIFTY24JANFUT`
- Stock futures: `NSE:BANKNIFTY24FEBFUT`
- BSE futures: `BSE:SENSEX23AUGFUT`

### Equity Options (Monthly Expiry)

**Format**: `{Ex}:{Ex_UnderlyingSymbol}{YY}{MMM}{Strike}{Opt_Type}`

**Examples**:
- Index options: `NSE:NIFTY24JAN11000CE`
- Index put: `NSE:BANKNIFTY24FEB25000PE`
- BSE options: `BSE:SENSEX23AUG60400CE`

### Equity Options (Weekly Expiry)

**Format**: `{Ex}:{Ex_UnderlyingSymbol}{YY}{M}{dd}{Strike}{Opt_Type}`

**Note**: `{M}` is a single character representing the month:
- Jan-Sep: 1-9
- Oct: O (letter)
- Nov: N
- Dec: D

**Examples**:
- Weekly call: `NSE:NIFTY24O0811000CE` (Oct 8, 2024)
- Weekly put: `NSE:NIFTY24N1525000PE` (Nov 15, 2024)
- Weekly BSE: `BSE:SENSEX23A1661000CE` (Apr 16, 2023)
- December weekly: `NSE:NIFTY24D1025000CE` (Dec 10, 2024)

### Currency Futures

**Format**: `{Ex}:{Ex_CurrencyPair}{YY}{MMM}FUT`

**Examples**:
- USD-INR: `NSE:USDINR24JANFUT`
- GBP-INR: `NSE:GBPINR24FEBFUT`

### Currency Options (Monthly Expiry)

**Format**: `{Ex}:{Ex_CurrencyPair}{YY}{MMM}{Strike}{Opt_Type}`

**Examples**:
- USD call: `NSE:USDINR24JAN75CE`
- GBP put: `NSE:GBPINR24FEB80.5PE`

### Currency Options (Weekly Expiry)

**Format**: `{Ex}:{Ex_CurrencyPair}{YY}{M}{dd}{Strike}{Opt_Type}`

**Examples**:
- Weekly USD: `NSE:USDINR24O0875CE` (Oct 8, 2024)
- Weekly GBP: `NSE:GBPINR24N0580.5PE` (Nov 5, 2024)
- December weekly: `NSE:USDINR24D1075CE` (Dec 10, 2024)

### Commodity Futures

**Format**: `{Ex}:{Ex_Commodity}{YY}{MMM}FUT`

**Examples**:
- Crude oil: `MCX:CRUDEOIL24JANFUT`
- Gold: `MCX:GOLD24DECFUT`

### Commodity Options (Monthly Expiry)

**Format**: `{Ex}:{Ex_Commodity}{YY}{MMM}{Strike}{Opt_Type}`

**Examples**:
- Crude call: `MCX:CRUDEOIL24JAN4000CE`
- Gold put: `MCX:GOLD24DEC40000PE`

### Symbology Variables Reference

| Variable | Description | Possible Values |
|----------|-------------|-----------------|
| `{Ex}` | Exchange | NSE, BSE, MCX |
| `{YY}` | Year (2 digits) | 23, 24, 25 |
| `{MMM}` | Month (3 letters) | JAN, FEB, MAR, APR, MAY, JUN, JUL, AUG, SEP, OCT, NOV, DEC |
| `{M}` | Month (1 char) | 1-9 (Jan-Sep), O (Oct), N (Nov), D (Dec) |
| `{dd}` | Date (2 digits) | 01-31 |
| `{Opt_Type}` | Option type | CE (Call), PE (Put) |
| `{Strike}` | Strike price | Numeric (e.g., 11000, 75.5) |

---

## Order and Position Constants

### Product Types

| Code | Description | Applicable Segments |
|------|-------------|---------------------|
| CNC | Cash and Carry | Equity only |
| INTRADAY | Intraday | All segments |
| MARGIN | Margin | Derivatives only |
| CO | Cover Order | All segments |
| BO | Bracket Order | All segments |
| MTF | Margin Trading Facility | Equity only |

### Order Types

| Code | Type | Description |
|------|------|-------------|
| 1 | LIMIT | Limit order |
| 2 | MARKET | Market order |
| 3 | STOP | Stop-loss market (SL-M) |
| 4 | STOP_LIMIT | Stop-loss limit (SL-L) |

### Order Status

| Code | Status | Description |
|------|--------|-------------|
| 1 | CANCELLED | Order cancelled |
| 2 | TRADED | Order filled/traded |
| 4 | TRANSIT | Order in transit |
| 5 | REJECTED | Order rejected |
| 6 | PENDING | Order pending |
| 7 | EXPIRED | Order expired |

### Order Sides

| Code | Side | Description |
|------|------|-------------|
| 1 | BUY | Buy order |
| -1 | SELL | Sell order |

### Position Sides

| Code | Side | Description |
|------|------|-------------|
| 1 | LONG | Long position |
| -1 | SHORT | Short position |
| 0 | CLOSED | Closed position |

### Holding Types

| Code | Type | Description |
|------|------|-------------|
| T1 | T+1 | Shares purchased but not yet delivered |
| HLD | HOLDINGS | Shares available in demat account |

### Order Sources

| Code | Source | Description |
|------|--------|-------------|
| M | MOBILE | Mobile app |
| W | WEB | Web platform |
| R | FYERS_ONE | Fyers One desktop app |
| A | ADMIN | Admin |
| ITS | API | API/Third-party system |

### Order Validity

| Code | Type | Description |
|------|------|-------------|
| DAY | Day | Valid for the trading day |
| IOC | Immediate or Cancel | Execute immediately or cancel |

---

## Usage Examples

### Creating Equity Orders

```python
from broker.fyers.models import create_limit_order, OrderSide

# Buy SBIN at limit price
order = create_limit_order(
    symbol="NSE:SBIN-EQ",
    qty=10,
    side=OrderSide.BUY,
    limit_price=500.50,
    product_type="CNC"
)
```

### Creating Futures Orders

```python
# Buy NIFTY futures
order = create_market_order(
    symbol="NSE:NIFTY24JANFUT",
    qty=50,  # 1 lot = 50 qty
    side=OrderSide.BUY,
    product_type="INTRADAY"
)
```

### Creating Options Orders

```python
# Buy NIFTY call option
order = create_limit_order(
    symbol="NSE:NIFTY24JAN18000CE",
    qty=50,
    side=OrderSide.BUY,
    limit_price=150.25,
    product_type="INTRADAY"
)
```

---

## References

- Fyers API Documentation: https://docs.fyers.in/
- Symbol Search: Available through the Fyers trading platform
- Contract Notes: For exact symbol formats used in your trades
