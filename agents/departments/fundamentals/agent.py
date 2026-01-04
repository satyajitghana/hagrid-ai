from agno.agent import Agent
from agno.models.openai import OpenAIChat
from core.broker_toolkit import BrokerToolkit
from core.market_data_sources import FundamentalsToolkit
from broker.mock_broker import MockBroker
from agents.departments.fundamentals.instructions import fundamentals_instructions

# Initialize broker and toolkits
broker = MockBroker()
broker_tools = BrokerToolkit(broker, include_tools=["get_quotes"])
fundamentals_tools = FundamentalsToolkit()

fundamentals_agent = Agent(
    name="Fundamentals Analyst",
    role="Company Fundamentals Expert",
    model=OpenAIChat(id="gpt-4o-mini"),
    tools=[broker_tools, fundamentals_tools],
    instructions=fundamentals_instructions,
    markdown=True,
)