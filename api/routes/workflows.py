"""
Workflow Sessions API Routes

Provides endpoints for:
- GET /api/workflows/sessions - Get workflow sessions
- GET /api/workflows/runs/{workflow_name}/{session_id} - Get run details
- GET /api/workflows/analysis/daily - Get daily analysis summary
- GET /api/workflows/picks/today - Get today's picks
"""

from datetime import date, timedelta
from typing import Optional, List, Dict, Any

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

router = APIRouter(prefix="/api/workflows", tags=["workflows"])


# ==============================================================================
# Response Models
# ==============================================================================

class SessionSummary(BaseModel):
    """Summary of a workflow session."""
    date: str
    has_data: bool
    regime: Optional[str]
    picks_count: int
    risk_validated: bool


class AnalysisSummary(BaseModel):
    """Daily analysis summary."""
    date: str
    regime: Optional[str]
    picks: List[Dict[str, Any]]
    department_reports: Dict[str, Any]
    risk_validated: bool


class PickSummary(BaseModel):
    """Summary of a trade pick."""
    symbol: str
    direction: str
    entry_price: Optional[str]
    stop_loss: Optional[str]
    take_profit: Optional[str]
    confidence: Optional[str]


# ==============================================================================
# Helper Functions
# ==============================================================================

def get_workflow_by_name(name: str):
    """Get workflow instance by name."""
    workflows = {
        "intraday": None,
        "executor": None,
        "monitoring": None,
        "news": None,
        "post_trade": None,
    }

    try:
        if name == "intraday":
            from workflows.intraday_cycle import intraday_workflow
            return intraday_workflow
        elif name == "executor":
            from workflows.executor import executor_workflow
            return executor_workflow
        elif name == "monitoring":
            from workflows.monitoring import monitoring_workflow
            return monitoring_workflow
        elif name == "news":
            from workflows.news_workflow import news_workflow
            return news_workflow
        elif name == "post_trade":
            from workflows.post_trade import post_trade_workflow
            return post_trade_workflow
    except ImportError:
        pass

    return workflows.get(name)


# ==============================================================================
# Endpoints
# ==============================================================================

@router.get("/sessions/{workflow_name}")
async def get_workflow_sessions(
    workflow_name: str,
    days: int = Query(7, description="Number of days to look back"),
):
    """
    Get recent workflow sessions for a specific workflow.

    Returns session summaries for the last N days.
    """
    workflow = get_workflow_by_name(workflow_name)

    if not workflow:
        raise HTTPException(
            status_code=404,
            detail=f"Workflow '{workflow_name}' not found. Available: intraday, executor, monitoring, news, post_trade"
        )

    sessions = []
    for i in range(days):
        day = (date.today() - timedelta(days=i)).isoformat()
        try:
            session = workflow.get_session(session_id=day)
            if session:
                state = session.session_state or {}
                sessions.append({
                    "date": day,
                    "has_data": True,
                    "regime": state.get("regime"),
                    "picks_count": len(state.get("picks", [])) if isinstance(state.get("picks"), list) else 0,
                    "session_state_keys": list(state.keys()),
                })
            else:
                sessions.append({
                    "date": day,
                    "has_data": False,
                })
        except Exception:
            sessions.append({
                "date": day,
                "has_data": False,
                "error": "Could not retrieve session",
            })

    return {
        "workflow": workflow_name,
        "sessions": sessions,
    }


@router.get("/runs/{workflow_name}/{session_id}")
async def get_workflow_run(workflow_name: str, session_id: str):
    """
    Get detailed run information for a workflow session.
    """
    workflow = get_workflow_by_name(workflow_name)

    if not workflow:
        raise HTTPException(
            status_code=404,
            detail=f"Workflow '{workflow_name}' not found"
        )

    try:
        session = workflow.get_session(session_id=session_id)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving session: {str(e)}"
        )

    if not session:
        raise HTTPException(
            status_code=404,
            detail=f"No session found for {workflow_name} on {session_id}"
        )

    return {
        "workflow": workflow_name,
        "session_id": session_id,
        "session_state": session.session_state,
        "runs": len(session.runs) if hasattr(session, 'runs') and session.runs else 0,
    }


@router.get("/analysis/daily")
async def get_daily_analysis(
    target_date: Optional[str] = Query(None, description="Date in YYYY-MM-DD format")
):
    """
    Get combined analysis for a trading day.

    Returns regime, picks, and department reports from the intraday workflow.
    """
    analysis_date = target_date or date.today().isoformat()

    try:
        from workflows.intraday_cycle import intraday_workflow
    except ImportError:
        raise HTTPException(
            status_code=500,
            detail="Could not import intraday workflow"
        )

    try:
        session = intraday_workflow.get_session(session_id=analysis_date)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving session: {str(e)}"
        )

    if not session:
        return {
            "date": analysis_date,
            "has_analysis": False,
            "message": "No analysis found for this date. Run the intraday workflow first.",
        }

    state = session.session_state or {}

    return {
        "date": analysis_date,
        "has_analysis": True,
        "regime": state.get("regime"),
        "picks": state.get("picks", []),
        "department_reports": state.get("department_reports", {}),
        "risk_validated": state.get("risk_validated", False),
    }


@router.get("/picks/today")
async def get_todays_picks():
    """
    Get today's trading picks from the intraday analysis.

    Returns the picks if analysis has been run, otherwise returns empty.
    """
    today = date.today().isoformat()

    try:
        from workflows.intraday_cycle import intraday_workflow
        session = intraday_workflow.get_session(session_id=today)
    except Exception:
        return {
            "date": today,
            "has_picks": False,
            "picks": [],
            "message": "Could not retrieve today's picks",
        }

    if not session:
        return {
            "date": today,
            "has_picks": False,
            "picks": [],
            "message": "No analysis run yet today",
        }

    state = session.session_state or {}
    picks = state.get("picks", [])
    regime = state.get("regime")

    return {
        "date": today,
        "has_picks": bool(picks),
        "regime": regime,
        "risk_validated": state.get("risk_validated", False),
        "picks": picks,
        "picks_count": len(picks) if isinstance(picks, list) else 0,
    }


@router.get("/news/latest")
async def get_latest_news():
    """
    Get the latest news summary from the news workflow.
    """
    today = date.today().isoformat()

    try:
        from workflows.news_workflow import news_workflow
        session = news_workflow.get_session(session_id=today)
    except Exception:
        return {
            "date": today,
            "has_news": False,
            "message": "Could not retrieve news summary",
        }

    if not session:
        return {
            "date": today,
            "has_news": False,
            "message": "No news summary available yet today",
        }

    state = session.session_state or {}

    return {
        "date": today,
        "has_news": True,
        "last_updated": state.get("last_updated"),
        "sentiment": state.get("sentiment", "NEUTRAL"),
        "key_events": state.get("key_events", []),
        "affected_symbols": state.get("affected_symbols", []),
        "latest_summary": state.get("latest_summary"),
    }


@router.get("/monitoring/status")
async def get_monitoring_status():
    """
    Get current position monitoring status.
    """
    today = date.today().isoformat()

    try:
        from workflows.monitoring import monitoring_workflow
        session = monitoring_workflow.get_session(session_id=today)
    except Exception:
        return {
            "date": today,
            "has_data": False,
            "message": "Could not retrieve monitoring status",
        }

    if not session:
        return {
            "date": today,
            "has_data": False,
            "message": "No monitoring data available yet today",
        }

    state = session.session_state or {}

    return {
        "date": today,
        "has_data": True,
        "open_trades": state.get("open_trades", []),
        "open_trades_count": len(state.get("open_trades", [])),
        "adjustments": state.get("adjustments", []),
        "monitoring_result": state.get("monitoring_result"),
        "capital": state.get("capital", 0),
        "target_pnl": state.get("target_pnl", 0),
        "max_loss": state.get("max_loss", 0),
    }


@router.get("/post-trade/report")
async def get_post_trade_report(
    target_date: Optional[str] = Query(None, description="Date in YYYY-MM-DD format")
):
    """
    Get post-trade analysis report for a specific date.
    """
    report_date = target_date or date.today().isoformat()

    try:
        from workflows.post_trade import post_trade_workflow
        session = post_trade_workflow.get_session(session_id=report_date)
    except Exception:
        return {
            "date": report_date,
            "has_report": False,
            "message": "Could not retrieve post-trade report",
        }

    if not session:
        return {
            "date": report_date,
            "has_report": False,
            "message": f"No post-trade analysis found for {report_date}",
        }

    state = session.session_state or {}

    return {
        "date": report_date,
        "has_report": True,
        "metrics": state.get("metrics", {}),
        "report": state.get("report", ""),
        "predictions": len(state.get("predictions", [])),
        "trades_analyzed": len(state.get("trades", [])),
    }


@router.get("/available")
async def get_available_workflows():
    """
    Get list of available workflows.
    """
    return {
        "workflows": [
            {
                "name": "intraday",
                "display_name": "Intraday Trading Cycle",
                "description": "Morning analysis workflow with hierarchical multi-agent system",
                "schedule": "9:00 AM Mon-Fri",
            },
            {
                "name": "executor",
                "display_name": "Order Executor",
                "description": "Execute orders based on intraday analysis picks",
                "schedule": "9:15 AM Mon-Fri",
            },
            {
                "name": "monitoring",
                "display_name": "Position Monitor",
                "description": "Monitor open positions, adjust stops, manage risk",
                "schedule": "Every 20 min during market hours",
            },
            {
                "name": "news",
                "display_name": "News Summarizer",
                "description": "Aggregate and summarize market news",
                "schedule": "Hourly during market hours",
            },
            {
                "name": "post_trade",
                "display_name": "Post-Trade Analysis",
                "description": "End of day performance analysis and reporting",
                "schedule": "4:00 PM Mon-Fri",
            },
        ]
    }
