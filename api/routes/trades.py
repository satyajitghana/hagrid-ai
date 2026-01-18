"""
Trade History API Routes

Provides endpoints for:
- GET /api/trades/daily - Get trades for a specific date
- GET /api/trades/history - Get trade history with filters
- GET /api/trades/{trade_id} - Get specific trade details
- GET /api/trades/summary - Get trading summary/statistics
"""

from datetime import date, timedelta
from typing import Optional, List

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from sqlmodel import Session, select, func

from core.models import Trade, engine

router = APIRouter(prefix="/api/trades", tags=["trades"])


# ==============================================================================
# Response Models
# ==============================================================================

class TradeResponse(BaseModel):
    """Trade response model."""
    id: int
    date: str
    symbol: str
    direction: str
    entry_price: float
    exit_price: Optional[float]
    quantity: int
    entry_time: str
    exit_time: Optional[str]
    stop_loss: float
    take_profit: float
    realized_pnl: Optional[float]
    status: str
    order_id: Optional[str]
    sl_order_id: Optional[str]
    exit_reason: Optional[str]


class TradeSummary(BaseModel):
    """Trading summary statistics."""
    date: str
    total_trades: int
    open_trades: int
    closed_trades: int
    winners: int
    losers: int
    win_rate: float
    total_pnl: float
    pnl_percent: float
    avg_win: float
    avg_loss: float
    best_trade: Optional[str]
    worst_trade: Optional[str]


class DailyTradesResponse(BaseModel):
    """Response for daily trades endpoint."""
    date: str
    trades: List[TradeResponse]
    summary: TradeSummary


# ==============================================================================
# Endpoints
# ==============================================================================

@router.get("/daily", response_model=DailyTradesResponse)
async def get_daily_trades(
    trade_date: Optional[str] = Query(None, description="Date in YYYY-MM-DD format. Defaults to today.")
):
    """
    Get all trades for a specific date.

    Returns trades and summary statistics for the specified date.
    """
    target_date = trade_date or date.today().isoformat()

    with Session(engine) as db:
        statement = select(Trade).where(Trade.date == target_date)
        trades = db.exec(statement).all()

    if not trades:
        return DailyTradesResponse(
            date=target_date,
            trades=[],
            summary=TradeSummary(
                date=target_date,
                total_trades=0,
                open_trades=0,
                closed_trades=0,
                winners=0,
                losers=0,
                win_rate=0.0,
                total_pnl=0.0,
                pnl_percent=0.0,
                avg_win=0.0,
                avg_loss=0.0,
                best_trade=None,
                worst_trade=None,
            )
        )

    # Calculate summary
    closed = [t for t in trades if t.status == "CLOSED"]
    open_trades = [t for t in trades if t.status == "OPEN"]
    winners = [t for t in closed if (t.realized_pnl or 0) > 0]
    losers = [t for t in closed if (t.realized_pnl or 0) < 0]

    total_pnl = sum(t.realized_pnl or 0 for t in closed)
    win_rate = len(winners) / max(len(closed), 1) * 100
    avg_win = sum(t.realized_pnl or 0 for t in winners) / max(len(winners), 1)
    avg_loss = abs(sum(t.realized_pnl or 0 for t in losers)) / max(len(losers), 1)

    # Find best and worst trades
    best = max(closed, key=lambda t: t.realized_pnl or 0, default=None)
    worst = min(closed, key=lambda t: t.realized_pnl or 0, default=None)

    from core.config import get_settings
    settings = get_settings()
    pnl_percent = total_pnl / settings.BASE_CAPITAL * 100

    trade_responses = [
        TradeResponse(
            id=t.id,
            date=t.date,
            symbol=t.symbol,
            direction=t.direction,
            entry_price=t.entry_price,
            exit_price=t.exit_price,
            quantity=t.quantity,
            entry_time=t.entry_time,
            exit_time=t.exit_time,
            stop_loss=t.stop_loss,
            take_profit=t.take_profit,
            realized_pnl=t.realized_pnl,
            status=t.status,
            order_id=t.order_id,
            sl_order_id=t.sl_order_id,
            exit_reason=t.exit_reason,
        )
        for t in trades
    ]

    return DailyTradesResponse(
        date=target_date,
        trades=trade_responses,
        summary=TradeSummary(
            date=target_date,
            total_trades=len(trades),
            open_trades=len(open_trades),
            closed_trades=len(closed),
            winners=len(winners),
            losers=len(losers),
            win_rate=win_rate,
            total_pnl=total_pnl,
            pnl_percent=pnl_percent,
            avg_win=avg_win,
            avg_loss=avg_loss,
            best_trade=best.symbol if best else None,
            worst_trade=worst.symbol if worst else None,
        )
    )


@router.get("/history")
async def get_trade_history(
    days: int = Query(7, description="Number of days to look back"),
    symbol: Optional[str] = Query(None, description="Filter by symbol"),
    status: Optional[str] = Query(None, description="Filter by status (OPEN/CLOSED/STOPPED_OUT)"),
    direction: Optional[str] = Query(None, description="Filter by direction (LONG/SHORT)"),
):
    """
    Get trade history with optional filters.

    Returns trades from the last N days with filtering options.
    """
    start_date = (date.today() - timedelta(days=days)).isoformat()

    with Session(engine) as db:
        statement = select(Trade).where(Trade.date >= start_date)

        if symbol:
            statement = statement.where(Trade.symbol == symbol)
        if status:
            statement = statement.where(Trade.status == status)
        if direction:
            statement = statement.where(Trade.direction == direction)

        statement = statement.order_by(Trade.date.desc(), Trade.entry_time.desc())
        trades = db.exec(statement).all()

    return {
        "start_date": start_date,
        "end_date": date.today().isoformat(),
        "total": len(trades),
        "filters": {
            "symbol": symbol,
            "status": status,
            "direction": direction,
        },
        "trades": [
            {
                "id": t.id,
                "date": t.date,
                "symbol": t.symbol,
                "direction": t.direction,
                "entry_price": t.entry_price,
                "exit_price": t.exit_price,
                "quantity": t.quantity,
                "status": t.status,
                "realized_pnl": t.realized_pnl,
                "exit_reason": t.exit_reason,
            }
            for t in trades
        ]
    }


@router.get("/{trade_id}", response_model=TradeResponse)
async def get_trade(trade_id: int):
    """
    Get details for a specific trade.
    """
    with Session(engine) as db:
        trade = db.get(Trade, trade_id)

    if not trade:
        raise HTTPException(status_code=404, detail=f"Trade {trade_id} not found")

    return TradeResponse(
        id=trade.id,
        date=trade.date,
        symbol=trade.symbol,
        direction=trade.direction,
        entry_price=trade.entry_price,
        exit_price=trade.exit_price,
        quantity=trade.quantity,
        entry_time=trade.entry_time,
        exit_time=trade.exit_time,
        stop_loss=trade.stop_loss,
        take_profit=trade.take_profit,
        realized_pnl=trade.realized_pnl,
        status=trade.status,
        order_id=trade.order_id,
        sl_order_id=trade.sl_order_id,
        exit_reason=trade.exit_reason,
    )


@router.get("/summary/weekly")
async def get_weekly_summary():
    """
    Get weekly trading summary.

    Returns aggregated statistics for the past 7 days.
    """
    start_date = (date.today() - timedelta(days=7)).isoformat()

    with Session(engine) as db:
        statement = select(Trade).where(
            Trade.date >= start_date,
            Trade.status == "CLOSED"
        )
        trades = db.exec(statement).all()

    if not trades:
        return {
            "period": f"{start_date} to {date.today().isoformat()}",
            "trading_days": 0,
            "total_trades": 0,
            "win_rate": 0.0,
            "total_pnl": 0.0,
            "daily_breakdown": [],
        }

    # Group by date
    by_date = {}
    for t in trades:
        if t.date not in by_date:
            by_date[t.date] = []
        by_date[t.date].append(t)

    daily_breakdown = []
    for d, day_trades in sorted(by_date.items()):
        winners = [t for t in day_trades if (t.realized_pnl or 0) > 0]
        pnl = sum(t.realized_pnl or 0 for t in day_trades)
        daily_breakdown.append({
            "date": d,
            "trades": len(day_trades),
            "winners": len(winners),
            "win_rate": len(winners) / len(day_trades) * 100,
            "pnl": pnl,
        })

    winners = [t for t in trades if (t.realized_pnl or 0) > 0]
    total_pnl = sum(t.realized_pnl or 0 for t in trades)

    return {
        "period": f"{start_date} to {date.today().isoformat()}",
        "trading_days": len(by_date),
        "total_trades": len(trades),
        "winners": len(winners),
        "losers": len(trades) - len(winners),
        "win_rate": len(winners) / len(trades) * 100 if trades else 0,
        "total_pnl": total_pnl,
        "avg_daily_pnl": total_pnl / len(by_date) if by_date else 0,
        "daily_breakdown": daily_breakdown,
    }
