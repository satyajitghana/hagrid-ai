from agno.agent import Agent
from agno.models.openai import OpenAIChat
from core.broker_toolkit import BrokerToolkit
from broker.mock_broker import MockBroker
from agents.departments.sector.instructions import sector_instructions

# Initialize broker and toolkit
broker = MockBroker()
broker_tools = BrokerToolkit(
    broker,
    include_tools=["get_quotes", "get_historical_data"]
)

sector_agent = Agent(
    name="Sector Analyst",
    role="Sector Rotation Specialist",
    model=OpenAIChat(id="gpt-4o-mini"),
    tools=[broker_tools],
    instructions=sector_instructions,
    markdown=True,
)