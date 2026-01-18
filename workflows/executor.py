"""
Executor Workflow

This workflow handles order execution:
1. Load today's picks from intraday_workflow session
2. Execute orders via execution agent
3. Store executed trades in Trade table

Runs at 9:15 AM after market opens.
"""

from datetime import date

from agno.workflow import Workflow, Step
from agno.workflow.types import StepInput, StepOutput
from sqlmodel import Session

from workflows import workflow_db
from workflows.intraday_cycle import intraday_workflow
from agents.meta.execution.agent import execution_agent
from core.models import Trade, engine


def load_todays_picks(step_input: StepInput) -> StepOutput:
    """
    Load picks from intraday workflow session.

    Accesses the intraday_workflow session for today and loads
    the risk-validated picks into this workflow's session_state.
    """
    today = date.today().isoformat()

    # Access intraday_workflow session
    session = intraday_workflow.get_session(session_id=today)

    if not session:
        return StepOutput(
            content="No analysis session found for today. Run intraday analysis first."
        )

    picks = session.session_data.get("picks", [])
    regime = session.session_data.get("regime")
    risk_validated = session.session_data.get("risk_validated", False)

    if not risk_validated:
        return StepOutput(
            content="Picks not yet risk-validated. Run intraday analysis first."
        )

    # Store in executor workflow's session state
    if step_input.workflow_session:
        step_input.workflow_session.session_data["picks"] = picks
        step_input.workflow_session.session_data["regime"] = regime

    return StepOutput(
        content=f"Loaded {len(picks) if isinstance(picks, list) else 1} picks for execution. "
        f"Market regime: {regime}"
    )


def store_executed_trades(step_input: StepInput) -> StepOutput:
    """
    Store executed trades to the Trade table.

    Parses the execution agent output and creates Trade records.
    """
    session_data = step_input.workflow_session.session_data if step_input.workflow_session else {}
    executed = session_data.get("executed", [])
    today = date.today().isoformat()

    if not executed:
        # Try to parse from execution agent output
        execution_result = step_input.previous_step_content

        # For now, just store the execution result in session state
        if step_input.workflow_session:
            step_input.workflow_session.session_data["execution_result"] = execution_result

        return StepOutput(
            content=f"Execution completed. Results: {execution_result}"
        )

    # Store trades in database
    stored_count = 0
    with Session(engine) as db:
        for trade_data in executed:
            trade = Trade(
                date=today,
                symbol=trade_data.get("symbol"),
                direction=trade_data.get("direction"),
                entry_price=trade_data.get("entry_price"),
                quantity=trade_data.get("quantity"),
                entry_time=trade_data.get("entry_time"),
                stop_loss=trade_data.get("stop_loss"),
                take_profit=trade_data.get("take_profit"),
                order_id=trade_data.get("order_id"),
                sl_order_id=trade_data.get("sl_order_id"),
                status="OPEN"
            )
            db.add(trade)
            stored_count += 1
        db.commit()

    return StepOutput(
        content=f"Stored {stored_count} trades to database"
    )


# Define the Executor Workflow
executor_workflow = Workflow(
    name="Order Executor",

    # Database for session storage
    db=workflow_db,

    # Session state for execution tracking
    session_state={
        "picks": [],
        "regime": None,
        "executed": [],
        "execution_result": None,
    },

    steps=[
        Step(
            name="Load Picks",
            executor=load_todays_picks,
            description="Load today's risk-validated picks from analysis workflow"
        ),
        Step(
            name="Execute Orders",
            agent=execution_agent,
            description="Execute orders based on picks and market conditions"
        ),
        Step(
            name="Store Trades",
            executor=store_executed_trades,
            description="Store executed trades in the Trade table"
        ),
    ]
)


async def run_executor(input_text: str = None) -> dict:
    """
    Run the executor workflow.

    Args:
        input_text: Optional custom input.

    Returns:
        dict with execution result
    """
    today = date.today().isoformat()

    if input_text is None:
        input_text = (
            f"Execute the risk-validated picks for {today}. "
            f"Place orders with appropriate stop loss and take profit levels. "
            f"Prioritize high-confidence trades first."
        )

    result = await executor_workflow.arun(
        input=input_text,
        session_id=today
    )

    return {
        "date": today,
        "session_id": today,
        "result": result.content if result else None,
        "executed": executor_workflow.session_state.get("executed", []),
    }


__all__ = ["executor_workflow", "run_executor"]
