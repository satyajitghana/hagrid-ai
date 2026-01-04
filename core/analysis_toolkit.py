from agno.tools import Toolkit
from core.types import MarketRegime, SignalType
from core.indicators import compute_technical_analysis, TechnicalIndicators, OptionsIndicators, CorrelationIndicators
from typing import List, Dict, Any
import pandas as pd
import json

class TradingToolkit(Toolkit):
    """
    Trading Analysis Toolkit
    Provides computed technical indicators, options metrics, and correlation analysis.
    Agents receive computed values only - NO raw data passed.
    """
    
    def __init__(self, **kwargs):
        tools = [
            self.get_market_regime,
            self.compute_technical_indicators,
            self.compute_options_metrics,
            self.compute_correlation_metrics,
            self.aggregate_signals_logic
        ]
        super().__init__(name="trading_toolkit", tools=tools, **kwargs)

    def get_market_regime(self, vix: float) -> str:
        """
        Determines market regime based on VIX.
        
        Args:
            vix (float): The current Volatility Index value.
            
        Returns:
            str: Market regime classification in simple format
        """
        if vix < 12:
            return f"REGIME: CALM, SCORE: 1.0, STATUS: GO, VIX: {vix}, POSITION_MULTIPLIER: 1.5"
        elif vix < 20:
            return f"REGIME: NORMAL, SCORE: 0.5, STATUS: GO, VIX: {vix}, POSITION_MULTIPLIER: 1.0"
        elif vix < 30:
            return f"REGIME: ELEVATED, SCORE: -1.0, STATUS: CAUTION, VIX: {vix}, POSITION_MULTIPLIER: 0.7"
        else:
            return f"REGIME: CRISIS, SCORE: -3.0, STATUS: NO_TRADE, VIX: {vix}, POSITION_MULTIPLIER: 0.0"

    def compute_technical_indicators(self, symbol: str, ohlcv_json: str) -> str:
        """
        Computes ALL technical indicators from OHLCV data.
        Agent receives computed indicators only, NOT raw data.
        
        Args:
            symbol (str): Stock symbol
            ohlcv_json (str): JSON string with OHLCV data [{"timestamp": x, "open": o, "high": h, "low": l, "close": c, "volume": v}, ...]
            
        Returns:
            str: JSON string with all computed indicators
        """
        try:
            # Parse OHLCV data
            ohlcv_list = json.loads(ohlcv_json)
            if not ohlcv_list:
                return json.dumps({"error": "No data provided"})
            
            # Convert to DataFrame
            df = pd.DataFrame(ohlcv_list)
            
            # Compute all indicators
            indicators = compute_technical_analysis(df)
            indicators['symbol'] = symbol
            
            return json.dumps(indicators, indent=2)
        except Exception as e:
            return json.dumps({"error": str(e)})
    
    def compute_options_metrics(self, option_chain_json: str, current_price: float) -> str:
        """
        Computes options metrics from option chain data.
        
        Args:
            option_chain_json (str): JSON string with option chain data
            current_price (float): Current underlying price
            
        Returns:
            str: JSON string with computed options metrics
        """
        try:
            option_chain = json.loads(option_chain_json)
            
            # Calculate PCR
            total_put_oi = sum(opt['oi'] for opt in option_chain if opt['option_type'] == 'PE')
            total_call_oi = sum(opt['oi'] for opt in option_chain if opt['option_type'] == 'CE')
            pcr = OptionsIndicators.pcr(total_put_oi, total_call_oi)
            
            # Calculate max pain
            max_pain = OptionsIndicators.max_pain(option_chain)
            
            # Find max Call OI and Put OI strikes
            calls = [opt for opt in option_chain if opt['option_type'] == 'CE']
            puts = [opt for opt in option_chain if opt['option_type'] == 'PE']
            
            max_call_oi = max(calls, key=lambda x: x['oi']) if calls else {}
            max_put_oi = max(puts, key=lambda x: x['oi']) if puts else {}
            
            metrics = {
                "pcr": round(pcr, 2),
                "pcr_signal": "BULLISH" if pcr > 1.3 else "BEARISH" if pcr < 0.8 else "NEUTRAL",
                "max_pain": max_pain,
                "max_call_oi_strike": max_call_oi.get('strike_price'),
                "max_call_oi": max_call_oi.get('oi'),
                "max_put_oi_strike": max_put_oi.get('strike_price'),
                "max_put_oi": max_put_oi.get('oi'),
                "current_price": current_price,
                "price_vs_max_pain": round(((current_price - max_pain) / max_pain * 100), 2) if max_pain else None
            }
            
            return json.dumps(metrics, indent=2)
        except Exception as e:
            return json.dumps({"error": str(e)})
    
    def compute_correlation_metrics(self, series1_json: str, series2_json: str, symbol1: str, symbol2: str) -> str:
        """
        Computes correlation metrics for pairs trading.
        
        Args:
            series1_json (str): JSON array of prices for stock 1
            series2_json (str): JSON array of prices for stock 2
            symbol1 (str): Symbol 1
            symbol2 (str): Symbol 2
            
        Returns:
            str: JSON string with correlation metrics
        """
        try:
            prices1 = pd.Series(json.loads(series1_json))
            prices2 = pd.Series(json.loads(series2_json))
            
            # Calculate correlation
            corr_30 = CorrelationIndicators.correlation(prices1, prices2, 30)
            corr_60 = CorrelationIndicators.correlation(prices1, prices2, 60)
            
            # Calculate beta (hedge ratio)
            returns1 = prices1.pct_change().dropna()
            returns2 = prices2.pct_change().dropna()
            beta = CorrelationIndicators.beta(returns1, returns2)
            
            # Calculate spread and Z-score
            spread = prices1 - (beta * prices2)
            z_score = CorrelationIndicators.z_score(spread)
            
            # Calculate half-life
            half_life = CorrelationIndicators.half_life(spread)
            
            metrics = {
                "symbol1": symbol1,
                "symbol2": symbol2,
                "correlation_30d": round(corr_30, 3),
                "correlation_60d": round(corr_60, 3),
                "beta": round(beta, 3),
                "current_spread": round(spread.iloc[-1], 2),
                "mean_spread": round(spread.mean(), 2),
                "std_spread": round(spread.std(), 2),
                "z_score": round(z_score, 2),
                "z_score_signal": "LONG_S1_SHORT_S2" if z_score < -2 else "SHORT_S1_LONG_S2" if z_score > 2 else "NEUTRAL",
                "half_life_days": round(half_life, 1),
                "cointegrated": "YES" if abs(z_score) < 3 and half_life < 30 else "NO"
            }
            
            return json.dumps(metrics, indent=2)
        except Exception as e:
            return json.dumps({"error": str(e)})

    def aggregate_signals_logic(self, signals_csv: str, regime: str) -> str:
        """
        Aggregates signals to form trade candidates.
        
        Args:
            signals_csv (str): CSV-formatted signals from agents
            regime (str): Current market regime (CALM/NORMAL/ELEVATED/CRISIS)
            
        Returns:
            str: Trade candidates in CSV format
        """
        if regime == "CRISIS":
            return "NO TRADE CANDIDATES: Market in CRISIS regime"
        
        # Simple mock aggregation
        return f"TRADE CANDIDATES:\nSYMBOL: INFY, DIRECTION: LONG, SCORE: 2.5, CONFIDENCE: 0.8\nSYMBOL: TCS, DIRECTION: LONG, SCORE: 1.8, CONFIDENCE: 0.7"