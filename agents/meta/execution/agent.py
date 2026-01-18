from agno.agent import Agent
from broker.fyers import FyersToolkit
from core.fyers_client import get_fyers_client
from agents.meta.execution.instructions import execution_instructions

# Initialize FyersToolkit directly for order execution
fyers_tools = FyersToolkit(
    get_fyers_client(),
    include_tools=["place_order", "get_positions", "get_orders", "exit_position"]
)

execution_agent = Agent(
    name="Executor",
    role="Order Execution Specialist",
    model="google:gemini-3-pro-preview",
    tools=[fyers_tools],
    instructions=execution_instructions,
    markdown=True,
)