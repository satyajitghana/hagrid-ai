from agno.agent import Agent
from agno.models.openai import OpenAIChat
from core.broker_toolkit import BrokerToolkit
from core.market_data_sources import EventsToolkit
from broker.mock_broker import MockBroker
from agents.departments.events.instructions import events_instructions

# Initialize broker and toolkits
broker = MockBroker()
broker_tools = BrokerToolkit(broker, include_tools=["get_quotes"])
events_tools = EventsToolkit()

events_agent = Agent(
    name="Corporate Events Analyst",
    role="Earnings and Corporate Action Specialist",
    model=OpenAIChat(id="gpt-4o-mini"),
    tools=[broker_tools, events_tools],
    instructions=events_instructions,
    markdown=True,
)