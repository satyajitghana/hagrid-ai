from agno.agent import Agent
from agno.models.openai import OpenAIChat
from core.analysis_toolkit import TradingToolkit
from agents.meta.aggregator.instructions import aggregator_instructions

trading_tools = TradingToolkit(include_tools=["aggregate_signals_logic"])

aggregator_agent = Agent(
    name="Signal Aggregator",
    role="Signal Fusion Specialist",
    model=OpenAIChat(id="gpt-4o-mini"),
    tools=[trading_tools],
    instructions=aggregator_instructions,
    markdown=True,
)