"""News Summarizer Agent for aggregating market news."""

from agno.agent import Agent
from agno.db.sqlite import SqliteDb

from tools.yahoo_finance import YahooFinanceToolkit
from tools.nse_india import NSEIndiaToolkit
from agents.news_summarizer.instructions import news_instructions
from core.config import get_settings

settings = get_settings()

# Initialize toolkits for news collection
yahoo_tools = YahooFinanceToolkit(
    include_tools=[
        "get_news",
        "get_market_status",
        "get_earnings_calendar",
    ]
)

nse_tools = NSEIndiaToolkit(
    include_tools=[
        "get_new_announcements",
        "get_equity_announcements",
        "get_symbol_announcements",
        "get_most_active",
    ]
)

# Agent database for chat history
agent_db = SqliteDb(db_file=settings.AGENT_DB_FILE)

news_agent = Agent(
    name="News Summarizer",
    role="Market News Analyst",
    model="google:gemini-3-pro-preview",
    tools=[yahoo_tools, nse_tools],
    instructions=news_instructions,
    markdown=True,

    # Agent-level history for tracking news patterns
    db=agent_db,
    add_history_to_context=True,
    num_history_runs=3,  # Last 3 news summaries for context
)
