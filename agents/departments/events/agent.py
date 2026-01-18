from agno.agent import Agent
from broker.fyers import FyersToolkit
from core.fyers_client import get_fyers_client
from tools.yahoo_finance import YahooFinanceToolkit
from tools.nse_india import NSEIndiaToolkit
from agents.departments.events.instructions import events_instructions

# Initialize toolkits - events agent needs quotes and corporate events data
fyers_tools = FyersToolkit(
    get_fyers_client(),
    include_tools=["get_quotes"]
)
# YahooFinance provides earnings calendar, key statistics
yahoo_tools = YahooFinanceToolkit()
# NSEIndia provides corporate announcements, board meetings, AGM dates
nse_tools = NSEIndiaToolkit()

events_agent = Agent(
    name="Corporate Events Analyst",
    role="Earnings and Corporate Action Specialist",
    model="google:gemini-3-pro-preview",
    tools=[fyers_tools, yahoo_tools, nse_tools],
    instructions=events_instructions,
    markdown=True,
)