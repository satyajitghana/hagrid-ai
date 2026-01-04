# Hagrid AI - Complete Information Flow Documentation

This document explains how information flows through the entire Hagrid AI system, from data collection to order execution.

## System Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                        HAGRID AI TRADING SYSTEM                      │
└─────────────────────────────────────────────────────────────────────┘

┌────────────────┐         ┌────────────────────────────────────────┐
│  Mock Broker   │◄────────┤          BrokerToolkit                 │
│  (Data Source) │         │  • get_quotes()                        │
└────────────────┘         │  • get_market_depth()                  │
                           │  • get_historical_data()                │
                           │  • get_option_chain()                   │
                           │  • place_order()                        │
                           │  • get_positions()                      │
                           │  • calculate_margin()                   │
                           └────────────────────────────────────────┘
                                            │
                                            ▼
┌─────────────────────────────────────────────────────────────────────┐
│                     INTRADAY WORKFLOW (5 Steps)                      │
├─────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  Step 1: REGIME CHECK                                                │
│  ├─ Regime Agent → Checks VIX, determines if trading allowed        │
│  └─ Output: GO/CAUTION/HALT decision                                │
│                                                                       │
│  Step 2: MULTI-AGENT ANALYSIS (Research Team - 12 Agents Parallel)  │
│  ├─ Technical Agent → Price action, indicators, setups              │
│  ├─ Options Agent → Options positioning, PCR, max pain              │
│  ├─ Fundamentals Agent → Company quality, earnings, valuation       │
│  ├─ Sector Agent → Sector rotation, relative strength               │
│  ├─ Microstructure Agent → Order book, liquidity, execution hints   │
│  ├─ Macro Agent → Global markets, currency, commodities             │
│  ├─ Institutional Agent → FII/DII flows, bulk deals                 │
│  ├─ News Agent → Breaking news, sentiment analysis                  │
│  ├─ Events Agent → Corporate actions, earnings calendar             │
│  ├─ Correlation Agent → Pairs trading opportunities                 │
│  └─ Position Agent → Manage existing open positions                 │
│  └─ Output: 12 sets of scores/signals for each stock                │
│                                                                       │
│  Step 3: SIGNAL AGGREGATION                                         │
│  ├─ Aggregator Agent → Combines all 12 agent signals               │
│  └─ Output: Top 10-15 stocks with composite scores                  │
│                                                                       │
│  Step 4: RISK MANAGEMENT                                            │
│  ├─ Risk Agent → Position sizing, margin checks, risk limits       │
│  └─ Output: Approved orders with exact quantities                   │
│                                                                       │
│  Step 5: EXECUTION                                                  │
│  ├─ Execution Agent → Places orders via broker                     │
│  └─ Output: Order confirmations, fill status                        │
│                                                                       │
└─────────────────────────────────────────────────────────────────────┘
```

## Detailed Information Flow

### 1. DATA COLLECTION (MockBroker → BrokerToolkit)

**Mock Broker Provides:**
- Real-time quotes (LTP, volume, bid-ask)
- Market depth (5-level order book)
- Historical OHLCV data (multiple timeframes)
- Options chain data (strikes, OI, Greeks)
- Position tracking
- Margin calculations

**BrokerToolkit Converts:**
- JSON responses → CSV-like formatted strings
- Makes data LLM-friendly for agent consumption
- Handles async broker API calls

### 2. STEP 1: REGIME CHECK

**Flow:**
```
User Trigger (POST /run-cycle) → Workflow Start → Regime Agent
                                                     ↓
                                      get_quotes(VIX) via BrokerToolkit
                                                     ↓
                                      get_market_regime(vix_value) via TradingToolkit
                                                     ↓
                                      Decision: GO/CAUTION/HALT
                                                     ↓
                                      If HALT → Stop entire workflow
                                      If GO/CAUTION → Proceed to Step 2
```

**Regime Agent Decision:**
- VIX < 12: CALM → Position multiplier 1.5x
- VIX 12-20: NORMAL → Position multiplier 1.0x
- VIX 20-30: ELEVATED → Position multiplier 0.7x
- VIX > 30: CRISIS → HALT (no trading)

### 3. STEP 2: MULTI-AGENT ANALYSIS (Research Team)

All 12 agents run **IN PARALLEL** analyzing the same NIFTY 100 stock list.

#### Agent-by-Agent Breakdown:

**A. Technical Agent**
- **Tools Used:** get_historical_data(), get_quotes(), get_market_depth(), calculate_sma_signal()
- **Analysis:** 200-day candles, 15-min candles, calculates SMA, MACD, RSI, Bollinger Bands, ATR, Volume
- **Output:** Score ±3, entry/exit levels, setup type (breakout/breakdown/mean-reversion)
- **Key Question:** Is there a clear technical setup for 1%+ move?

**B. Options Agent**
- **Tools Used:** get_option_chain(), get_quotes()
- **Analysis:** PCR, max Call/Put OI, implied volatility rank, max pain, Greeks
- **Output:** Score ±3, sentiment (bullish/bearish), key strikes, price targets
- **Key Question:** What does options positioning suggest about price direction?

**C. Fundamentals Agent**
- **Tools Used:** get_quotes() (for current price context)
- **Analysis:** Quarterly results, PE/PB ratios, ROE, debt, earnings momentum, valuation vs peers
- **Output:** Score ±1, bias (positive/neutral/negative), favor longs/shorts
- **Key Question:** Is the company fundamentally strong or weak?

**D. Sector Agent**
- **Tools Used:** get_quotes() (sector indices), get_historical_data() (sector trends)
- **Analysis:** Sector index performance vs NIFTY, relative strength, volume, momentum
- **Output:** Score ±2, sector trend (leading/lagging), favor/avoid stocks from sector
- **Key Question:** Which sectors are showing strength/weakness?

**E. Microstructure Agent**
- **Tools Used:** get_market_depth(), get_quotes(), get_historical_data() (1-min)
- **Analysis:** Bid-ask spread, order book imbalance, VWAP, tick analysis, liquidity assessment
- **Output:** Score ±3, order flow (buying/selling), execution guidance, slippage risk
- **Key Question:** Is there buying or selling pressure right now?

**F. Macro Agent**
- **Tools Used:** get_quotes() (global indices, FX, commodities), get_historical_data()
- **Analysis:** S&P 500, Nasdaq, USDINR, crude oil, gold, global VIX
- **Output:** Score ±1, risk sentiment (risk-on/risk-off), sector implications
- **Key Question:** What's the global macro backdrop?

**G. Institutional Agent**
- **Tools Used:** get_quotes() (for price context), provided FII/DII data
- **Analysis:** FII/DII net flows, bulk deals, block trades, holding patterns
- **Output:** Score ±2, flow trend (accumulation/distribution), institution activity
- **Key Question:** Are institutions buying or selling this stock?

**H. News Agent**
- **Tools Used:** get_quotes(), external news APIs (provided data)
- **Analysis:** Breaking news, corporate announcements, sentiment analysis, broker ratings
- **Output:** Score ±3, sentiment (bullish/bearish), news impact assessment
- **Key Question:** Is there any material news affecting this stock?

**I. Events Agent**
- **Tools Used:** get_quotes(), corporate calendar data (provided)
- **Analysis:** Earnings calendar, dividend dates, buybacks, splits, AGMs
- **Output:** Score ±2, event type, expected impact, trading strategy
- **Key Question:** Are there upcoming events creating opportunities?

**J. Correlation Agent**
- **Tools Used:** get_historical_data() (pairs), get_quotes() (current prices)
- **Analysis:** Correlation coefficients, cointegration, spread analysis, Z-scores
- **Output:** Score ±2, pairs trade setup (long A/short B), hedge ratios
- **Key Question:** Are there pairs trading opportunities (diverged pairs)?

**K. Position Agent** (for existing positions only)
- **Tools Used:** get_positions(), get_quotes(), get_market_depth(), get_historical_data()
- **Analysis:** Current P&L, trailing stops, partial exits, time-based management
- **Output:** HOLD/ADJUST_SL/ADJUST_TP/PARTIAL_EXIT/FULL_EXIT recommendations
- **Key Question:** How should we manage existing open positions?

**Result of Step 2:**
Each of 100 stocks now has:
- 12 different scores from 12 agents
- Multiple perspectives on each stock
- Comprehensive analysis covering technical, fundamental, flow, news, events, etc.

### 4. STEP 3: SIGNAL AGGREGATION

**Flow:**
```
All 12 agent outputs → Aggregator Agent
                            ↓
         Weight scores by market regime
                            ↓
         Calculate composite score for each stock
                            ↓
         Rank stocks by absolute composite score
                            ↓
         Select top 5-8 LONG candidates (highest positive)
         Select top 5-7 SHORT candidates (lowest negative)
                            ↓
         Validate: sector diversity, liquidity, 1% target potential
                            ↓
         Output: 10-15 final stock recommendations
```

**Aggregation Logic:**
- **Regime-Based Weighting:**
  - CALM: Technical 30%, Options 25%, Microstructure 20%, Others 25%
  - NORMAL: Technical 25%, Options 20%, Fundamentals 15%, News 15%, Others 25%
  - ELEVATED: Options 30%, Technical 25%, Risk factors 45%

- **Composite Score Calculation:**
  ```
  Composite = Σ (Agent_Score × Weight)
  Bonus for signal confluence (multiple agents agree)
  Penalty for conflicting signals
  ```

- **Stock Selection Criteria:**
  - Minimum absolute composite score: ±2.0
  - Minimum confidence: 0.70
  - Minimum daily volume: 500,000 shares
  - Clear entry/exit levels
  - Balanced long/short exposure

**Aggregator Output:**
- 10-15 stocks with:
  - Direction (LONG/SHORT)
  - Composite score
  - Confidence level
  - Entry range
  - Stop loss
  - Target (1%+ move)
  - Key reasons (top 3 supporting signals)

### 5. STEP 4: RISK MANAGEMENT

**Flow:**
```
10-15 trade candidates → Risk Agent
                            ↓
            get_positions() - Check existing positions
            calculate_margin() - Check margin availability
                            ↓
            Position Sizing for each trade:
            Risk per trade = ₹500 (0.5% of ₹100k capital)
            Quantity = Risk Amount / Stop Loss Distance
                            ↓
            Risk Checks:
            - Total risk < ₹2,000 (daily limit)
            - Margin available > margin required
            - No duplicate symbols
            - Sector exposure < 30%
            - Risk-reward ratio > 1.5:1
                            ↓
            Reject trades that fail checks
            Approve trades that pass
                            ↓
            Output: Approved orders with exact quantities
```

**Risk Agent Calculations:**
Example:
```
Stock: NSE:INFY-EQ
Entry: ₹1500
Stop Loss: ₹1485 (distance = ₹15)
Risk per trade: ₹500
Quantity = 500 / 15 = 33 shares

Margin Check:
Required margin = 33 × ₹1500 × 20% = ₹9,900
Available margin = ₹500,000 (5x leverage on ₹100k)
✓ Sufficient margin

Total Risk Check:
If approving 10 trades, total risk = 10 × ₹500 = ₹5,000
But daily limit is ₹2,000
So Risk Agent will approve only 4 trades to stay within limit
```

**Risk Agent Output:**
- Approved trades (X out of 10-15)
- Rejected trades with reasons
- Portfolio risk metrics
- Margin utilization

### 6. STEP 5: EXECUTION

**Flow:**
```
Approved orders → Execution Agent
                        ↓
        get_quotes() - Verify current prices
        get_market_depth() - Check liquidity
                        ↓
        For each order:
            place_order() - Entry order (LIMIT/MARKET)
                ↓
            Wait for fill confirmation
                ↓
            place_order() - SL order (GTT)
            place_order() - TP order (GTT)
                ↓
        get_positions() - Verify all orders placed
                        ↓
        Output: Execution status, order IDs, slippage
```

**Execution Agent Logic:**
- **Order Type Selection:**
  - High liquidity + neutral flow: LIMIT at bid/ask
  - High liquidity + momentum: LIMIT at ask (LONG) or MARKET
  - Low liquidity: Always LIMIT (avoid slippage)

- **Slippage Tracking:**
  - Target: < 0.1% for liquid NIFTY 100 stocks
  - Actual: (Fill Price - Intended Price) / Intended Price

- **Error Handling:**
  - Order rejected: Log reason, notify Risk Agent
  - Partial fill: Wait 30s, then cancel or keep
  - Insufficient margin: Report immediately

**Execution Agent Output:**
- Order confirmations with IDs
- Fill prices and slippage
- SL/TP order IDs
- Execution quality metrics

### 7. POSITION UPDATES (Continuous)

Once orders are filled, Position Agent monitors:

```
Every 5 minutes (or price trigger):
    get_positions() - Check all open positions
    get_quotes() - Current prices
                    ↓
    For each position:
        Calculate current P&L
        Check if SL/TP hit
        Evaluate trailing stop criteria
                    ↓
    Recommendations:
        - Trail SL for +2% profit positions
        - Book partial profits at +3%
        - Tighten SLs near market close (3:15 PM)
        - Exit all positions by 3:25 PM (intraday)
```

## Data Flow Summary

```
┌──────────────────────────────────────────────────────────────────┐
│                      COMPLETE DATA FLOW                           │
└──────────────────────────────────────────────────────────────────┘

MockBroker (Data Source)
    │
    ▼
BrokerToolkit (API Wrapper)
    │
    ▼
┌─────────────────────────────────────────────┐
│              WORKFLOW START                  │
│  (User triggers via POST /run-cycle)         │
└─────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────┐
│  STEP 1: Regime Agent                       │
│  Input: VIX from broker                     │
│  Output: GO/CAUTION/HALT                    │
└─────────────────────────────────────────────┘
    │
    ▼ (if GO or CAUTION)
┌─────────────────────────────────────────────┐
│  STEP 2: Research Team (12 Agents)         │
│  Input: 100 NIFTY stocks                    │
│  Each agent analyzes all 100 stocks         │
│  Output: 12 scores per stock (1200 signals) │
└─────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────┐
│  STEP 3: Aggregator Agent                   │
│  Input: 1200 signals (12 × 100)             │
│  Process: Weight, rank, filter              │
│  Output: Top 10-15 stocks                   │
└─────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────┐
│  STEP 4: Risk Agent                         │
│  Input: 10-15 trade candidates              │
│  Process: Size positions, check limits      │
│  Output: 4-10 approved orders               │
└─────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────┐
│  STEP 5: Execution Agent                    │
│  Input: 4-10 approved orders                │
│  Process: Place orders via broker           │
│  Output: Order confirmations                │
└─────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────┐
│  CONTINUOUS: Position Agent                 │
│  Input: Open positions                      │
│  Process: Monitor, adjust SL/TP             │
│  Output: Position management actions        │
└─────────────────────────────────────────────┘
    │
    ▼
MockBroker (Order Storage & Tracking)
```

## API Integration Points

### 1. FastAPI Server (api/main.py)

**Endpoints:**
- `POST /run-cycle` → Triggers the entire workflow
- `GET /staging?date=YYYY-MM-DD` → Retrieves daily picks
- `GET /marketwatch` → Real-time quotes for watchlist
- `GET /positions` → Current open positions
- `GET /orders` → Order book
- `GET /funds` → Account balance/margins
- `POST /news` → Add news items
- `GET /news?category=stocks` → Retrieve news
- `WS /ws/analysis` → WebSocket for chat with agents
- `WS /ws/updates` → WebSocket for real-time updates

**Data Storage (SQLModel):**
- `DailyPick`: Stores daily analysis results
- `NewsItem`: Stores market news
- `UserSession`: Tracks user sessions

Agno automatically stores agent sessions and logs.

### 2. Workflow Integration

The workflow is defined in [`workflows/intraday_cycle.py`](workflows/intraday_cycle.py:1):

```python
intraday_workflow = Workflow(
    name="Intraday Trading Cycle",
    steps=[
        Step(name="Regime Check", agent=regime_agent),
        Step(name="Multi-Agent Analysis", team=research_team),
        Step(name="Signal Aggregation", agent=aggregator_agent),
        Step(name="Risk Management", agent=risk_agent),
        Step(name="Execution", agent=execution_agent)
    ]
)
```

When triggered, the workflow:
1. Executes steps sequentially
2. Passes output from one step as input to next
3. Stops if Regime Agent says HALT
4. Returns final result to API endpoint

## Error Handling & Edge Cases

### 1. Regime CRISIS
- Workflow stops at Step 1
- No stock analysis happens
- Returns: "Market in CRISIS regime, no trading today"

### 2. All Signals Neutral
- Aggregator finds no stocks meeting criteria
- Returns: "No actionable opportunities found"

### 3. Risk Agent Rejects All Trades
- Insufficient margin, or all trades fail risk checks
- Returns: "No trades approved due to risk constraints"

### 4. Execution Failures
- Some orders may be rejected by broker
- Execution Agent reports failures
- Partial execution possible (some orders fill, some don't)

### 5. Low Liquidity Stocks
- Microstructure Agent flags high slippage risk
- Execution Agent uses LIMIT orders only
- May result in partial fills or no fills

## Performance Monitoring

### Key Metrics Tracked:
1. **Agent Performance:**
   - Signal accuracy (correct directional calls)
   - Confidence calibration
   - Response time

2. **Execution Quality:**
   - Average slippage per trade
   - Fill rate (% orders filled)
   - Order placement speed

3. **Risk Metrics:**
   - Daily P&L
   - Maximum drawdown
   - Win rate
   - Average winner vs average loser

4. **System Performance:**
   - Workflow execution time
   - API response times
   - Data fetch latency

## Conclusion

The Hagrid AI system provides a comprehensive, multi-layered analysis approach:
- **12 specialized agents** each contribute unique perspectives
- **Parallel processing** for efficiency
- **Risk management** ensures capital preservation
- **Quality execution** minimizes slippage
- **Mock broker** enables safe testing before live trading

Every piece connects seamlessly: data flows from broker → agents → aggregation → risk validation → execution → back to broker, creating a complete trading loop.