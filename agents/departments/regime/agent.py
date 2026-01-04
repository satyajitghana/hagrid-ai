from agno.agent import Agent
from agno.models.openai import OpenAIChat
from core.analysis_toolkit import TradingToolkit
from core.broker_toolkit import BrokerToolkit
from broker.mock_broker import MockBroker
from agents.departments.regime.instructions import regime_instructions

# Initialize broker and toolkits
broker = MockBroker()
broker_tools = BrokerToolkit(broker, include_tools=["get_quotes"])  # Only needs quotes
trading_tools = TradingToolkit(include_tools=["get_market_regime"])  # Only needs regime tool

regime_agent = Agent(
    name="Regime Detective",
    role="Market Regime Classifier",
    model=OpenAIChat(id="gpt-4o-mini"),
    tools=[
        broker_tools,
        trading_tools
    ],
    instructions=regime_instructions,
    markdown=True,
)