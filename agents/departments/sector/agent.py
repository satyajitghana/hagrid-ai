from agno.agent import Agent
from broker.fyers import FyersToolkit
from core.fyers_client import get_fyers_client
from tools.groww import GrowwToolkit
from tools.nse_india import NSEIndiaToolkit
from agents.departments.sector.instructions import sector_instructions

# Initialize toolkits - sector agent needs comprehensive sector data
fyers_tools = FyersToolkit(
    get_fyers_client(),
    include_tools=["get_quotes", "get_historical_data"]
)
# Groww provides market movers, Indian indices (sectoral)
groww_tools = GrowwToolkit()
# NSE India provides comprehensive index data, constituents, market movers
nse_tools = NSEIndiaToolkit()

sector_agent = Agent(
    name="Sector Analyst",
    role="Sector Rotation Specialist",
    model="google:gemini-3-pro-preview",
    tools=[fyers_tools, groww_tools, nse_tools],
    instructions=sector_instructions,
    markdown=True,
)