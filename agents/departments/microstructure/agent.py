from agno.agent import Agent
from broker.fyers import FyersToolkit
from core.fyers_client import get_fyers_client
from tools.nse_india import NSEIndiaToolkit
from agents.departments.microstructure.instructions import microstructure_instructions

# Initialize toolkits - microstructure agent needs quotes, depth, historical data, and OI flow
fyers_tools = FyersToolkit(
    get_fyers_client(),
    include_tools=["get_quotes", "get_market_depth", "get_historical_data"]
)
# NSE India provides OI spurts for smart money flow analysis
nse_tools = NSEIndiaToolkit()

microstructure_agent = Agent(
    name="Microstructure Analyst",
    role="Order Book and Liquidity Specialist",
    model="google:gemini-3-pro-preview",
    tools=[fyers_tools, nse_tools],
    instructions=microstructure_instructions,
    markdown=True,
)