from agno.agent import Agent
from core.broker_toolkit import BrokerToolkit
from core.market_data_sources import NewsToolkit
from broker.fyers_broker import FyersBroker
from core.config import get_settings
from agents.departments.news.instructions import news_instructions

settings = get_settings()

# Initialize broker and toolkits
broker = FyersBroker(
    client_id=settings.FYERS_CLIENT_ID,
    secret_key=settings.FYERS_SECRET_KEY,
    token_file=settings.FYERS_TOKEN_FILE
)
broker_tools = BrokerToolkit(broker, include_tools=["get_quotes"])
news_tools = NewsToolkit()

news_agent = Agent(
    name="News Analyst",
    role="Sentiment and News Specialist",
    model="google:gemini-3-pro-preview",
    tools=[broker_tools, news_tools],
    instructions=news_instructions,
    markdown=True,
)