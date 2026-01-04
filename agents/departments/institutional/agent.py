from agno.agent import Agent
from agno.models.openai import OpenAIChat
from core.broker_toolkit import BrokerToolkit
from core.market_data_sources import FIIDIIToolkit
from broker.mock_broker import MockBroker
from agents.departments.institutional.instructions import institutional_instructions

# Initialize broker and toolkits
broker = MockBroker()
broker_tools = BrokerToolkit(broker, include_tools=["get_quotes"])
fii_dii_tools = FIIDIIToolkit()

institutional_agent = Agent(
    name="Institutional Flow Analyst",
    role="FII/DII and Bulk Deal Specialist",
    model=OpenAIChat(id="gpt-4o-mini"),
    tools=[broker_tools, fii_dii_tools],
    instructions=institutional_instructions,
    markdown=True,
)