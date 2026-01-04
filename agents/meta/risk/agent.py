from agno.agent import Agent
from agno.models.openai import OpenAIChat
from core.broker_toolkit import BrokerToolkit
from broker.mock_broker import MockBroker
from agents.meta.risk.instructions import risk_instructions

# Initialize broker and toolkit
broker = MockBroker()
broker_tools = BrokerToolkit(
    broker,
    include_tools=["get_positions", "calculate_margin"]  # Only needs position and margin tools
)

risk_agent = Agent(
    name="Risk Manager",
    role="Portfolio Risk Guardian",
    model=OpenAIChat(id="gpt-4o-mini"),
    tools=[broker_tools],
    instructions=risk_instructions,
    markdown=True,
)