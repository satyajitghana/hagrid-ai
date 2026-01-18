from agno.agent import Agent
from broker.fyers import FyersToolkit
from core.fyers_client import get_fyers_client
from tools.analysis import TradingToolkit
from agents.departments.regime.instructions import regime_instructions

# Initialize toolkits - regime agent needs quotes and historical data for VIX analysis
fyers_tools = FyersToolkit(
    get_fyers_client(),
    include_tools=["get_quotes", "get_historical_data"]
)
trading_tools = TradingToolkit(include_tools=["get_market_regime"])

regime_agent = Agent(
    name="Regime Detective",
    role="Market Regime Classifier",
    model="google:gemini-3-pro-preview",
    tools=[fyers_tools, trading_tools],
    instructions=regime_instructions,
    markdown=True,
)