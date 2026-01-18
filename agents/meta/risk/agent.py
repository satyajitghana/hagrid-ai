from agno.agent import Agent
from broker.fyers import FyersToolkit
from core.fyers_client import get_fyers_client
from agents.meta.risk.instructions import risk_instructions

# Initialize FyersToolkit directly for risk management
fyers_tools = FyersToolkit(
    get_fyers_client(),
    include_tools=["get_positions", "get_holdings", "get_funds", "calculate_margin"]
)

risk_agent = Agent(
    name="Risk Manager",
    role="Portfolio Risk Guardian",
    model="google:gemini-3-pro-preview",
    tools=[fyers_tools],
    instructions=risk_instructions,
    markdown=True,
)