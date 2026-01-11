from agno.agent import Agent
from core.analysis_toolkit import TradingToolkit
from core.broker_toolkit import BrokerToolkit
from broker.fyers_broker import FyersBroker
from core.config import get_settings
from agents.departments.regime.instructions import regime_instructions

settings = get_settings()

# Initialize broker and toolkits
broker = FyersBroker(
    client_id=settings.FYERS_CLIENT_ID,
    secret_key=settings.FYERS_SECRET_KEY,
    token_file=settings.FYERS_TOKEN_FILE
)
broker_tools = BrokerToolkit(broker, include_tools=["get_quotes"])  # Only needs quotes
trading_tools = TradingToolkit(include_tools=["get_market_regime"])  # Only needs regime tool

regime_agent = Agent(
    name="Regime Detective",
    role="Market Regime Classifier",
    model="google:gemini-3-pro-preview",
    tools=[
        broker_tools,
        trading_tools
    ],
    instructions=regime_instructions,
    markdown=True,
)