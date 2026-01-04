# Hagrid AI Implementation Plan

## 1. Directory Structure

```text
hagrid-ai/
├── agents/
│   ├── departments/          # The 12 specialized agents (Agno Agent Instances)
│   │   ├── __init__.py
│   │   ├── technical.py      # Dept 1
│   │   ├── options.py        # Dept 2
│   │   ├── fundamentals.py   # Dept 3
│   │   ├── sector.py         # Dept 4
│   │   ├── microstructure.py # Dept 5
│   │   ├── macro.py          # Dept 6
│   │   ├── institutional.py  # Dept 7
│   │   ├── news.py           # Dept 8
│   │   ├── regime.py         # Dept 9 (Volatility Filter)
│   │   ├── events.py         # Dept 10
│   │   ├── correlation.py    # Dept 11
│   │   └── position.py       # Dept 12
│   ├── meta/                 # Coordinator agents
│   │   ├── __init__.py
│   │   ├── aggregator.py     # Signal Aggregator
│   │   ├── risk.py           # Portfolio & Risk
│   │   └── execution.py      # Execution Agent
│   └── teams.py              # Agno Teams definitions
├── workflows/                # Deterministic workflows
│   ├── __init__.py
│   └── intraday_cycle.py     # The main trading loop workflow
├── core/
│   ├── __init__.py
│   ├── config.py             # Settings and Env vars
│   ├── types.py              # Pydantic models (Signal, Trade, etc.)
│   └── logic.py              # Pure algorithmic calculations (VIX check, Indicators, Sizing)
├── broker/
│   ├── __init__.py
│   ├── interface.py          # Abstract base class for brokers
│   └── mock_broker.py        # Mock implementation
├── api/
│   ├── __init__.py
│   ├── main.py               # FastAPI application entry point
└── main.py                   # CLI entry point
```

## 2. Agent Implementation Strategy (The Agno Way)
We will **instantiate** `agno.agent.Agent` instead of inheriting from it. Logic will be defined in `core/logic.py` and passed as **tools** to the agents.

### Example: Regime Agent (Dept 9)
- **Role**: Market Regime Classifier
- **Tool**: `get_market_regime(vix: float)` (defined in `core/logic.py`)
- **Instructions**: "Use the `get_market_regime` tool to determine the current market state. If the regime is CRISIS, output a NO_TRADE signal."

### Example: Technical Agent (Dept 1)
- **Role**: Technical Analyst
- **Tool**: `analyze_technicals(symbol: str, prices: list)`
- **Instructions**: "Analyze the technicals for the given symbol using the provided tool."

## 3. Workflow Strategy (`IntradayCycle`)
We will use `agno.workflow.Workflow` to orchestrate the steps.
- **Step 1**: `Regime Agent` checks market condition.
- **Step 2**: `Research Team` (Parallel) analyzes symbols.
- **Step 3**: `Signal Aggregator` combines results.
- **Step 4**: `Risk Agent` validates and sizes trades.
- **Step 5**: `Execution Agent` places orders.

## 4. Dependencies
- `agno`: Core framework.
- `fastapi`: API.
- `uvicorn`: Server.
- `pydantic`: Data validation.
- `python-dotenv`: Env vars.