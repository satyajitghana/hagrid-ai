# Hagrid-AI Trading Workflow System - Implementation Plan

## Overview

Implement a comprehensive multi-agent trading workflow system using **agno's native features**:

- 5 scheduled workflows with built-in session storage
- Login script for Fyers authentication
- API endpoints leveraging agno's session management
- Day-wise history via agno's workflow sessions

---

## Agno Architecture Summary

Based on the documentation, agno provides:

```python
# Workflow with automatic session storage
workflow = Workflow(
    name="My Workflow",
    db=SqliteDb(db_file="workflows.db"),  # Auto-stores all runs
    steps=[agent, team, function],
    session_state={"shared_data": []},     # Shared between steps
    add_workflow_history_to_steps=True,    # Access previous runs
    num_history_runs=5,                     # How many past runs to include
)

# Each run stores: input, output, step results, session_state
result = workflow.run(input="...", session_id="2025-01-19")
```

**Step Types:** Agent, Team, Function (`StepInput` -> `StepOutput`), Parallel, Condition, Loop, Router

**Data Access in Steps:**
- `step_input.input` - original workflow input
- `step_input.previous_step_content` - previous step output
- `step_input.additional_data` - metadata dict
- `run_context.session_state` - shared mutable state

---

## Files to Modify/Create

### Remove

- [api/main.py](api/main.py): Remove `/run-cycle` endpoint (lines 54-96)

### New Files

| File | Purpose |
| ---- | ------- |
| `scripts/login_fyers.py` | Smart Fyers login with token validation/refresh |
| `workflows/executor.py` | Execute orders from analysis |
| `workflows/monitoring.py` | 20-min position monitoring |
| `workflows/news_workflow.py` | Hourly news summarization |
| `workflows/post_trade.py` | After-market analysis |
| `scheduler/__init__.py` | Scheduler package |
| `scheduler/__main__.py` | Entry point for `python -m scheduler` |
| `scheduler/scheduler.py` | APScheduler integration |
| `scheduler/jobs.py` | Scheduled job implementations |
| `api/routes/__init__.py` | Routes package |
| `api/routes/trades.py` | Trade history endpoints |
| `api/routes/workflows.py` | Workflow session/run endpoints |
| `agents/monitoring/agent.py` | Position monitoring agent |
| `agents/monitoring/instructions.py` | Monitoring agent instructions |
| `agents/news_summarizer/agent.py` | News summarization agent |
| `agents/news_summarizer/instructions.py` | News agent instructions |
| `agents/post_trade/agent.py` | Post-trade analysis agent |
| `agents/post_trade/instructions.py` | Post-trade instructions |

### Modify

| File | Changes |
| ---- | ------- |
| [core/models.py](core/models.py) | Add `Trade` table only (agno handles workflow runs) |
| [core/config.py](core/config.py) | Add scheduler settings, target profit %, base capital |
| [api/main.py](api/main.py) | Include new route modules, remove /run-cycle |
| [workflows/intraday_cycle.py](workflows/intraday_cycle.py) | Add `db=SqliteDb()`, session_state, history |

---

## 1. Login Script (`scripts/login_fyers.py`)

```
Flow:
1. Load saved token from file
2. Call get_profile() to validate token
3. If valid -> Success (use existing token)
4. If expired -> Try refresh_access_token(refresh_token, PIN)
5. If refresh fails -> Full OAuth login via callback server
6. Store new token to file
```

**Usage:**

```bash
python scripts/login_fyers.py              # Auto (tries token -> refresh -> full)
python scripts/login_fyers.py --refresh    # Force refresh (prompts for PIN interactively)
python scripts/login_fyers.py --force      # Force full login
```

**PIN Handling:** Interactive prompt when refresh is needed (secure, no PIN stored in config)

---

## 2. Database Schema

### Using Agno's Built-in Storage

Agno automatically creates tables for workflow sessions:

```python
from agno.db.sqlite import SqliteDb

# Single DB for all workflows
workflow_db = SqliteDb(
    db_file="hagrid_workflows.db",
    session_table="workflow_sessions"  # Custom table name
)
```

Each workflow run automatically stores:

- `session_id` (use date like "2025-01-19" for day-wise access)
- `run_id` (unique per execution)
- Input, output, all step results
- Session state
- Timestamps

### Custom Trade Table Only

Add to [core/models.py](core/models.py):

```python
class Trade(SQLModel, table=True):
    """Individual trade records - not covered by agno"""
    id: Optional[int] = Field(default=None, primary_key=True)
    date: str = Field(index=True)  # YYYY-MM-DD
    symbol: str = Field(index=True)
    direction: str  # LONG or SHORT
    entry_price: float
    exit_price: Optional[float] = None
    quantity: int
    entry_time: str
    exit_time: Optional[str] = None
    stop_loss: float
    take_profit: float
    realized_pnl: Optional[float] = None
    status: str = Field(default="OPEN")  # OPEN, CLOSED, STOPPED_OUT
    order_id: Optional[str] = None
    sl_order_id: Optional[str] = None
    exit_reason: Optional[str] = None
```

---

## 3. Workflows

### 3.1 Enhanced Intraday Workflow

**File:** [workflows/intraday_cycle.py](workflows/intraday_cycle.py)

```python
from agno.workflow import Workflow, Step
from agno.workflow.parallel import Parallel
from agno.workflow.types import StepInput, StepOutput
from agno.db.sqlite import SqliteDb
from datetime import date

# Shared database
workflow_db = SqliteDb(db_file="hagrid_workflows.db")

def prepare_analysis_input(step_input: StepInput) -> StepOutput:
    """Prepare NIFTY 100 symbols for analysis"""
    symbols = get_nifty100_symbols()  # From config or API
    return StepOutput(
        content=f"Analyze these symbols: {', '.join(symbols)}. Target: 15 stocks (mix LONG/SHORT), 5% daily return."
    )

def aggregate_and_select(step_input: StepInput) -> StepOutput:
    """Select 15 stocks from research team output"""
    research_results = step_input.previous_step_content
    # Parse and select top 15 stocks
    # Return structured selection with entry/SL/TP levels
    return StepOutput(content=selected_picks_json)

intraday_workflow = Workflow(
    name="Intraday Analysis",
    db=workflow_db,
    session_state={
        "picks": [],
        "regime": None,
        "news_context": None
    },
    add_workflow_history_to_steps=True,  # Access past runs
    num_history_runs=5,  # Last 5 trading days
    steps=[
        Step(name="Regime Check", agent=regime_agent),
        Step(name="Research", team=research_team),  # 12 agents in parallel
        Step(name="Aggregation", agent=aggregator_agent),
        Step(name="Risk Validation", agent=risk_agent),
    ]
)

# Run with date-based session_id for day-wise access
result = intraday_workflow.run(
    input="Morning analysis",
    session_id=date.today().isoformat()  # "2025-01-19"
)
```

### 3.2 Executor Workflow

**File:** `workflows/executor.py`

```python
from agno.workflow import Workflow, Step
from agno.workflow.types import StepInput, StepOutput, RunContext

def load_todays_picks(step_input: StepInput, run_context: RunContext) -> StepOutput:
    """Load picks from intraday workflow session"""
    today = date.today().isoformat()
    # Access intraday_workflow session
    session = intraday_workflow.get_session(session_id=today)
    picks = session.session_data.get("picks", [])
    run_context.session_state["picks"] = picks
    return StepOutput(content=f"Loaded {len(picks)} picks for execution")

def store_trades(step_input: StepInput, run_context: RunContext) -> StepOutput:
    """Store executed trades to Trade table"""
    executed = run_context.session_state.get("executed", [])
    with Session(engine) as db:
        for trade in executed:
            db.add(Trade(**trade))
        db.commit()
    return StepOutput(content=f"Stored {len(executed)} trades")

executor_workflow = Workflow(
    name="Order Executor",
    db=workflow_db,
    session_state={"picks": [], "executed": []},
    steps=[
        load_todays_picks,
        Step(name="Execute Orders", agent=execution_agent),
        store_trades,
    ]
)
```

### 3.3 Monitoring Workflow

**File:** `workflows/monitoring.py`

```python
from agno.workflow import Workflow, Step, Loop
from agno.workflow.types import StepInput, StepOutput, RunContext

def load_open_positions(step_input: StepInput, run_context: RunContext) -> StepOutput:
    """Load open trades from Trade table + broker"""
    with Session(engine) as db:
        trades = db.exec(select(Trade).where(
            Trade.date == date.today().isoformat(),
            Trade.status == "OPEN"
        )).all()

    # Also get latest news summary from news workflow
    news_session = news_workflow.get_session(session_id=date.today().isoformat())

    run_context.session_state["open_trades"] = [t.model_dump() for t in trades]
    run_context.session_state["news_context"] = news_session.session_data if news_session else {}

    return StepOutput(content=f"Monitoring {len(trades)} open positions")

monitoring_workflow = Workflow(
    name="Position Monitor",
    db=workflow_db,
    session_state={
        "open_trades": [],
        "news_context": {},
        "adjustments": []
    },
    steps=[
        load_open_positions,
        Step(name="Analyze Positions", agent=monitoring_agent),
        Step(name="Execute Adjustments", agent=monitoring_agent),
        # Update Trade table with results
    ]
)
```

**Monitoring Agent Constraints:**

- **NO new positions** - only modify or close existing
- Track cumulative P&L toward 5% target
- **Never let P&L go negative** (close losers early)
- **ATR-based dynamic trailing stops** (1.5-2x ATR for SL distance)
- Trail SL for winners
- Close losers proactively when momentum reverses

### 3.4 News Workflow

**File:** `workflows/news_workflow.py`

```python
news_workflow = Workflow(
    name="News Summarizer",
    db=workflow_db,
    session_state={
        "key_events": [],
        "sentiment": "NEUTRAL",
        "affected_symbols": []
    },
    steps=[
        Step(name="Fetch News", agent=news_agent),
        Step(name="Analyze Impact", agent=news_agent),
    ]
)

# Run hourly with hour-based session for aggregation
result = news_workflow.run(
    input="Summarize market news for the past hour",
    session_id=f"{date.today().isoformat()}"  # Append to same day's session
)
```

### 3.5 Post-Trade Analysis Workflow

**File:** `workflows/post_trade.py`

```python
def load_all_day_data(step_input: StepInput, run_context: RunContext) -> StepOutput:
    """Load all workflow sessions and trades for today"""
    today = date.today().isoformat()

    # Get intraday analysis session
    intraday_session = intraday_workflow.get_session(session_id=today)

    # Get all trades
    with Session(engine) as db:
        trades = db.exec(select(Trade).where(Trade.date == today)).all()

    run_context.session_state["predictions"] = intraday_session.runs if intraday_session else []
    run_context.session_state["trades"] = [t.model_dump() for t in trades]

    return StepOutput(content=f"Loaded {len(trades)} trades for analysis")

post_trade_workflow = Workflow(
    name="Post-Trade Analysis",
    db=workflow_db,
    add_workflow_history_to_steps=True,  # Access past analyses
    num_history_runs=20,  # Last 20 trading days
    session_state={
        "predictions": [],
        "trades": [],
        "report": ""
    },
    steps=[
        load_all_day_data,
        Step(name="Analyze Performance", agent=post_trade_agent),
        Step(name="Generate Report", agent=post_trade_agent),
    ]
)
```

---

## 4. Scheduler

**Package:** `scheduler/`

Using APScheduler with AsyncIOScheduler. **Runs as separate process** (`python -m scheduler`).

### Schedule

| Job | Time | Frequency |
| --- | ---- | --------- |
| Intraday Analysis | 9:00 AM | Mon-Fri |
| Order Execution | 9:15 AM | Mon-Fri |
| Position Monitoring | 9:30 AM - 3:20 PM | Every 20 min |
| News Summary | 9 AM - 4 PM | Hourly |
| Post-Trade Analysis | 4:00 PM | Mon-Fri |

### Implementation

```python
# scheduler/__main__.py
from scheduler.scheduler import start_scheduler
import asyncio

if __name__ == "__main__":
    asyncio.run(start_scheduler())
```

```python
# scheduler/scheduler.py
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

scheduler = AsyncIOScheduler()

def configure_jobs():
    # Intraday Analysis - 9:00 AM
    scheduler.add_job(
        run_intraday_analysis,
        CronTrigger(hour=9, minute=0, day_of_week='mon-fri'),
        id='intraday_analysis'
    )

    # Monitoring - Every 20 min during market hours
    scheduler.add_job(
        run_monitoring,
        CronTrigger(minute='*/20', hour='9-15', day_of_week='mon-fri'),
        id='position_monitoring'
    )
    # ... other jobs

async def start_scheduler():
    configure_jobs()
    scheduler.start()
    # Keep running
    while True:
        await asyncio.sleep(3600)
```

---

## 5. API Endpoints

### Remove

- `POST /run-cycle` - No API exposure for running workflows

### Add Routes

**Trades (`/api/trades`):**

- `GET /daily?date=YYYY-MM-DD` - Get all trades for a date
- `GET /history?days=7&symbol=` - Get trade history
- `GET /{trade_id}` - Get trade detail

**Workflows (`/api/workflows`):**

```python
# api/routes/workflows.py
from fastapi import APIRouter

router = APIRouter()

@router.get("/sessions/{workflow_name}")
async def get_workflow_sessions(workflow_name: str, days: int = 7):
    """Get recent workflow sessions"""
    workflow = get_workflow_by_name(workflow_name)
    # Use agno's session retrieval
    sessions = []
    for i in range(days):
        day = (date.today() - timedelta(days=i)).isoformat()
        session = workflow.get_session(session_id=day)
        if session:
            sessions.append({
                "date": day,
                "runs": len(session.runs) if session.runs else 0,
                "session_data": session.session_data
            })
    return sessions

@router.get("/runs/{workflow_name}/{session_id}")
async def get_workflow_run(workflow_name: str, session_id: str):
    """Get detailed run information"""
    workflow = get_workflow_by_name(workflow_name)
    session = workflow.get_session(session_id=session_id)
    return {
        "session_id": session_id,
        "runs": [run.model_dump() for run in session.runs] if session.runs else [],
        "session_state": session.session_data
    }

@router.get("/analysis/daily")
async def get_daily_analysis(date_str: str = None):
    """Get combined analysis for a day"""
    target_date = date_str or date.today().isoformat()

    # Get from intraday workflow
    session = intraday_workflow.get_session(session_id=target_date)
    if not session:
        return {"error": "No analysis for this date"}

    return {
        "date": target_date,
        "picks": session.session_data.get("picks", []),
        "regime": session.session_data.get("regime"),
        "runs": len(session.runs) if session.runs else 0
    }
```

---

## 6. New Agents

### Monitoring Agent

**Location:** `agents/monitoring/`

Tools (no place_order):

- FyersToolkit: get_positions, get_quotes, get_market_depth, exit_position, modify_order

Instructions focus:

- Only modify or close positions
- Track toward 5% daily target
- Never go negative
- **ATR-based dynamic trailing stops** (1.5-2x ATR for SL distance)
- Trail SL for winners
- Close losers proactively when momentum reverses

### News Summarizer Agent

**Location:** `agents/news_summarizer/`

Tools:

- CogencisToolkit
- NSEIndiaToolkit: get_announcements, get_corporate_actions
- YahooFinanceToolkit: get_market_news

Output: Structured JSON with KEY_EVENTS, SENTIMENT, AFFECTED_SYMBOLS stored in session_state

### Post-Trade Analyst Agent

**Location:** `agents/post_trade/`

Tools: None (analysis only, receives data via session_state)

Output: Markdown report with metrics, agent accuracy, learnings

---

## 7. Data Flow

```
News Workflow (hourly)
       |
       v
   session_state["news_context"]
       |
       v
Intraday Analysis (9 AM)
       |
       v
   session_state["picks"] ---------> Agno Session DB
       |                              (auto-stored)
       v
Executor Workflow (9:15 AM)
       |
       v
   Trade table (SQLModel)
       |
       v
Monitoring (every 20 min) <--- Reads news_workflow session
       |                       Reads Trade table
       v
Trade table (updates)
       |
       v
Post-Trade Analysis (4 PM) <--- Reads all sessions
       |
       v
   session_state["report"]
```

---

## 8. Key Configuration Additions

Add to [core/config.py](core/config.py):

```python
# Trading targets
TARGET_DAILY_RETURN_PERCENT: float = 5.0
MAX_DAILY_LOSS_PERCENT: float = 2.0
BASE_CAPITAL: float = 100000.0
MAX_STOCKS_PER_DAY: int = 15

# Scheduler (separate process)
SCHEDULER_ENABLED: bool = True
MARKET_OPEN_TIME: str = "09:15"
MARKET_CLOSE_TIME: str = "15:30"

# Agno Workflow DB
WORKFLOW_DB_FILE: str = "hagrid_workflows.db"
```

---

## 9. Implementation Order

### Phase 1: Foundation

1. Add Trade model to [core/models.py](core/models.py)
2. Add config settings to [core/config.py](core/config.py)
3. Create `scripts/login_fyers.py`
4. Create shared `workflow_db = SqliteDb(...)` in `workflows/__init__.py`

### Phase 2: Agents

5. Create monitoring agent (`agents/monitoring/`)
6. Create news summarizer agent (`agents/news_summarizer/`)
7. Create post-trade analyst agent (`agents/post_trade/`)

### Phase 3: Workflows

8. Enhance [workflows/intraday_cycle.py](workflows/intraday_cycle.py) with db, session_state, history
9. Create `workflows/executor.py`
10. Create `workflows/monitoring.py`
11. Create `workflows/news_workflow.py`
12. Create `workflows/post_trade.py`

### Phase 4: Scheduler

13. Create `scheduler/__init__.py` and `scheduler/__main__.py`
14. Create `scheduler/scheduler.py`
15. Create `scheduler/jobs.py`

### Phase 5: API

16. Create route modules in `api/routes/`
17. Remove `/run-cycle` from [api/main.py](api/main.py)
18. Add new route includes

---

## 10. Verification Plan

### Unit Tests

- Test login script token validation flow
- Test Trade model creation
- Test workflow session_state sharing

### Integration Tests

- Run intraday workflow, verify session stored in DB
- Access session via `workflow.get_session(session_id="...")`
- Test cross-workflow data access (monitoring reads intraday session)

### End-to-End Test

1. Run `scripts/login_fyers.py` - verify token stored
2. Manually trigger news workflow - verify session_state has news
3. Manually trigger intraday workflow - verify picks in session_state
4. Check DB has workflow sessions: `sqlite3 hagrid_workflows.db ".tables"`
5. Manually trigger executor - verify Trade records created
6. Manually trigger monitoring - verify Trade updates
7. Manually trigger post-trade - verify report in session_state
8. Test API endpoints return data from workflow sessions

### Scheduler Test

```bash
python -m scheduler  # Start scheduler process
# Watch logs for job execution at scheduled times
```

---

## Key Design Decisions

| Question | Decision |
| -------- | -------- |
| Where to store workflow runs? | Agno's built-in SqliteDb (auto-stores input, output, step results) |
| Where to store trades? | Custom Trade SQLModel table (trade lifecycle not covered by agno) |
| How workflows communicate? | Via session_state and cross-workflow session access |
| How to access past runs? | `add_workflow_history_to_steps=True` + `workflow.get_session()` |
| Session ID strategy? | Use date string like "2025-01-19" for day-wise organization |
| Scheduler deployment? | Separate process: `python -m scheduler` |

---

## 11. Comprehensive Session, History & Data Flow Reference

### 11.1 Workflow Sessions

**What Workflow Sessions Store:**
- `session_id` - Unique identifier (we use date string like "2025-01-19")
- `runs` - List of all workflow executions for this session
- `session_state` - Shared mutable data between steps (persists across runs)
- `session_data` - Execution metadata (name, timestamps)
- Input/output for each run, all step results, timing metrics

**Key Difference from Agent Sessions:**
- Agent sessions store conversation messages and can create summaries
- Workflow sessions store complete run results, NO summaries

**Accessing Workflow Sessions:**
```python
# Get session by ID
session = workflow.get_session(session_id="2025-01-19")

# Access stored data
runs = session.runs  # List of all executions
state = session.session_state  # Shared state dict
```

### 11.2 Workflow Session State

**Initialization:**
```python
workflow = Workflow(
    name="My Workflow",
    session_state={"picks": [], "regime": None},  # Initial state
    db=SqliteDb(db_file="workflows.db"),
)
```

**Accessing in Function Steps (via RunContext):**
```python
def my_function(step_input: StepInput, run_context: RunContext) -> StepOutput:
    # Read state
    picks = run_context.session_state.get("picks", [])

    # Modify state (changes persist across steps and runs)
    run_context.session_state["picks"] = new_picks

    return StepOutput(content="Done")
```

**Accessing in Agent Tools:**
```python
def my_tool(run_context: RunContext, param: str) -> str:
    # Tools can also access session_state
    run_context.session_state["key"] = value
    return "Tool result"
```

**Persistence:**
- Session state persists if database is configured
- Loads automatically in subsequent runs with same session_id
- All components (agents, teams, functions) share the same state object

### 11.3 Accessing Previous Step Outputs

**StepInput Methods:**
```python
def my_function(step_input: StepInput) -> StepOutput:
    # Original workflow input
    original_input = step_input.input

    # Previous step's output (immediate predecessor)
    prev_content = step_input.previous_step_content

    # Get specific step by name
    regime_output = step_input.get_step_content("Regime Check")

    # Get complete StepOutput object
    step_output = step_input.get_step_output("Research Step")

    # All previous step outputs combined
    all_content = step_input.get_all_previous_content()

    # Last step content specifically
    last_content = step_input.get_last_step_content()

    return StepOutput(content="Processed")
```

**Parallel Group Output:**
- When accessing Parallel group output, returns dict with step names as keys
- `step_input.get_step_content("Parallel Step")` → `{"Step A": "...", "Step B": "..."}`

**Lookup Priority:**
- Top-level steps have priority over nested steps with same name
- System recursively searches through Parallel, Condition, Router, Loop groups

### 11.4 Workflow History (Past Runs)

**Enabling Workflow History:**
```python
workflow = Workflow(
    name="Intraday Analysis",
    db=workflow_db,
    add_workflow_history_to_steps=True,  # Enable for all steps
    num_history_runs=5,  # Last 5 runs (default: all available)
    steps=[...],
)
```

**Step-Level Override:**
```python
Step(
    name="Analysis Step",
    agent=my_agent,
    add_workflow_history=True,  # Override workflow setting
)
```

**Accessing History in Functions:**
```python
def my_function(step_input: StepInput) -> StepOutput:
    # Get history as list of (input, output) tuples
    history = step_input.get_workflow_history(num_runs=5)
    for user_input, workflow_output in history:
        print(f"Input: {user_input}, Output: {workflow_output}")

    # Get history as formatted XML string (for agent consumption)
    history_context = step_input.get_workflow_history_context(num_runs=5)

    return StepOutput(content="Processed with history")
```

**What History Contains:**
- Previous workflow inputs and outputs
- Run identifiers
- Enables pattern analysis across multiple days

### 11.5 Agent Chat History (Within Workflow Steps)

**Agent-Level History Configuration:**
```python
my_agent = Agent(
    name="Analysis Agent",
    model=OpenAIChat(id="gpt-4o"),
    db=SqliteDb(db_file="agents.db"),  # Required for history

    # Automatic history injection
    add_history_to_context=True,  # Auto-include past messages
    num_history_runs=3,  # Last 3 conversations (default: 3)

    # Active retrieval tools (agent decides when to use)
    read_chat_history=True,  # Provides get_chat_history() tool
    read_tool_call_history=True,  # Provides get_tool_call_history() tool

    # Cross-session history
    search_session_history=True,  # Search across sessions
    num_history_sessions=2,  # How many past sessions
)
```

**When to Use Which:**
| Option | Use Case |
| ------ | -------- |
| `add_history_to_context=True` | Simple continuity, short conversations |
| `read_chat_history=True` | Long conversations, selective access needed |
| `search_session_history=True` | Need memory across different days/sessions |

**Important:** More history = larger context = slower/costlier. Start with `num_history_runs=3`.

### 11.6 Team History & State Sharing

**Team-Level History:**
```python
research_team = Team(
    name="Research Team",
    members=[agent1, agent2],
    db=SqliteDb(db_file="teams.db"),

    # Team leader history
    add_history_to_context=True,
    num_history_runs=3,

    # Share team history with all members
    add_team_history_to_members=True,
    num_team_history_runs=5,

    # Share member outputs within current execution
    share_member_interactions=True,
)
```

**Team Session State:**
```python
research_team = Team(
    name="Research Team",
    members=[agent1, agent2],
    session_state={"market_context": None},  # Shared across members
    enable_agentic_state=True,  # Allow agents to modify state
)
```

**How Members Access Team State:**
- Via `run_context.session_state` in tool functions
- State propagates through nested team structures
- Updates automatically persist to database

### 11.7 Complete Data Flow Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                        WORKFLOW RUN                                 │
│  session_id="2025-01-19"                                           │
│  session_state={"picks":[], "regime":None, "news_context":None}    │
└─────────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│  STEP 1: Regime Check (Agent)                                       │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │ Agent has:                                                   │   │
│  │ - add_history_to_context=True (sees past agent runs)        │   │
│  │ - Access to run_context.session_state                       │   │
│  │ - Workflow history via step_input.get_workflow_history()    │   │
│  └─────────────────────────────────────────────────────────────┘   │
│  Output: "TRENDING" → stored as step output                         │
└─────────────────────────────────────────────────────────────────────┘
                                │
                                ▼ step_input.previous_step_content = "TRENDING"
                                  step_input.get_step_content("Regime Check") = "TRENDING"
┌─────────────────────────────────────────────────────────────────────┐
│  STEP 2: Research Team (Team with 12 agents)                        │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │ Team has:                                                    │   │
│  │ - add_team_history_to_members=True (share with agents)      │   │
│  │ - share_member_interactions=True (agents see each other)    │   │
│  │ - session_state shared across all members                   │   │
│  │                                                              │   │
│  │ Each member agent has own add_history_to_context setting    │   │
│  └─────────────────────────────────────────────────────────────┘   │
│  Output: Combined research from all 12 agents                       │
└─────────────────────────────────────────────────────────────────────┘
                                │
                                ▼ step_input.previous_step_content = research output
                                  step_input.get_step_content("Research Team") = research
┌─────────────────────────────────────────────────────────────────────┐
│  STEP 3: Aggregation (Function)                                     │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │ def aggregate(step_input: StepInput, run_context: RunContext):│  │
│  │     # Access all previous step outputs                       │   │
│  │     regime = step_input.get_step_content("Regime Check")    │   │
│  │     research = step_input.previous_step_content             │   │
│  │                                                              │   │
│  │     # Access workflow history (past days)                   │   │
│  │     history = step_input.get_workflow_history(num_runs=5)   │   │
│  │                                                              │   │
│  │     # Update session state (persists for other steps/runs)  │   │
│  │     run_context.session_state["picks"] = selected_picks     │   │
│  │     run_context.session_state["regime"] = regime            │   │
│  │                                                              │   │
│  │     return StepOutput(content=json.dumps(picks))            │   │
│  └─────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│  AUTO-STORED TO DATABASE                                            │
│  - All step outputs                                                 │
│  - Final workflow output                                            │
│  - Updated session_state                                            │
│  - Timestamps, metrics                                              │
└─────────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│  CROSS-WORKFLOW ACCESS (e.g., Executor Workflow)                    │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │ def load_picks(step_input, run_context):                    │   │
│  │     # Access another workflow's session                     │   │
│  │     session = intraday_workflow.get_session(                │   │
│  │         session_id=date.today().isoformat()                 │   │
│  │     )                                                        │   │
│  │     picks = session.session_state.get("picks", [])          │   │
│  │     run_context.session_state["picks"] = picks              │   │
│  └─────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
```

### 11.8 Summary: What Each Component Can Access

| Component | Can Access |
| --------- | ---------- |
| **Agent in Step** | Own chat history (if enabled), run_context.session_state, tools |
| **Team in Step** | Team history, member histories, shared session_state |
| **Function Step** | step_input.* methods, run_context.session_state, workflow history |
| **Condition/Router** | run_context.session_state for decision logic |
| **Other Workflows** | workflow.get_session(session_id) for cross-workflow data |

### 11.9 Best Practices

1. **Session ID Strategy**: Use `date.today().isoformat()` for day-wise organization
2. **History Limits**: Start with `num_history_runs=3-5`, increase if needed
3. **Agent History**: Use `add_history_to_context` for simple cases, `read_chat_history` for selective access
4. **Team History**: Enable `share_member_interactions` for collaborative analysis
5. **Session State**: Put data that needs to flow between steps/workflows in session_state
6. **Database Required**: All persistence features require `db=SqliteDb(...)` configuration

---

## 12. Configuration Changes to Existing Agents/Teams

### 12.1 Shared Database Instance

Create `workflows/__init__.py` with shared database:

```python
from agno.db.sqlite import SqliteDb

# Shared database for all workflows
workflow_db = SqliteDb(
    db_file="hagrid_workflows.db",
    session_table="workflow_sessions"
)

# Shared database for all agents (optional - for agent-level history)
agent_db = SqliteDb(
    db_file="hagrid_agents.db",
    session_table="agent_sessions"
)
```

### 12.2 Research Team Configuration

Update `workflows/intraday_cycle.py`:

```python
from workflows import workflow_db, agent_db

# Enhanced Research Team with history sharing
research_team = Team(
    name="Research Team",
    members=[
        technical_agent, options_agent, fundamentals_agent,
        sector_agent, microstructure_agent, macro_agent,
        institutional_agent, news_agent, events_agent,
        correlation_agent, position_agent
    ],
    db=agent_db,  # Enable team history storage

    # Share team context with all members
    add_team_history_to_members=True,
    num_team_history_runs=3,  # Last 3 team runs

    # Members see each other's outputs during execution
    share_member_interactions=True,

    # Team session state for coordination
    session_state={"market_context": {}},

    description="12 specialized agents analyzing from multiple perspectives."
)
```

### 12.3 Individual Agent Configuration (Optional Enhancement)

For agents that benefit from their own history (like regime_agent):

```python
# agents/departments/regime/agent.py
from agno.agent import Agent
from agno.db.sqlite import SqliteDb

agent_db = SqliteDb(db_file="hagrid_agents.db")

regime_agent = Agent(
    name="Regime Detective",
    role="Market Regime Classifier",
    model="google:gemini-3-pro-preview",
    tools=[fyers_tools, trading_tools],
    instructions=regime_instructions,
    markdown=True,

    # Agent-level history (sees its own past analyses)
    db=agent_db,
    add_history_to_context=True,
    num_history_runs=3,  # Last 3 regime checks
)
```

**Note:** Agent-level history is OPTIONAL. The workflow history (`add_workflow_history_to_steps`) gives steps access to past workflow runs, which may be sufficient.

### 12.4 Enhanced Intraday Workflow

Complete configuration:

```python
from workflows import workflow_db
from datetime import date

intraday_workflow = Workflow(
    name="Intraday Trading Cycle",
    db=workflow_db,

    # Session state shared across all steps
    session_state={
        "picks": [],
        "regime": None,
        "news_context": None,
        "risk_validated": False
    },

    # Enable workflow history for all steps
    add_workflow_history_to_steps=True,
    num_history_runs=5,  # Last 5 trading days

    steps=[
        Step(
            name="Regime Check",
            agent=regime_agent,
            description="Check market regime",
            # Step can override workflow history setting if needed
            # add_workflow_history=False  # Disable for this step
        ),
        Step(
            name="Multi-Agent Analysis",
            team=research_team,
            description="12 agents analyze in parallel"
        ),
        Step(
            name="Signal Aggregation",
            agent=aggregator_agent,
            description="Aggregate signals into candidates"
        ),
        Step(
            name="Risk Management",
            agent=risk_agent,
            description="Validate and size trades"
        ),
        # Note: Execution step removed - handled by executor_workflow
    ]
)

# Run workflow with date-based session
result = intraday_workflow.run(
    input="Analyze NIFTY 100 for intraday trading",
    session_id=date.today().isoformat()  # "2025-01-19"
)
```

### 12.5 Decision Matrix: When to Use Each History Type

| History Type | When to Use | Example |
| ------------ | ----------- | ------- |
| **Workflow History** (`add_workflow_history_to_steps`) | Steps need past workflow runs | "Yesterday we picked INFY, how did it do?" |
| **Agent History** (`add_history_to_context`) | Agent needs its own past conversations | Regime agent comparing to previous regime calls |
| **Team History** (`add_team_history_to_members`) | Team members need shared context | Research team knowing what was analyzed before |
| **Cross-Workflow** (`workflow.get_session()`) | Workflow needs data from another workflow | Executor loading picks from analysis workflow |

### 12.6 Files to Modify for History/Session Support

| File | Change |
| ---- | ------ |
| `workflows/__init__.py` | Add `workflow_db` and `agent_db` exports |
| `workflows/intraday_cycle.py` | Add `db`, `session_state`, `add_workflow_history_to_steps` to workflow; add history settings to team |
| `agents/departments/regime/agent.py` | (Optional) Add `db`, `add_history_to_context` |
| `agents/meta/aggregator/agent.py` | (Optional) Add `db`, `add_history_to_context` |

**Recommendation:** Start with workflow-level history only. Add agent-level history later if needed for specific agents.
