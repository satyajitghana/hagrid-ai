from agno.agent import Agent
from agno.models.openai import OpenAIChat
from core.broker_toolkit import BrokerToolkit
from core.analysis_toolkit import TradingToolkit
from broker.mock_broker import MockBroker
from agents.departments.options.instructions import options_instructions

# Initialize broker and toolkits
broker = MockBroker()
broker_tools = BrokerToolkit(broker, include_tools=["get_option_chain", "get_quotes"])
trading_tools = TradingToolkit(include_tools=["compute_options_metrics"])

options_agent = Agent(
    name="Options Analyst",
    role="Derivatives and Greeks Specialist",
    model=OpenAIChat(id="gpt-4o-mini"),
    tools=[broker_tools, trading_tools],
    instructions=options_instructions,
    markdown=True,
)