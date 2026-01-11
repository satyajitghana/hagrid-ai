from agno.agent import Agent
from core.broker_toolkit import BrokerToolkit
from broker.fyers_broker import FyersBroker
from core.config import get_settings
from agents.departments.position.instructions import position_instructions

settings = get_settings()

# Initialize broker and toolkit
broker = FyersBroker(
    client_id=settings.FYERS_CLIENT_ID,
    secret_key=settings.FYERS_SECRET_KEY,
    token_file=settings.FYERS_TOKEN_FILE
)
broker_tools = BrokerToolkit(
    broker,
    include_tools=["get_positions", "get_quotes", "get_market_depth", "get_historical_data"]
)

position_agent = Agent(
    name="Position Adjuster",
    role="Trade Management Specialist",
    model="google:gemini-3-pro-preview",
    tools=[broker_tools],
    instructions=position_instructions,
    markdown=True,
)