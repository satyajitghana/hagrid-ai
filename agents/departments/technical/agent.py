from agno.agent import Agent
from core.analysis_toolkit import TradingToolkit
from core.broker_toolkit import BrokerToolkit
from broker.fyers_broker import FyersBroker
from core.config import get_settings
from core.analysis_toolkit import TechnicalScannerToolkit
from agents.departments.technical.instructions import technical_instructions

settings = get_settings()

# Initialize broker and toolkits
broker = FyersBroker(
    client_id=settings.FYERS_CLIENT_ID,
    secret_key=settings.FYERS_SECRET_KEY,
    token_file=settings.FYERS_TOKEN_FILE
)
broker_tools = BrokerToolkit(
    broker,
    include_tools=["get_quotes", "get_market_depth", "get_technical_indicators"]
)
scanner_tools = TechnicalScannerToolkit()

technical_agent = Agent(
    name="Technical Analyst",
    role="Technical Indicators Specialist",
    model="google:gemini-3-pro-preview",
    tools=[broker_tools, scanner_tools],
    instructions=technical_instructions,
    markdown=True,
)