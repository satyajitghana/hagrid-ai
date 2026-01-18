from agno.agent import Agent
from broker.fyers import FyersToolkit
from core.fyers_client import get_fyers_client
from tools.screener import ScreenerToolkit
from tools.yahoo_finance import YahooFinanceToolkit
from tools.nse_india import NSEIndiaToolkit
from tools.groww import GrowwToolkit
from agents.departments.fundamentals.instructions import fundamentals_instructions

# Initialize toolkits - fundamentals agent needs quotes and fundamentals data sources
fyers_tools = FyersToolkit(
    get_fyers_client(),
    include_tools=["get_quotes"]
)
# Screener provides detailed Indian company fundamentals
screener_tools = ScreenerToolkit()
# YahooFinance provides global fundamentals, financials, and metrics
yahoo_tools = YahooFinanceToolkit()
# NSEIndia provides shareholding patterns, corporate filings
nse_tools = NSEIndiaToolkit()
# Groww provides company details, stock prices, search
groww_tools = GrowwToolkit()

fundamentals_agent = Agent(
    name="Fundamentals Analyst",
    role="Company Fundamentals Expert",
    model="google:gemini-3-pro-preview",
    tools=[fyers_tools, screener_tools, yahoo_tools, nse_tools, groww_tools],
    instructions=fundamentals_instructions,
    markdown=True,
)