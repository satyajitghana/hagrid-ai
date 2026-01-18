from agno.agent import Agent
from broker.fyers import FyersToolkit
from core.fyers_client import get_fyers_client
from tools.public_market_data import PublicMarketDataToolkit
from tools.nse_india import NSEIndiaToolkit
from tools.groww import GrowwToolkit
from agents.departments.institutional.instructions import institutional_instructions

# Initialize toolkits - institutional agent needs quotes and institutional flow data
fyers_tools = FyersToolkit(
    get_fyers_client(),
    include_tools=["get_quotes"]
)
# PublicMarketData provides FII/DII monthly data, bulk deals
public_data_tools = PublicMarketDataToolkit()
# NSEIndia provides shareholding patterns, block deals, bulk deals
nse_tools = NSEIndiaToolkit()
# Groww provides market movers (top gainers/losers), live prices
groww_tools = GrowwToolkit()

institutional_agent = Agent(
    name="Institutional Flow Analyst",
    role="FII/DII and Bulk Deal Specialist",
    model="google:gemini-3-pro-preview",
    tools=[fyers_tools, public_data_tools, nse_tools, groww_tools],
    instructions=institutional_instructions,
    markdown=True,
)