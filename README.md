# Hagrid AI - Multi-Agent Algorithmic Trading Platform

A sophisticated multi-agent trading platform for Indian equities (NIFTY 100 stocks), built using the Agno framework.

## Overview

Hagrid AI analyzes all NIFTY 100 stocks daily using 12 specialized AI agents to select 10-15 best trading opportunities with:
- **Target**: 1% per stock movement → 5% daily portfolio return (with 5x intraday leverage)
- **Risk Control**: Never negative - both LONG & SHORT positions with strict SL/TP
- **Consensus**: Parallel agent validation for critical decisions

## Architecture

See [`ARCHITECTURE.md`](./ARCHITECTURE.md) for complete system design and [`PLAN.md`](./PLAN.md) for implementation details.

## Project Structure

```
hagrid-ai/
├── agents/                   # All trading agents
│   ├── departments/         # 12 specialized analysis agents
│   │   ├── technical/       # Technical Analysis (Dept 1)
│   │   ├── options/         # Options & Greeks (Dept 2)
│   │   ├── fundamentals/    # Fundamental Analysis (Dept 3)
│   │   ├── sector/          # Sector Rotation (Dept 4)
│   │   ├── microstructure/  # Order Book Analysis (Dept 5)
│   │   ├── macro/           # Global Macro (Dept 6)
│   │   ├── institutional/   # FII/DII Flows (Dept 7)
│   │   ├── news/            # News & Sentiment (Dept 8)
│   │   ├── regime/          # Market Regime Detector (Dept 9)
│   │   ├── events/          # Corporate Events (Dept 10)
│   │   ├── correlation/     # Pairs Trading (Dept 11)
│   │   └── position/        # Position Management (Dept 12)
│   └── meta/                # Meta-coordination agents
│       ├── aggregator/      # Signal Aggregator
│       ├── risk/            # Portfolio & Risk Manager
│       └── execution/       # Execution Handler
├── workflows/               # Deterministic workflows
│   └── intraday_cycle.py   # Main trading cycle
├── core/                    # Core logic and types
│   ├── config.py           # Application settings
│   ├── types.py            # Pydantic models
│   ├── models.py           # SQLModel database models
│   ├── toolkits.py         # Trading analysis toolkit
│   └── broker_toolkit.py   # Broker operations toolkit
├── broker/                  # Broker integrations
│   ├── interface.py        # Abstract interface (Fyers-compatible)
│   └── mock_broker.py      # Mock implementation for testing
├── api/                     # FastAPI application
│   └── main.py             # REST + WebSocket endpoints
└── main.py                  # Application entry point
```

## Getting Started

### Prerequisites

- Python 3.12+
- OpenAI API Key

### Installation

1. Clone the repository
2. Install dependencies:
```bash
uv sync
```

3. Set environment:
```bash
export OPENAI_API_KEY="your-api-key-here"
```

### Running

```bash
python main.py
```

API available at `http://localhost:8000`

## API Endpoints

### Trading Operations
- `POST /run-cycle` - Trigger daily NIFTY 100 analysis
- `GET /staging?date=YYYY-MM-DD` - View daily AI picks (supports historical query)
- `GET /marketwatch` - Real-time prices for all symbols
- `GET /positions` - Current open positions from broker
- `GET /orders` - Order book from broker
- `GET /funds` - Account balance and margins

### Analysis & Monitoring
- `GET /agent-logs?agent_name=Technical&limit=50` - Agent execution logs (Agno auto-stores)
- `POST /analysis/stock` - Deep-dive analysis for specific stock
- `GET /analysis/history?days=7` - Historical picks and analysis
- `GET /news?category=stocks` - Latest market news

### WebSocket Streams
- `WS /ws/analysis` - Real-time chat with AI agents
- `WS /ws/updates` - Live market data and position updates

## Key Features

- ✅ **12 Specialized Agents**: Each analyzes stocks from different angles
- ✅ **Consensus Validation**: Critical decisions run through 2 parallel agents
- ✅ **Fyers-Compatible Broker**: Ready for real broker integration
- ✅ **SQLModel ORM**: Clean database operations with type safety
- ✅ **Minimal Storage**: Only user sessions & daily picks (Agno handles agent logs)
- ✅ **Mock Broker**: Complete Fyers API emulation for testing
- ✅ **CSV Tool Responses**: LLM-friendly formatted data
- ✅ **Selective Tool Access**: Agents get only the tools they need
- ✅ **WebSocket Support**: Real-time updates and streaming

## Development

### Agent Structure
Each agent has:
- `agent.py`: Agent instantiation with specific tools
- `instructions.py`: Detailed instructions using `dedent()`

### Toolkits
- **TradingToolkit**: Analysis functions (regime, SMA, aggregation)
- **BrokerToolkit**: Market data operations (quotes, depth, history, options, orders)

### Database
- Uses SQLModel ORM for type-safe database operations
- Minimal storage: only daily picks and user sessions
- Agno automatically stores agent sessions and logs

## Next Steps

1. Enhance agent instructions for comprehensive NIFTY 100 analysis
2. Add technical indicator helper functions
3. Integrate real Fyers/Zerodha broker API
4. Implement news API integration
5. Add caching for computed metrics
6. Build Next.js frontend dashboard

## License

[Your License Here]