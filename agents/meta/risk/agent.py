from agno.agent import Agent
from core.broker_toolkit import BrokerToolkit
from broker.fyers_broker import FyersBroker
from core.config import get_settings
from agents.meta.risk.instructions import risk_instructions

settings = get_settings()

# Initialize broker and toolkit
broker = FyersBroker(
    client_id=settings.FYERS_CLIENT_ID,
    secret_key=settings.FYERS_SECRET_KEY,
    token_file=settings.FYERS_TOKEN_FILE
)
broker_tools = BrokerToolkit(
    broker,
    include_tools=["get_positions", "calculate_margin"]
)

risk_agent = Agent(
    name="Risk Manager",
    role="Portfolio Risk Guardian",
    model="google:gemini-3-pro-preview",
    tools=[broker_tools],
    instructions=risk_instructions,
    markdown=True,
)