from agno.agent import Agent
from broker.fyers import FyersToolkit
from core.fyers_client import get_fyers_client
from tools.nse_india import NSEIndiaToolkit
from agents.departments.position.instructions import position_instructions

# Initialize toolkits - position agent needs positions, quotes, depth, historical data, and OI flow
fyers_tools = FyersToolkit(
    get_fyers_client(),
    include_tools=["get_positions", "get_quotes", "get_market_depth", "get_historical_data"]
)
# NSE India provides OI spurts for exit timing and smart money flow
nse_tools = NSEIndiaToolkit()

position_agent = Agent(
    name="Position Adjuster",
    role="Trade Management Specialist",
    model="google:gemini-3-pro-preview",
    tools=[fyers_tools, nse_tools],
    instructions=position_instructions,
    markdown=True,
)