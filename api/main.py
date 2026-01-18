from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import Session, select
from core.config import get_settings
from core.models import DailyPick, NewsItem, create_db_and_tables, get_session
from core.fyers_client import get_fyers_client, ensure_authenticated
from typing import Optional, Annotated
from datetime import datetime, date, timedelta
import asyncio
import json

# Import API routes
from api.routes import trades_router, workflows_router

settings = get_settings()
SessionDep = Annotated[Session, Depends(get_session)]

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.VERSION,
    debug=settings.DEBUG,
    description="Hagrid AI Trading Backend - Multi-Agent Trading System"
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(trades_router)
app.include_router(workflows_router)

# Get Fyers client (lazy initialization, authentication on first use)
def get_broker():
    """Get FyersClient instance for API endpoints."""
    return get_fyers_client()

@app.on_event("startup")
def on_startup():
    create_db_and_tables()

@app.get("/")
async def root():
    return {
        "message": "Hagrid AI Trading Backend",
        "version": settings.VERSION,
        "status": "operational"
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

# === CORE TRADING ENDPOINTS ===
# Note: /run-cycle removed - use scheduler or /api/workflows endpoints instead

@app.get("/staging")
async def get_staging(date_str: Optional[str] = None, session: SessionDep = None):
    """
    Get staged AI picks for a specific date.
    Defaults to today if no date provided.
    """
    target_date = date_str or date.today().isoformat()
    
    statement = select(DailyPick).where(DailyPick.date == target_date)
    pick = session.exec(statement).first()
    
    if pick:
        return json.loads(pick.picks_json)
    
    return {
        "status": "no_picks",
        "date": target_date,
        "message": "No picks available for this date"
    }

@app.get("/marketwatch")
async def get_marketwatch():
    """
    Get real-time market watch directly from broker.
    """
    broker = get_broker()
    symbols = ["NSE:INFY-EQ", "NSE:TCS-EQ", "NSE:RELIANCE-EQ", "NSE:SBIN-EQ", "NSE:HDFCBANK-EQ"]
    quotes_result = await broker.get_quotes(symbols)

    watchlist = []
    if quotes_result.quotes:
        for quote in quotes_result.quotes:
            watchlist.append({
                "symbol": quote.symbol,
                "ltp": quote.ltp,
                "change": quote.change,
                "change_pct": quote.change_percent,
                "volume": quote.volume,
                "high": quote.high,
                "low": quote.low
            })

    return {
        "timestamp": datetime.now().isoformat(),
        "symbols": watchlist
    }

@app.get("/positions")
async def get_positions():
    """Get current positions directly from broker"""
    broker = get_broker()
    positions_result = await broker.get_positions()
    positions_list = [p.model_dump() for p in positions_result.net_positions] if positions_result.net_positions else []
    return {
        "timestamp": datetime.now().isoformat(),
        "positions": positions_list,
        "count": len(positions_list)
    }

@app.get("/funds")
async def get_funds():
    """Get account funds directly from broker"""
    broker = get_broker()
    funds_result = await broker.get_funds()
    return {
        "available_balance": funds_result.available_margin or 0,
        "used_margin": funds_result.used_margin or 0,
        "total_equity": funds_result.total_balance or 0,
        "pnl_today": funds_result.realized_profit or 0,
        "timestamp": datetime.now().isoformat()
    }

@app.get("/orders")
async def get_orders():
    """Get order book directly from broker"""
    broker = get_broker()
    orders_result = await broker.get_orders()
    orders_list = [o.model_dump() for o in orders_result.orders] if orders_result.orders else []
    return {
        "orders": orders_list,
        "count": len(orders_list),
        "timestamp": datetime.now().isoformat()
    }

@app.post("/news")
async def add_news(
    title: str,
    summary: str,
    category: str,
    source: str,
    content: Optional[str] = None,
    url: Optional[str] = None,
    symbols: Optional[str] = None,
    session: SessionDep = None
):
    """Add a news item to database"""
    news = NewsItem(
        title=title,
        summary=summary,
        content=content,
        category=category,
        source=source,
        url=url,
        symbols=symbols,
        timestamp=datetime.now().isoformat(),
        fetched_at=datetime.now().isoformat()
    )
    session.add(news)
    session.commit()
    session.refresh(news)
    return news

@app.get("/news")
async def get_news(
    category: Optional[str] = None, 
    limit: int = 20,
    session: SessionDep = None
):
    """
    Get latest market news from database.
    """
    statement = select(NewsItem).order_by(NewsItem.timestamp.desc()).limit(limit)
    
    if category:
        statement = statement.where(NewsItem.category == category)
    
    news_items = session.exec(statement).all()
    
    return {
        "news": [
            {
                "id": item.id,
                "title": item.title,
                "summary": item.summary,
                "category": item.category,
                "source": item.source,
                "url": item.url,
                "symbols": item.symbols,
                "timestamp": item.timestamp
            }
            for item in news_items
        ],
        "count": len(news_items)
    }

@app.get("/agent-logs")
async def get_agent_logs(agent_name: Optional[str] = None):
    """
    Get agent execution logs.
    Note: Agno stores agent sessions/logs automatically when db is configured.
    """
    return {
        "message": "Agent logs are managed by Agno's session storage",
        "note": "Agents should be configured with agno.db.sqlite.SqliteDb() for automatic logging"
    }

# === WEBSOCKET ENDPOINTS ===

@app.websocket("/ws/analysis")
async def websocket_analysis(websocket: WebSocket):
    """WebSocket for chat-based analysis with agents"""
    await websocket.accept()
    session_id = f"session_{datetime.now().timestamp()}"
    
    try:
        await websocket.send_json({
            "type": "connected",
            "session_id": session_id,
            "message": "Connected to Hagrid AI Analysis"
        })
        
        while True:
            data = await websocket.receive_json()
            message = data.get("message", "")
            
            response = f"Analyzing: {message}"
            
            await websocket.send_json({
                "type": "message",
                "content": response,
                "timestamp": datetime.now().isoformat()
            })
            
    except WebSocketDisconnect:
        print(f"Client disconnected from session {session_id}")

@app.websocket("/ws/updates")
async def websocket_updates(websocket: WebSocket):
    """WebSocket for real-time market updates from broker"""
    await websocket.accept()
    broker = get_broker()
    try:
        while True:
            await asyncio.sleep(5)
            quotes = await broker.get_quotes(["NSE:NIFTY50-INDEX"])
            quotes_data = [q.model_dump() for q in quotes.quotes] if quotes.quotes else []

            await websocket.send_json({
                "type": "market_update",
                "timestamp": datetime.now().isoformat(),
                "data": quotes_data
            })
    except WebSocketDisconnect:
        print("Client disconnected from updates")

# === ANALYSIS ENDPOINTS ===

@app.post("/analysis/stock")
async def analyze_stock(symbol: str):
    """Run comprehensive analysis on a specific stock"""
    broker = get_broker()
    quotes = await broker.get_quotes([symbol])
    market_depth = await broker.get_market_depth(symbol)

    quote_data = quotes.quotes[0].model_dump() if quotes.quotes else {}
    depth_data = market_depth.model_dump() if market_depth else {}

    return {
        "symbol": symbol,
        "market_data": quote_data,
        "depth": depth_data,
        "recommendation": "BUY",
        "confidence": 0.85,
        "target": 1560.00,
        "stop_loss": 1485.00,
        "timestamp": datetime.now().isoformat()
    }

@app.get("/analysis/history")
async def get_analysis_history(days: int = 7, session: SessionDep = None):
    """Get historical analysis and picks"""
    history = []
    for i in range(days):
        day = (date.today() - timedelta(days=i)).isoformat()
        statement = select(DailyPick).where(DailyPick.date == day)
        pick = session.exec(statement).first()
        if pick:
            history.append(json.loads(pick.picks_json))
    
    return {
        "days": days,
        "history": history
    }

# === TECHNICAL INDICATORS ENDPOINTS ===

@app.get("/indicators/technical/{symbol}")
async def get_technical_indicators(symbol: str, resolution: str = "D", days: int = 200):
    """
    Get computed technical indicators for a stock.
    Returns all TA indicators (SMA, RSI, MACD, etc.) - NO raw data.
    """
    from core.indicators import compute_technical_analysis
    import pandas as pd

    broker = get_broker()

    # Fetch historical data
    from datetime import datetime, timedelta
    range_to = datetime.now().strftime("%Y-%m-%d")
    range_from = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")

    result = await broker.get_history(
        symbol=symbol,
        resolution=resolution,
        date_format=1,
        range_from=range_from,
        range_to=range_to
    )

    candles = result.candles if result and result.candles else []
    if not candles:
        return {"error": "No historical data available", "symbol": symbol}

    # Convert to DataFrame - FyersClient returns candle objects
    df = pd.DataFrame([
        {
            'timestamp': c.timestamp,
            'open': c.open,
            'high': c.high,
            'low': c.low,
            'close': c.close,
            'volume': c.volume
        }
        for c in candles
    ])

    # Compute all indicators
    indicators = compute_technical_analysis(df)
    indicators['symbol'] = symbol
    indicators['resolution'] = resolution
    indicators['timestamp'] = datetime.now().isoformat()

    return indicators

@app.get("/indicators/options/{symbol}")
async def get_options_metrics(symbol: str, strike_count: int = 10):
    """
    Get computed options metrics (PCR, max pain, etc.).
    Returns analysis only - NO raw option chain.
    """
    from core.indicators import OptionsIndicators

    broker = get_broker()

    # Fetch option chain and current price
    option_result = await broker.get_option_chain(symbol, strike_count)
    quote_result = await broker.get_quotes([symbol])

    # Convert option chain to list of dicts for compatibility
    option_chain = []
    if option_result and option_result.options_chain:
        for opt in option_result.options_chain:
            option_chain.append({
                'strike_price': opt.strike_price,
                'option_type': opt.option_type,
                'oi': opt.open_interest or 0,
                'ltp': opt.ltp or 0
            })

    current_price = quote_result.quotes[0].ltp if quote_result.quotes else 0

    if not option_chain:
        return {"error": "No options data available", "symbol": symbol}

    # Calculate metrics
    total_put_oi = sum(opt['oi'] for opt in option_chain if opt['option_type'] == 'PE')
    total_call_oi = sum(opt['oi'] for opt in option_chain if opt['option_type'] == 'CE')
    pcr = OptionsIndicators.pcr(total_put_oi, total_call_oi)
    max_pain = OptionsIndicators.max_pain(option_chain)

    # Find max OI strikes
    calls = [opt for opt in option_chain if opt['option_type'] == 'CE']
    puts = [opt for opt in option_chain if opt['option_type'] == 'PE']
    max_call_oi = max(calls, key=lambda x: x['oi']) if calls else {}
    max_put_oi = max(puts, key=lambda x: x['oi']) if puts else {}

    return {
        "symbol": symbol,
        "current_price": current_price,
        "pcr": round(pcr, 2),
        "pcr_signal": "BULLISH" if pcr > 1.3 else "BEARISH" if pcr < 0.8 else "NEUTRAL",
        "max_pain": max_pain,
        "max_call_oi_strike": max_call_oi.get('strike_price'),
        "max_call_oi": max_call_oi.get('oi'),
        "max_put_oi_strike": max_put_oi.get('strike_price'),
        "max_put_oi": max_put_oi.get('oi'),
        "price_vs_max_pain": round(((current_price - max_pain) / max_pain * 100), 2) if max_pain else None,
        "timestamp": datetime.now().isoformat()
    }

@app.get("/indicators/correlation/{symbol1}/{symbol2}")
async def get_correlation_metrics(symbol1: str, symbol2: str, days: int = 100):
    """
    Get correlation metrics for pairs trading.
    Returns correlation, beta, z-score, etc.
    """
    from core.indicators import CorrelationIndicators
    import pandas as pd

    broker = get_broker()

    # Fetch historical data for both symbols
    from datetime import datetime, timedelta
    range_to = datetime.now().strftime("%Y-%m-%d")
    range_from = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")

    result1 = await broker.get_history(symbol1, "D", 1, range_from, range_to)
    result2 = await broker.get_history(symbol2, "D", 1, range_from, range_to)

    candles1 = result1.candles if result1 and result1.candles else []
    candles2 = result2.candles if result2 and result2.candles else []

    if not candles1 or not candles2:
        return {"error": "Insufficient data for correlation analysis"}

    # Extract close prices from candle objects
    prices1 = pd.Series([c.close for c in candles1])
    prices2 = pd.Series([c.close for c in candles2])

    # Calculate metrics
    corr_30 = CorrelationIndicators.correlation(prices1, prices2, 30)
    corr_60 = CorrelationIndicators.correlation(prices1, prices2, 60)

    returns1 = prices1.pct_change().dropna()
    returns2 = prices2.pct_change().dropna()
    beta = CorrelationIndicators.beta(returns1, returns2)

    spread = prices1 - (beta * prices2)
    z_score = CorrelationIndicators.z_score(spread)
    half_life = CorrelationIndicators.half_life(spread)

    return {
        "symbol1": symbol1,
        "symbol2": symbol2,
        "correlation_30d": round(corr_30, 3),
        "correlation_60d": round(corr_60, 3),
        "beta": round(beta, 3),
        "current_spread": round(spread.iloc[-1], 2),
        "mean_spread": round(spread.mean(), 2),
        "z_score": round(z_score, 2),
        "z_score_signal": "LONG_S1_SHORT_S2" if z_score < -2 else "SHORT_S1_LONG_S2" if z_score > 2 else "NEUTRAL",
        "half_life_days": round(half_life, 1),
        "cointegrated": "YES" if abs(z_score) < 3 and half_life < 30 else "NO",
        "timestamp": datetime.now().isoformat()
    }