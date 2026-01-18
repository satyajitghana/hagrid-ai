from agno.agent import Agent
from broker.fyers import FyersToolkit
from core.fyers_client import get_fyers_client
from tools.analysis import TechnicalScannerToolkit
from tools.groww import GrowwToolkit
from tools.nse_india import NSEIndiaToolkit
from agents.departments.technical.instructions import technical_instructions

# Initialize toolkits - technical agent needs quotes, depth, historical data, and indicators
fyers_tools = FyersToolkit(
    get_fyers_client(),
    include_tools=["get_quotes", "get_market_depth", "get_historical_data", "get_technical_indicators"]
)
scanner_tools = TechnicalScannerToolkit()
# Groww provides live prices, stock search, indices
groww_tools = GrowwToolkit()
# NSE India provides OI spurts for breakout confirmation and sector data
nse_tools = NSEIndiaToolkit()

technical_agent = Agent(
    name="Technical Analyst",
    role="Technical Indicators Specialist",
    model="google:gemini-3-pro-preview",
    tools=[fyers_tools, scanner_tools, groww_tools, nse_tools],
    instructions=technical_instructions,
    markdown=True,
)