from agno.agent import Agent
from agno.models.openai import OpenAIChat
from core.broker_toolkit import BrokerToolkit
from broker.mock_broker import MockBroker
from agents.departments.position.instructions import position_instructions

# Initialize broker and toolkit
broker = MockBroker()
broker_tools = BrokerToolkit(
    broker,
    include_tools=["get_positions", "get_quotes", "get_market_depth", "get_historical_data"]
)

position_agent = Agent(
    name="Position Adjuster",
    role="Trade Management Specialist",
    model=OpenAIChat(id="gpt-4o-mini"),
    tools=[broker_tools],
    instructions=position_instructions,
    markdown=True,
)