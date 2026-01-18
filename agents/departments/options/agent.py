from agno.agent import Agent
from broker.fyers import FyersToolkit
from core.fyers_client import get_fyers_client
from tools.analysis import TradingToolkit
from tools.nse_india import NSEIndiaToolkit
from tools.groww import GrowwToolkit
from agents.departments.options.instructions import options_instructions

# Initialize toolkits - options agent needs option chain, quotes, Greeks, and OI data
fyers_tools = FyersToolkit(
    get_fyers_client(),
    include_tools=["get_quotes", "get_option_chain", "get_option_greeks"]
)
# TradingToolkit provides options metrics computation
trading_tools = TradingToolkit(include_tools=["compute_options_metrics"])
# NSEIndia provides OI spurts, PCR data
nse_tools = NSEIndiaToolkit()
# Groww provides option chain with greeks, live prices
groww_tools = GrowwToolkit()

options_agent = Agent(
    name="Options Analyst",
    role="Derivatives and Greeks Specialist",
    model="google:gemini-3-pro-preview",
    tools=[fyers_tools, trading_tools, nse_tools, groww_tools],
    instructions=options_instructions,
    markdown=True,
)
