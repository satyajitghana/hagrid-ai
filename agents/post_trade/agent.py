"""Post-Trade Analyst Agent for end-of-day analysis."""

from agno.agent import Agent
from agno.db.sqlite import SqliteDb

from agents.post_trade.instructions import post_trade_instructions
from core.config import get_settings

settings = get_settings()

# Agent database for chat history
agent_db = SqliteDb(db_file=settings.AGENT_DB_FILE)

# Post-trade analyst has NO tools - it receives all data via session_state
# and produces analysis based on that data
post_trade_agent = Agent(
    name="Post-Trade Analyst",
    role="Trading Performance Analyst",
    model="google:gemini-3-pro-preview",
    tools=[],  # No tools - analysis only based on provided data
    instructions=post_trade_instructions,
    markdown=True,

    # Agent-level history for tracking patterns across days
    db=agent_db,
    add_history_to_context=True,
    num_history_runs=20,  # Last 20 trading days for pattern recognition
)
