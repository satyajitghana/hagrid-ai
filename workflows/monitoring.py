"""
Position Monitoring Workflow

This workflow monitors open positions throughout the trading day:
1. Load open trades from Trade table
2. Get latest news context from news_workflow
3. Analyze positions and decide on adjustments
4. Execute adjustments (trailing stops, exits)
5. Update Trade table with results

Runs every 20 minutes during market hours (9:30 AM - 3:20 PM).
"""

from datetime import date

from agno.workflow import Workflow, Step
from agno.workflow.types import StepInput, StepOutput
from sqlmodel import Session, select

from workflows import workflow_db
from agents.monitoring import monitoring_agent
from core.models import Trade, engine
from core.config import get_settings

settings = get_settings()


def load_open_positions(step_input: StepInput) -> StepOutput:
    """
    Load open trades from Trade table and broker.

    Also fetches latest news summary from news_workflow if available.
    """
    today = date.today().isoformat()

    # Load open trades from database
    with Session(engine) as db:
        statement = select(Trade).where(
            Trade.date == today,
            Trade.status == "OPEN"
        )
        trades = db.exec(statement).all()

    open_trades = [
        {
            "id": t.id,
            "symbol": t.symbol,
            "direction": t.direction,
            "entry_price": t.entry_price,
            "quantity": t.quantity,
            "entry_time": t.entry_time,
            "stop_loss": t.stop_loss,
            "take_profit": t.take_profit,
            "order_id": t.order_id,
            "sl_order_id": t.sl_order_id,
        }
        for t in trades
    ]

    session_data = step_input.workflow_session.session_data if step_input.workflow_session else {}

    # Store in session state
    if step_input.workflow_session:
        step_input.workflow_session.session_data["open_trades"] = open_trades

    # Try to get news context from news workflow
    try:
        from workflows.news_workflow import news_workflow
        news_session = news_workflow.get_session(session_id=today)
        if news_session and step_input.workflow_session:
            step_input.workflow_session.session_data["news_context"] = news_session.session_data
    except Exception:
        if step_input.workflow_session:
            step_input.workflow_session.session_data["news_context"] = {}

    # Calculate cumulative P&L tracking info
    if step_input.workflow_session:
        step_input.workflow_session.session_data["capital"] = settings.BASE_CAPITAL
        step_input.workflow_session.session_data["target_pnl"] = (
            settings.BASE_CAPITAL * settings.TARGET_DAILY_RETURN_PERCENT / 100
        )
        step_input.workflow_session.session_data["max_loss"] = (
            settings.BASE_CAPITAL * settings.MAX_DAILY_LOSS_PERCENT / 100
        )

    target_pnl = settings.BASE_CAPITAL * settings.TARGET_DAILY_RETURN_PERCENT / 100
    max_loss = settings.BASE_CAPITAL * settings.MAX_DAILY_LOSS_PERCENT / 100

    return StepOutput(
        content=f"Monitoring {len(open_trades)} open positions. "
        f"Target P&L: ₹{target_pnl:.0f}, "
        f"Max Loss: ₹{max_loss:.0f}"
    )


def apply_adjustments(step_input: StepInput) -> StepOutput:
    """
    Apply adjustments from monitoring agent to the Trade table.

    Parses the monitoring agent's output and updates trade records.
    """
    session_data = step_input.workflow_session.session_data if step_input.workflow_session else {}
    adjustments = session_data.get("adjustments", [])
    monitoring_result = step_input.previous_step_content

    # Store monitoring result
    if step_input.workflow_session:
        step_input.workflow_session.session_data["monitoring_result"] = monitoring_result

    if not adjustments:
        return StepOutput(
            content=f"Monitoring complete. Agent analysis: {monitoring_result}"
        )

    # Apply adjustments to Trade table
    updates = []
    with Session(engine) as db:
        for adj in adjustments:
            trade_id = adj.get("trade_id")
            action = adj.get("action")

            if not trade_id:
                continue

            trade = db.get(Trade, trade_id)
            if not trade:
                continue

            if action == "MODIFY_SL":
                trade.stop_loss = adj.get("new_sl", trade.stop_loss)
                updates.append(f"{trade.symbol}: SL updated to {trade.stop_loss}")

            elif action == "EXIT":
                trade.status = "CLOSED"
                trade.exit_price = adj.get("exit_price")
                trade.exit_time = adj.get("exit_time")
                trade.exit_reason = adj.get("reason", "MANUAL")
                if trade.exit_price and trade.entry_price:
                    if trade.direction == "LONG":
                        pnl = (trade.exit_price - trade.entry_price) * trade.quantity
                    else:
                        pnl = (trade.entry_price - trade.exit_price) * trade.quantity
                    trade.realized_pnl = pnl
                updates.append(f"{trade.symbol}: Closed at {trade.exit_price}")

        db.commit()

    return StepOutput(
        content=f"Applied {len(updates)} adjustments: {'; '.join(updates)}"
    )


# Define the Monitoring Workflow
monitoring_workflow = Workflow(
    name="Position Monitor",

    # Database for session storage
    db=workflow_db,

    # Session state for position tracking
    session_state={
        "open_trades": [],
        "news_context": {},
        "adjustments": [],
        "monitoring_result": None,
        "capital": 0,
        "target_pnl": 0,
        "max_loss": 0,
    },

    steps=[
        Step(
            name="Load Positions",
            executor=load_open_positions,
            description="Load open trades from database and news context"
        ),
        Step(
            name="Analyze Positions",
            agent=monitoring_agent,
            description="Analyze positions for SL adjustments or exits"
        ),
        Step(
            name="Apply Adjustments",
            executor=apply_adjustments,
            description="Apply position adjustments to Trade table"
        ),
    ]
)


async def run_monitoring(input_text: str = None) -> dict:
    """
    Run the monitoring workflow.

    Args:
        input_text: Optional custom input.

    Returns:
        dict with monitoring result
    """
    today = date.today().isoformat()

    if input_text is None:
        input_text = (
            f"Monitor all open positions for {today}. "
            f"Check for stop loss adjustments needed based on ATR. "
            f"Identify any positions that should be closed. "
            f"Never go negative on daily P&L. Trail stops for winners."
        )

    result = await monitoring_workflow.arun(
        input=input_text,
        session_id=today
    )

    return {
        "date": today,
        "session_id": today,
        "result": result.content if result else None,
        "open_trades": monitoring_workflow.session_state.get("open_trades", []),
        "adjustments": monitoring_workflow.session_state.get("adjustments", []),
    }


__all__ = ["monitoring_workflow", "run_monitoring"]
