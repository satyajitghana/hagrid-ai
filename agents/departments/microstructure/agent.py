from agno.agent import Agent
from agno.models.openai import OpenAIChat
from core.broker_toolkit import BrokerToolkit
from broker.mock_broker import MockBroker
from agents.departments.microstructure.instructions import microstructure_instructions

# Initialize broker and toolkit
broker = MockBroker()
broker_tools = BrokerToolkit(
    broker,
    include_tools=["get_quotes", "get_market_depth", "get_historical_data"]
)

microstructure_agent = Agent(
    name="Microstructure Analyst",
    role="Order Book and Liquidity Specialist",
    model=OpenAIChat(id="gpt-4o-mini"),
    tools=[broker_tools],
    instructions=microstructure_instructions,
    markdown=True,
)