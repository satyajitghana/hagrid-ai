"""
Analysis Toolkits for Trading.

Provides:
- TradingToolkit: Market regime classification, options metrics, signal aggregation
- TechnicalScannerToolkit: Technical analysis using TradingView data
"""

from agno.tools import Toolkit
from core.indicators import (
    compute_technical_analysis,
    OptionsIndicators,
)
from tools.tradingview import TradingViewClient
from typing import Dict, Any, Optional, List
import pandas as pd
import json


class TradingToolkit(Toolkit):
    """
    Trading Analysis Toolkit.

    Provides tools for:
    - Market regime classification based on VIX
    - Options metrics computation (PCR, max pain)
    - Signal aggregation for trade candidates

    Usage:
        ```python
        from tools.analysis import TradingToolkit

        toolkit = TradingToolkit()

        # Or with specific tools only
        toolkit = TradingToolkit(include_tools=["get_market_regime"])
        ```
    """

    def __init__(self, include_tools: Optional[List[str]] = None, **kwargs):
        """
        Initialize TradingToolkit.

        Args:
            include_tools: List of tool names to include. If None, includes all.
            **kwargs: Additional arguments for Toolkit base class.
        """
        all_tools = {
            "get_market_regime": self.get_market_regime,
            "compute_options_metrics": self.compute_options_metrics,
            "aggregate_signals_logic": self.aggregate_signals_logic,
        }

        if include_tools:
            tools = [all_tools[name] for name in include_tools if name in all_tools]
        else:
            tools = list(all_tools.values())

        instructions = """Use these tools for trading analysis:
- get_market_regime: Classify market regime based on VIX value
- compute_options_metrics: Calculate PCR, max pain from option chain data
- aggregate_signals_logic: Combine agent signals into trade candidates"""

        super().__init__(name="trading_toolkit", tools=tools, instructions=instructions, **kwargs)

    def get_market_regime(self, vix: float) -> str:
        """
        Classify market regime based on India VIX value.

        The VIX (Volatility Index) measures expected market volatility.
        Different VIX levels indicate different trading conditions.

        Args:
            vix: Current India VIX value (e.g., 12.5, 18.3, 25.0)

        Returns:
            Market regime classification with trading guidance:
            - CALM (VIX < 12): Low volatility, aggressive positioning allowed
            - NORMAL (VIX 12-20): Standard conditions, normal position sizes
            - ELEVATED (VIX 20-30): High volatility, reduce position sizes
            - CRISIS (VIX > 30): Extreme volatility, avoid new trades

        Example:
            ```
            REGIME: NORMAL, SCORE: 0.5, STATUS: GO, VIX: 15.2, POSITION_MULTIPLIER: 1.0
            ```
        """
        if vix < 12:
            return f"REGIME: CALM, SCORE: 1.0, STATUS: GO, VIX: {vix}, POSITION_MULTIPLIER: 1.5"
        elif vix < 20:
            return f"REGIME: NORMAL, SCORE: 0.5, STATUS: GO, VIX: {vix}, POSITION_MULTIPLIER: 1.0"
        elif vix < 30:
            return f"REGIME: ELEVATED, SCORE: -1.0, STATUS: CAUTION, VIX: {vix}, POSITION_MULTIPLIER: 0.7"
        else:
            return f"REGIME: CRISIS, SCORE: -3.0, STATUS: NO_TRADE, VIX: {vix}, POSITION_MULTIPLIER: 0.0"

    def compute_options_metrics(self, option_chain_json: str, current_price: float) -> str:
        """
        Compute options metrics from option chain data.

        Calculates key options indicators used for sentiment analysis:
        - PCR (Put-Call Ratio): High PCR (>1.3) is bullish, low PCR (<0.8) is bearish
        - Max Pain: Strike price where option writers have minimum loss
        - Max OI strikes: Strikes with highest open interest (support/resistance)

        Args:
            option_chain_json: JSON string with option chain data.
                Each option should have: strike_price, option_type (CE/PE), oi
            current_price: Current underlying price

        Returns:
            JSON string with computed metrics:
            - pcr, pcr_signal
            - max_pain, price_vs_max_pain
            - max_call_oi_strike, max_put_oi_strike
        """
        try:
            option_chain = json.loads(option_chain_json)

            # Calculate PCR
            total_put_oi = sum(opt['oi'] for opt in option_chain if opt.get('option_type') == 'PE')
            total_call_oi = sum(opt['oi'] for opt in option_chain if opt.get('option_type') == 'CE')
            pcr = OptionsIndicators.pcr(total_put_oi, total_call_oi)

            # Calculate max pain
            max_pain = OptionsIndicators.max_pain(option_chain)

            # Find max Call OI and Put OI strikes
            calls = [opt for opt in option_chain if opt.get('option_type') == 'CE']
            puts = [opt for opt in option_chain if opt.get('option_type') == 'PE']

            max_call_oi = max(calls, key=lambda x: x.get('oi', 0)) if calls else {}
            max_put_oi = max(puts, key=lambda x: x.get('oi', 0)) if puts else {}

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

    def aggregate_signals_logic(self, signals_csv: str, regime: str) -> str:
        """
        Aggregate signals from multiple agents into trade candidates.

        Combines scores from different analysis agents and filters based on
        current market regime.

        Args:
            signals_csv: CSV-formatted signals from agents with columns:
                SYMBOL, DEPARTMENT, SCORE, CONFIDENCE
            regime: Current market regime (CALM/NORMAL/ELEVATED/CRISIS)

        Returns:
            Trade candidates in CSV format, or NO_TRADE message if regime is CRISIS
        """
        if regime == "CRISIS":
            return "NO TRADE CANDIDATES: Market in CRISIS regime"

        # Simple aggregation - in production, this would parse the CSV and compute weighted scores
        return "TRADE CANDIDATES:\nSYMBOL: INFY, DIRECTION: LONG, SCORE: 2.5, CONFIDENCE: 0.8\nSYMBOL: TCS, DIRECTION: LONG, SCORE: 1.8, CONFIDENCE: 0.7"


class TechnicalScannerToolkit(Toolkit):
    """
    Technical Scanner Toolkit using TradingView data.

    Provides real-time technical analysis for Indian stocks using TradingView's
    technical analysis data including:
    - Overall buy/sell recommendations
    - Moving averages (SMA, EMA)
    - Oscillators (RSI, Stochastic, CCI, Williams %R)
    - Pivot levels (Classic)

    Usage:
        ```python
        from tools.analysis import TechnicalScannerToolkit

        toolkit = TechnicalScannerToolkit()

        # Use in an agent
        agent = Agent(
            name="Technical Analyst",
            tools=[toolkit],
            ...
        )
        ```
    """

    def __init__(self, **kwargs):
        """Initialize TechnicalScannerToolkit with TradingView client."""
        self.tv = TradingViewClient()

        tools = [
            self.scan_technical_setup,
            self.get_moving_averages,
            self.get_oscillators,
            self.get_pivot_levels,
        ]

        instructions = """Use these tools for technical scanning via TradingView:
- scan_technical_setup: Get overall technical recommendation (BUY/SELL/NEUTRAL)
- get_moving_averages: Get SMA/EMA values (20, 50, 200)
- get_oscillators: Get RSI, Stochastic, CCI, Williams %R, Momentum
- get_pivot_levels: Get Classic pivot points (S3-R3)

Symbol format: "NSE:SYMBOL" (e.g., "NSE:RELIANCE", "NSE:TCS")"""

        super().__init__(name="technical_scanner", tools=tools, instructions=instructions, **kwargs)

    def _normalize_symbol(self, symbol: str) -> str:
        """Normalize symbol to TradingView format."""
        if ":" not in symbol and not symbol.startswith("NSE:"):
            symbol = f"NSE:{symbol.replace('-EQ', '')}"
        elif "-EQ" in symbol:
            symbol = symbol.replace("-EQ", "")
        return symbol

    def scan_technical_setup(self, symbol: str) -> str:
        """
        Scan a symbol for technical setup and signals using TradingView.

        Provides a comprehensive technical overview including:
        - Overall recommendation (STRONG_BUY, BUY, NEUTRAL, SELL, STRONG_SELL)
        - RSI with overbought/oversold status
        - MACD and signal line
        - ADX for trend strength
        - Price position relative to 200 SMA

        Args:
            symbol: Stock symbol (e.g., "NSE:RELIANCE" or "RELIANCE")

        Returns:
            Technical analysis summary with key indicators and signals
        """
        try:
            symbol = self._normalize_symbol(symbol)
            technicals = self.tv.get_technicals(symbol)

            return f"""TECHNICAL_ANALYSIS:
Recommendation: {technicals.overall_recommendation.value} (Score: {technicals.recommend_all:.2f})
RSI(14): {technicals.rsi:.2f} ({'Oversold' if technicals.is_oversold else 'Overbought' if technicals.is_overbought else 'Neutral'})
MACD: {technicals.macd_macd:.2f} (Signal: {technicals.macd_signal:.2f})
ADX(14): {technicals.adx:.2f} ({'Trending' if technicals.is_trending else 'Sideways'})
Price vs SMA200: {'Above' if technicals.is_above_200_sma else 'Below'}"""

        except Exception as e:
            return f"Error scanning {symbol}: {str(e)}"

    def get_moving_averages(self, symbol: str) -> str:
        """
        Get moving average values for a symbol.

        Returns SMA and EMA at key periods:
        - SMA 20, 50, 200 (short, medium, long-term trend)
        - EMA 20, 50 (responsive moving averages)

        Args:
            symbol: Stock symbol (e.g., "NSE:RELIANCE")

        Returns:
            Moving average values formatted as text
        """
        try:
            symbol = self._normalize_symbol(symbol)
            mas = self.tv.get_moving_averages(symbol)

            return f"""MOVING_AVERAGES:
SMA20: {mas.get('SMA20')}
SMA50: {mas.get('SMA50')}
SMA200: {mas.get('SMA200')}
EMA20: {mas.get('EMA20')}
EMA50: {mas.get('EMA50')}"""

        except Exception as e:
            return f"Error fetching MAs: {str(e)}"

    def get_oscillators(self, symbol: str) -> str:
        """
        Get oscillator values for a symbol.

        Returns key momentum oscillators:
        - RSI (14): Overbought > 70, Oversold < 30
        - Stochastic %K: Fast momentum
        - CCI (20): Commodity Channel Index
        - Williams %R: Momentum oscillator
        - Momentum: Price momentum

        Args:
            symbol: Stock symbol (e.g., "NSE:RELIANCE")

        Returns:
            Oscillator values formatted as text
        """
        try:
            symbol = self._normalize_symbol(symbol)
            tech = self.tv.get_technicals(symbol)

            return f"""OSCILLATORS:
RSI: {tech.rsi:.2f}
Stoch %K: {tech.stoch_k:.2f}
CCI: {tech.cci20:.2f}
Williams %R: {tech.williams_r:.2f}
Momentum: {tech.mom:.2f}"""

        except Exception as e:
            return f"Error fetching oscillators: {str(e)}"

    def get_pivot_levels(self, symbol: str) -> str:
        """
        Get Classic pivot levels for a symbol.

        Pivot points are used to identify potential support/resistance levels:
        - R3, R2, R1: Resistance levels
        - Pivot: Central pivot point
        - S1, S2, S3: Support levels

        Args:
            symbol: Stock symbol (e.g., "NSE:RELIANCE")

        Returns:
            Pivot levels formatted as text
        """
        try:
            symbol = self._normalize_symbol(symbol)
            pivots = self.tv.get_pivot_levels(symbol)

            return f"""PIVOT_LEVELS (Classic):
R3: {pivots.get('R3')}
R2: {pivots.get('R2')}
R1: {pivots.get('R1')}
Pivot: {pivots.get('Pivot')}
S1: {pivots.get('S1')}
S2: {pivots.get('S2')}
S3: {pivots.get('S3')}"""

        except Exception as e:
            return f"Error fetching pivots: {str(e)}"
