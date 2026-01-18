from agno.agent import Agent
from broker.fyers import FyersToolkit
from core.fyers_client import get_fyers_client
from tools.public_market_data import PublicMarketDataToolkit
from tools.yahoo_finance import YahooFinanceToolkit
from tools.groww import GrowwToolkit
from agents.departments.macro.instructions import macro_instructions

# Initialize toolkits - macro agent needs quotes, historical data, and macro data
fyers_tools = FyersToolkit(
    get_fyers_client(),
    include_tools=["get_quotes", "get_historical_data"]
)
# PublicMarketData provides FII/DII data, market holidays, etc.
public_data_tools = PublicMarketDataToolkit()
# YahooFinance provides global markets, commodities, forex
yahoo_tools = YahooFinanceToolkit()
# Groww provides global indices, Indian indices
groww_tools = GrowwToolkit()

macro_agent = Agent(
    name="Macro Analyst",
    role="Global Macro Expert",
    model="google:gemini-3-pro-preview",
    tools=[fyers_tools, public_data_tools, yahoo_tools, groww_tools],
    instructions=macro_instructions,
    markdown=True,
)