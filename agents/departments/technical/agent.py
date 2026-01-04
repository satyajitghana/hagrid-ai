from agno.agent import Agent
from agno.models.openai import OpenAIChat
from core.analysis_toolkit import TradingToolkit
from core.broker_toolkit import BrokerToolkit
from broker.mock_broker import MockBroker
from agents.departments.technical.instructions import technical_instructions

# Initialize broker and toolkits
broker = MockBroker()
broker_tools = BrokerToolkit(
    broker,
    include_tools=["get_quotes", "get_market_depth", "get_technical_analysis"]  # Use computed indicators
)
trading_tools = TradingToolkit()

technical_agent = Agent(
    name="Technical Analyst",
    role="Technical Indicators Specialist",
    model=OpenAIChat(id="gpt-4o-mini"),
    tools=[broker_tools, trading_tools],
    instructions=technical_instructions,
    markdown=True,
)