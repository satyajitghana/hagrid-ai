from agno.agent import Agent
from tools.analysis import TradingToolkit
from agents.meta.aggregator.instructions import aggregator_instructions

trading_tools = TradingToolkit(include_tools=["aggregate_signals_logic"])

aggregator_agent = Agent(
    name="Signal Aggregator",
    role="Signal Fusion Specialist",
    model="google:gemini-3-pro-preview",
    tools=[trading_tools],
    instructions=aggregator_instructions,
    markdown=True,
)