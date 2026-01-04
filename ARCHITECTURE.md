# Hagrid AI Architecture

## 1. High‑Level Concept
Hagrid AI is a multi‑agent algorithmic trading platform for Indian equities (NIFTY 100) that:
- **Daily Stock Selection**: Analyzes all NIFTY 100 stocks daily to identify 10-15 best opportunities.
- **Dual-Direction Trading**: Takes both LONG and SHORT positions based on analysis.
- **Target**: 1% movement per stock, targeting 5% daily portfolio return (with 5x intraday leverage).
- **Risk Management**: Uses parallel agent validation, stop-loss, and take-profit mechanisms.
- **Multi-Agent Analysis**: 12+ specialized agents analyze each stock across multiple dimensions.

## 2. Daily Workflow
**Morning (Pre-Market):**
1. Regime Detection: Check VIX, market sentiment
2. Stock Screening: All 12 agents analyze each NIFTY 100 stock in parallel
3. Signal Aggregation: Combine scores from all agents (run 2x for validation)
4. Stock Selection: Pick top 10-15 stocks with highest conviction (run 2x for validation)
5. Position Sizing: Calculate quantities based on risk parameters
6. Staging: Present picks to user for review

**Intraday:**
1. Execution: Place orders as market opens
2. Monitoring: Track positions, P&L, market conditions
3. Adjustment: Position Adjustment Agent manages stops/targets dynamically
4. Exit: Close positions as targets hit or end of day approaches

## 3. Agent Strategy
Each of the 12 departments analyzes every stock:
- **Parallel Execution**: For critical analyses, 2 agents run same task independently
- **Consensus Building**: Results consolidated only if both agents agree
- **Scoring**: Each agent provides score (-3 to +3) and reasoning
- **Final Selection**: Aggregator picks 10-15 stocks based on combined scores

## 4. System Architecture
### 4.1 Component View
```text
                      ┌─────────────────────────────┐
                      │         Next.js UI          │
                      │  (Dashboard & Control)      │
                      └─────────────┬───────────────┘
                                    │ HTTPS / WebSocket
                                    ▼
                       ┌──────────────────────────┐
                       │    FastAPI Gateway       │
                       │  /analysis (chat)        │
                       │  /staging (daily picks)  │
                       │  /marketwatch            │
                       │  /positions              │
                       │  /funds                  │
                       │  /news                   │
                       └─────────────┬───────────┘
─────────────────────────────────────┼────────────────────────────────
BACKEND (Python + Agno)
                                     │
           ┌─────────────────────────┴─────────────────────────┐
           │                                                   │
┌──────────────────────┐                            ┌──────────────────────┐
│  Market Data Service │◄───────────────►Cache     │  Execution Service   │
│ (NSE, VIX, F&O)      │                            │ (Broker: Fyers/etc.) │
└──────────────────────┘                            └──────────────────────┘
           │  
           ▼
┌────────────────────────────────────────────────────────────┐
│  AGENT ORCHESTRATOR (Agno Workflows)                       │
│  - Analyzes all NIFTY 100 stocks daily                     │
│  - Runs parallel agent teams                               │
│  - Consensus-based stock selection                         │
└────────────────────────────────────────────────────────────┘
   │             │              │                  │
   ▼             ▼              ▼                  ▼
 Dept 1–4    Dept 5–8       Dept 9–12        Meta Agents
 (Signals)   (Context)      (Regimes etc.)   (Agg, Risk, Exec)

Storage:
┌────────────────────────────────┐
│  SQLite (MVP)                  │
│  - Daily picks & analysis      │
│  - Position history            │
│  - Agent decisions & reasoning │
└────────────────────────────────┘
```

## 5. Stock Selection Process
**Input**: NIFTY 100 stocks
**Output**: 10-15 stocks with direction (LONG/SHORT), entry, SL, TP

**Process**:
1. **Filter**: Regime check (halt if CRISIS)
2. **Analyze**: Each stock scored by all 12 agents
3. **Aggregate**: Combine scores (weighted by regime)
4. **Validate**: Run aggregation 2x, pick consensus
5. **Select**: Top 10-15 with highest conviction
6. **Size**: Calculate quantities (risk-based)
7. **Stage**: Present to user for approval

## 6. Target & Risk
- **Per-Stock Target**: 1% price movement
- **Portfolio Target**: 5% daily (with 5x intraday leverage)
- **Risk Control**: Never negative - both LONG & SHORT positions
- **Stop Loss**: Mandatory for each position
- **Position Adjustment**: Dynamic trailing stops for profit maximization

## 7. API Endpoints (Frontend Integration)
- `/analysis` - Chat interface with agents (WebSocket)
- `/staging` - View daily stock picks (supports date query)
- `/marketwatch` - Real-time symbol prices & changes
- `/positions` - Current open positions
- `/funds` - Account balance & transactions
- `/news` - Latest market news
- `/run-cycle` - Trigger stock analysis workflow
- `/orders` - Order book & history

## 8. Tech Stack
- **Backend**: Python 3.12+, Agno, FastAPI, Uvicorn
- **Database**: SQLite (MVP) → Postgres (Production)
- **Broker**: Fyers API (mock for MVP)
- **Frontend**: Next.js, TypeScript, TailwindCSS, WebSockets