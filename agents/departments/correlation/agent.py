from agno.agent import Agent
from core.broker_toolkit import BrokerToolkit
from core.analysis_toolkit import TradingToolkit
from broker.fyers_broker import FyersBroker
from core.config import get_settings
from agents.departments.correlation.instructions import correlation_instructions

settings = get_settings()

# Initialize broker and toolkits
broker = FyersBroker(
    client_id=settings.FYERS_CLIENT_ID,
    secret_key=settings.FYERS_SECRET_KEY,
    token_file=settings.FYERS_TOKEN_FILE
)
broker_tools = BrokerToolkit(broker, include_tools=["get_quotes", "get_historical_data"])
trading_tools = TradingToolkit(include_tools=["compute_correlation_metrics"])

correlation_agent = Agent(
    name="Correlation Analyst",
    role="Pairs Trading Specialist",
    model="google:gemini-3-pro-preview",
    tools=[broker_tools, trading_tools],
    instructions=correlation_instructions,
    markdown=True,
)