from agno.agent import Agent
from agno.models.openai import OpenAIChat
from core.broker_toolkit import BrokerToolkit
from core.analysis_toolkit import TradingToolkit
from broker.mock_broker import MockBroker
from agents.departments.correlation.instructions import correlation_instructions

# Initialize broker and toolkits
broker = MockBroker()
broker_tools = BrokerToolkit(broker, include_tools=["get_quotes", "get_historical_data"])
trading_tools = TradingToolkit(include_tools=["compute_correlation_metrics"])

correlation_agent = Agent(
    name="Correlation Analyst",
    role="Pairs Trading Specialist",
    model=OpenAIChat(id="gpt-4o-mini"),
    tools=[broker_tools, trading_tools],
    instructions=correlation_instructions,
    markdown=True,
)