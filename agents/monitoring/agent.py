"""Position Monitoring Agent for managing open positions."""

from agno.agent import Agent
from agno.db.sqlite import SqliteDb

from broker.fyers import FyersToolkit
from core.fyers_client import get_fyers_client
from tools.analysis import TradingToolkit
from agents.monitoring.instructions import monitoring_instructions
from core.config import get_settings

settings = get_settings()

# Initialize toolkits - monitoring agent needs position management and market data
# NOTE: Does NOT include place_order - monitoring agent cannot open new positions
fyers_tools = FyersToolkit(
    get_fyers_client(),
    include_tools=[
        # Market Data - for analysis
        "get_quotes",
        "get_market_depth",
        "get_historical_data",
        "get_technical_indicators",
        # Position Management - modify/close only
        "get_positions",
        "exit_position",
        "get_orders",
        # Account Info
        "get_funds",
    ]
)

# Analysis tools for ATR calculation and technical signals
trading_tools = TradingToolkit(
    include_tools=[
        "calculate_atr",
        "get_technical_signals",
        "calculate_trailing_stop",
    ]
)

# Agent database for chat history (optional)
agent_db = SqliteDb(db_file=settings.AGENT_DB_FILE)

monitoring_agent = Agent(
    name="Position Monitor",
    role="Position Management Specialist",
    model="google:gemini-3-pro-preview",
    tools=[fyers_tools, trading_tools],
    instructions=monitoring_instructions,
    markdown=True,

    # Agent-level history for pattern recognition across monitoring cycles
    db=agent_db,
    add_history_to_context=True,
    num_history_runs=5,  # Last 5 monitoring cycles for context
)
