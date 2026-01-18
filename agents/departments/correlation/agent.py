from agno.agent import Agent
from broker.fyers import FyersToolkit
from core.fyers_client import get_fyers_client
from tools.correlation import CorrelationToolkit
from tools.nse_india import NSEIndiaClient
from agents.departments.correlation.instructions import correlation_instructions

# Initialize toolkits - correlation agent needs quotes, historical data, and correlation tools
fyers_client = get_fyers_client()
fyers_tools = FyersToolkit(
    fyers_client,
    include_tools=["get_quotes", "get_historical_data", "get_correlation_matrix"]
)
# CorrelationToolkit provides precomputed NIFTY100 correlation matrix
correlation_tools = CorrelationToolkit(fyers_client, NSEIndiaClient())

correlation_agent = Agent(
    name="Correlation Analyst",
    role="Pairs Trading Specialist",
    model="google:gemini-3-pro-preview",
    tools=[fyers_tools, correlation_tools],
    instructions=correlation_instructions,
    markdown=True,
)