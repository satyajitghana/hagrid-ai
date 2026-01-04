from agno.agent import Agent
from agno.models.openai import OpenAIChat
from core.broker_toolkit import BrokerToolkit
from core.market_data_sources import NewsToolkit
from broker.mock_broker import MockBroker
from agents.departments.news.instructions import news_instructions

# Initialize broker and toolkits
broker = MockBroker()
broker_tools = BrokerToolkit(broker, include_tools=["get_quotes"])
news_tools = NewsToolkit()

news_agent = Agent(
    name="News Analyst",
    role="Sentiment and News Specialist",
    model=OpenAIChat(id="gpt-4o-mini"),
    tools=[broker_tools, news_tools],
    instructions=news_instructions,
    markdown=True,
)