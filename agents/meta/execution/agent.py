from agno.agent import Agent
from agno.models.openai import OpenAIChat
from core.broker_toolkit import BrokerToolkit
from broker.mock_broker import MockBroker
from agents.meta.execution.instructions import execution_instructions

# Initialize broker and toolkit
broker = MockBroker()
broker_tools = BrokerToolkit(
    broker,
    include_tools=["place_order", "get_positions"]  # Only needs order placement and position check
)

execution_agent = Agent(
    name="Executor",
    role="Order Execution Specialist",
    model=OpenAIChat(id="gpt-4o-mini"),
    tools=[broker_tools],
    instructions=execution_instructions,
    markdown=True,
)