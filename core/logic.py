from core.types import MarketRegime, AgentSignal, SignalType, TradeCandidate, Order, OrderStatus
from typing import List, Dict, Any

def get_market_regime(vix: float) -> dict:
    """
    Tool function to determine market regime based on VIX.
    """
    if vix < 12:
        return {"regime": MarketRegime.CALM, "score": 1.0, "status": "GO"}
    elif vix < 20:
        return {"regime": MarketRegime.NORMAL, "score": 0.5, "status": "GO"}
    elif vix < 30:
        return {"regime": MarketRegime.ELEVATED, "score": -1.0, "status": "CAUTION"}
    else:
        return {"regime": MarketRegime.CRISIS, "score": -3.0, "status": "NO_TRADE"}

def calculate_sma_signal(symbol: str, prices: List[float]) -> dict:
    """
    Tool function to calculate simple technical signal (Mock).
    """
    if not prices:
        return {"signal": SignalType.NEUTRAL, "score": 0.0}
        
    current_price = prices[-1]
    # Mock SMA 200 logic (assuming prices list is long enough or just mocking it)
    sma_200 = current_price * 0.95 # Mock: Price is above SMA
    
    if current_price > sma_200:
        return {
            "signal": SignalType.BUY,
            "score": 1.5,
            "reasoning": f"Price {current_price} is above 200 SMA ({sma_200})",
            "metadata": {"indicators": {"SMA_200": sma_200}}
        }
    else:
        return {
            "signal": SignalType.SELL,
            "score": -1.5,
            "reasoning": f"Price {current_price} is below 200 SMA ({sma_200})",
            "metadata": {"indicators": {"SMA_200": sma_200}}
        }

def aggregate_signals_logic(signals: List[dict], regime: str) -> List[dict]:
    """
    Tool function to combine signals.
    """
    candidates = []
    # Simplified Logic
    if regime == "CRISIS":
        return []
        
    # Group by symbol
    grouped = {}
    for s in signals:
        sym = s.get("symbol")
        if sym:
            if sym not in grouped: grouped[sym] = []
            grouped[sym].append(s)
            
    for sym, sigs in grouped.items():
        total_score = sum(s.get("score", 0) for s in sigs)
        if total_score > 1.0:
            candidates.append({
                "symbol": sym,
                "direction": "LONG",
                "score": total_score,
                "confidence": 0.8 # Mock
            })
    return candidates