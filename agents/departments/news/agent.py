from agno.agent import Agent
from broker.fyers import FyersToolkit
from core.fyers_client import get_fyers_client
from tools.yahoo_finance import YahooFinanceToolkit
from tools.nse_india import NSEIndiaToolkit
from agents.departments.news.instructions import news_instructions

# Initialize toolkits - news agent needs quotes and news sources
fyers_tools = FyersToolkit(
    get_fyers_client(),
    include_tools=["get_quotes"]
)
# YahooFinance provides stock news and market news
yahoo_tools = YahooFinanceToolkit()
# NSEIndia provides corporate announcements
nse_tools = NSEIndiaToolkit()

news_agent = Agent(
    name="News Analyst",
    role="Sentiment and News Specialist",
    model="google:gemini-3-pro-preview",
    tools=[fyers_tools, yahoo_tools, nse_tools],
    instructions=news_instructions,
    markdown=True,
)