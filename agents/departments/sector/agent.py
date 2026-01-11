from agno.agent import Agent
from core.broker_toolkit import BrokerToolkit
from broker.fyers_broker import FyersBroker
from core.config import get_settings
from agents.departments.sector.instructions import sector_instructions

settings = get_settings()

# Initialize broker and toolkit
broker = FyersBroker(
    client_id=settings.FYERS_CLIENT_ID,
    secret_key=settings.FYERS_SECRET_KEY,
    token_file=settings.FYERS_TOKEN_FILE
)
broker_tools = BrokerToolkit(
    broker,
    include_tools=["get_quotes", "get_historical_data"]
)

sector_agent = Agent(
    name="Sector Analyst",
    role="Sector Rotation Specialist",
    model="google:gemini-3-pro-preview",
    tools=[broker_tools],
    instructions=sector_instructions,
    markdown=True,
)