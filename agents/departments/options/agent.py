from agno.agent import Agent
from core.broker_toolkit import BrokerToolkit
from core.analysis_toolkit import TradingToolkit
from broker.fyers_broker import FyersBroker
from core.config import get_settings
from agents.departments.options.instructions import options_instructions

settings = get_settings()

# Initialize broker and toolkits
broker = FyersBroker(
    client_id=settings.FYERS_CLIENT_ID,
    secret_key=settings.FYERS_SECRET_KEY,
    token_file=settings.FYERS_TOKEN_FILE
)
broker_tools = BrokerToolkit(broker, include_tools=["get_option_chain", "get_quotes"])
trading_tools = TradingToolkit(include_tools=["compute_options_metrics"])

options_agent = Agent(
    name="Options Analyst",
    role="Derivatives and Greeks Specialist",
    model="google:gemini-3-pro-preview",
    tools=[broker_tools, trading_tools],
    instructions=options_instructions,
    markdown=True,
)