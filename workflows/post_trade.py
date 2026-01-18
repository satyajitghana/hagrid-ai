"""
Post-Trade Analysis Workflow

This workflow analyzes the day's trading performance:
1. Load all workflow sessions and trades for today
2. Compare predictions vs outcomes
3. Calculate performance metrics
4. Generate detailed report with learnings
5. Store report for future reference

Runs at 4:00 PM after market closes.
"""

from datetime import date

from agno.workflow import Workflow, Step
from agno.workflow.types import StepInput, StepOutput
from sqlmodel import Session, select

from workflows import workflow_db
from workflows.intraday_cycle import intraday_workflow
from agents.post_trade import post_trade_agent
from core.models import Trade, engine
from core.config import get_settings

settings = get_settings()


def load_all_day_data(step_input: StepInput) -> StepOutput:
    """
    Load all workflow sessions and trades for today.

    Gathers data from:
    - Intraday analysis workflow (predictions)
    - Trade table (actual trades)
    - News workflow (market context)
    """
    today = date.today().isoformat()

    # Get intraday analysis session (predictions)
    predictions = []
    regime = None
    try:
        intraday_session = intraday_workflow.get_session(session_id=today)
        if intraday_session:
            predictions = intraday_session.session_data.get("picks", [])
            regime = intraday_session.session_data.get("regime")
    except Exception:
        pass

    if step_input.workflow_session:
        step_input.workflow_session.session_data["predictions"] = predictions
        step_input.workflow_session.session_data["regime"] = regime

    # Get all trades for today from database
    with Session(engine) as db:
        statement = select(Trade).where(Trade.date == today)
        trades = db.exec(statement).all()

    trades_data = [
        {
            "id": t.id,
            "symbol": t.symbol,
            "direction": t.direction,
            "entry_price": t.entry_price,
            "exit_price": t.exit_price,
            "quantity": t.quantity,
            "entry_time": t.entry_time,
            "exit_time": t.exit_time,
            "stop_loss": t.stop_loss,
            "take_profit": t.take_profit,
            "realized_pnl": t.realized_pnl,
            "status": t.status,
            "exit_reason": t.exit_reason,
        }
        for t in trades
    ]

    if step_input.workflow_session:
        step_input.workflow_session.session_data["trades"] = trades_data

    # Calculate summary metrics
    total_pnl = sum(t.realized_pnl or 0 for t in trades if t.status == "CLOSED")
    winners = [t for t in trades if t.status == "CLOSED" and (t.realized_pnl or 0) > 0]
    losers = [t for t in trades if t.status == "CLOSED" and (t.realized_pnl or 0) < 0]
    open_trades = [t for t in trades if t.status == "OPEN"]

    win_rate = len(winners) / max(len(winners) + len(losers), 1) * 100
    avg_win = sum(t.realized_pnl or 0 for t in winners) / max(len(winners), 1)
    avg_loss = abs(sum(t.realized_pnl or 0 for t in losers)) / max(len(losers), 1)

    metrics = {
        "total_trades": len(trades),
        "closed_trades": len(winners) + len(losers),
        "open_trades": len(open_trades),
        "winners": len(winners),
        "losers": len(losers),
        "total_pnl": total_pnl,
        "pnl_pct": total_pnl / settings.BASE_CAPITAL * 100,
        "win_rate": win_rate,
        "avg_win": avg_win,
        "avg_loss": avg_loss,
        "reward_risk_ratio": avg_win / max(avg_loss, 1),
        "target_pnl": settings.BASE_CAPITAL * settings.TARGET_DAILY_RETURN_PERCENT / 100,
    }

    if step_input.workflow_session:
        step_input.workflow_session.session_data["metrics"] = metrics

    # Get news context
    try:
        from workflows.news_workflow import news_workflow
        news_session = news_workflow.get_session(session_id=today)
        if news_session and step_input.workflow_session:
            step_input.workflow_session.session_data["news_context"] = news_session.session_data
    except Exception:
        if step_input.workflow_session:
            step_input.workflow_session.session_data["news_context"] = {}

    return StepOutput(
        content=f"Loaded {len(trades_data)} trades for analysis. "
        f"P&L: ₹{total_pnl:.0f} ({metrics['pnl_pct']:.2f}%), "
        f"Win Rate: {win_rate:.1f}%"
    )


def store_report(step_input: StepInput) -> StepOutput:
    """
    Store the analysis report in session state.
    """
    report = step_input.previous_step_content

    if step_input.workflow_session:
        step_input.workflow_session.session_data["report"] = report

    return StepOutput(
        content=f"Post-trade analysis complete. Report stored."
    )


# Define the Post-Trade Analysis Workflow
post_trade_workflow = Workflow(
    name="Post-Trade Analysis",

    # Database for session storage
    db=workflow_db,

    # Enable workflow history for multi-day pattern analysis
    add_workflow_history_to_steps=True,
    num_history_runs=20,  # Last 20 trading days

    # Session state for analysis data
    session_state={
        "predictions": [],
        "trades": [],
        "metrics": {},
        "news_context": {},
        "regime": None,
        "report": "",
    },

    steps=[
        Step(
            name="Load Day Data",
            executor=load_all_day_data,
            description="Load all workflow sessions and trades for today"
        ),
        Step(
            name="Analyze Performance",
            agent=post_trade_agent,
            description="Analyze trading performance and generate report"
        ),
        Step(
            name="Store Report",
            executor=store_report,
            description="Store analysis report in session state"
        ),
    ]
)


async def run_post_trade_analysis(input_text: str = None) -> dict:
    """
    Run the post-trade analysis workflow.

    Args:
        input_text: Optional custom input.

    Returns:
        dict with analysis result
    """
    today = date.today().isoformat()

    if input_text is None:
        input_text = (
            f"Analyze today's ({today}) trading performance. "
            f"Compare predictions vs actual outcomes. "
            f"Calculate performance metrics and win rate. "
            f"Identify what worked and what didn't. "
            f"Provide actionable recommendations for improvement. "
            f"Generate a detailed markdown report."
        )

    result = await post_trade_workflow.arun(
        input=input_text,
        session_id=today
    )

    return {
        "date": today,
        "session_id": today,
        "result": result.content if result else None,
        "metrics": post_trade_workflow.session_state.get("metrics", {}),
        "report": post_trade_workflow.session_state.get("report", ""),
    }


__all__ = ["post_trade_workflow", "run_post_trade_analysis"]
