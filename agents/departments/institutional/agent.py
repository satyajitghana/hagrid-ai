from agno.agent import Agent
from core.broker_toolkit import BrokerToolkit
from core.market_data_sources import FIIDIIToolkit
from broker.fyers_broker import FyersBroker
from core.config import get_settings
from agents.departments.institutional.instructions import institutional_instructions

settings = get_settings()

# Initialize broker and toolkits
broker = FyersBroker(
    client_id=settings.FYERS_CLIENT_ID,
    secret_key=settings.FYERS_SECRET_KEY,
    token_file=settings.FYERS_TOKEN_FILE
)
broker_tools = BrokerToolkit(broker, include_tools=["get_quotes"])
fii_dii_tools = FIIDIIToolkit()

institutional_agent = Agent(
    name="Institutional Flow Analyst",
    role="FII/DII and Bulk Deal Specialist",
    model="google:gemini-3-pro-preview",
    tools=[broker_tools, fii_dii_tools],
    instructions=institutional_instructions,
    markdown=True,
)