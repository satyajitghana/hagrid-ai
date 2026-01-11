from agno.agent import Agent
from core.broker_toolkit import BrokerToolkit
from core.market_data_sources import EventsToolkit
from broker.fyers_broker import FyersBroker
from core.config import get_settings
from agents.departments.events.instructions import events_instructions

settings = get_settings()

# Initialize broker and toolkits
broker = FyersBroker(
    client_id=settings.FYERS_CLIENT_ID,
    secret_key=settings.FYERS_SECRET_KEY,
    token_file=settings.FYERS_TOKEN_FILE
)
broker_tools = BrokerToolkit(broker, include_tools=["get_quotes"])
events_tools = EventsToolkit()

events_agent = Agent(
    name="Corporate Events Analyst",
    role="Earnings and Corporate Action Specialist",
    model="google:gemini-3-pro-preview",
    tools=[broker_tools, events_tools],
    instructions=events_instructions,
    markdown=True,
)