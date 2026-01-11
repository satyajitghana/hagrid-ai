"""
Technical Analysis Indicators Module
Computes all TA indicators using pandas/numpy - agents receive computed values, not raw data.
"""
import pandas as pd
import numpy as np
from typing import List, Dict, Optional, Tuple


class TechnicalIndicators:
    """Compute technical indicators from OHLCV data"""
    
    @staticmethod
    def sma(prices: pd.Series, period: int) -> pd.Series:
        """Simple Moving Average"""
        return prices.rolling(window=period).mean()
    
    @staticmethod
    def ema(prices: pd.Series, period: int) -> pd.Series:
        """Exponential Moving Average"""
        return prices.ewm(span=period, adjust=False).mean()
    
    @staticmethod
    def rsi(prices: pd.Series, period: int = 14) -> pd.Series:
        """Relative Strength Index"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    @staticmethod
    def macd(prices: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """MACD, Signal Line, Histogram"""
        ema_fast = prices.ewm(span=fast, adjust=False).mean()
        ema_slow = prices.ewm(span=slow, adjust=False).mean()
        macd_line = ema_fast - ema_slow
        signal_line = macd_line.ewm(span=signal, adjust=False).mean()
        histogram = macd_line - signal_line
        return macd_line, signal_line, histogram
    
    @staticmethod
    def bollinger_bands(prices: pd.Series, period: int = 20, std_dev: float = 2.0) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """Bollinger Bands: Upper, Middle, Lower"""
        middle = prices.rolling(window=period).mean()
        std = prices.rolling(window=period).std()
        upper = middle + (std * std_dev)
        lower = middle - (std * std_dev)
        return upper, middle, lower
    
    @staticmethod
    def atr(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
        """Average True Range"""
        tr1 = high - low
        tr2 = abs(high - close.shift())
        tr3 = abs(low - close.shift())
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = tr.rolling(window=period).mean()
        return atr
    
    @staticmethod
    def stochastic(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14, k_smooth: int = 3) -> Tuple[pd.Series, pd.Series]:
        """Stochastic Oscillator: %K, %D"""
        lowest_low = low.rolling(window=period).min()
        highest_high = high.rolling(window=period).max()
        k = 100 * ((close - lowest_low) / (highest_high - lowest_low))
        k = k.rolling(window=k_smooth).mean()
        d = k.rolling(window=3).mean()
        return k, d
    
    @staticmethod
    def adx(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
        """Average Directional Index"""
        plus_dm = high.diff()
        minus_dm = -low.diff()
        plus_dm[plus_dm < 0] = 0
        minus_dm[minus_dm < 0] = 0
        
        tr = pd.concat([high - low, abs(high - close.shift()), abs(low - close.shift())], axis=1).max(axis=1)
        atr = tr.rolling(window=period).mean()
        
        plus_di = 100 * (plus_dm.rolling(window=period).mean() / atr)
        minus_di = 100 * (minus_dm.rolling(window=period).mean() / atr)
        
        dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di)
        adx = dx.rolling(window=period).mean()
        return adx
    
    @staticmethod
    def obv(close: pd.Series, volume: pd.Series) -> pd.Series:
        """On-Balance Volume"""
        obv = (np.sign(close.diff()) * volume).fillna(0).cumsum()
        return obv
    
    @staticmethod
    def vwap(high: pd.Series, low: pd.Series, close: pd.Series, volume: pd.Series) -> pd.Series:
        """Volume Weighted Average Price"""
        typical_price = (high + low + close) / 3
        vwap = (typical_price * volume).cumsum() / volume.cumsum()
        return vwap
    
    @staticmethod
    def support_resistance(prices: pd.Series, window: int = 20) -> Dict[str, float]:
        """Find support and resistance levels"""
        rolling_max = prices.rolling(window=window).max()
        rolling_min = prices.rolling(window=window).min()
        
        resistance = rolling_max.iloc[-1]
        support = rolling_min.iloc[-1]
        
        return {
            "resistance": resistance,
            "support": support,
            "mid": (resistance + support) / 2
        }
    
    @staticmethod
    def pivot_points(high: float, low: float, close: float) -> Dict[str, float]:
        """Calculate pivot points"""
        pivot = (high + low + close) / 3
        r1 = 2 * pivot - low
        s1 = 2 * pivot - high
        r2 = pivot + (high - low)
        s2 = pivot - (high - low)
        r3 = high + 2 * (pivot - low)
        s3 = low - 2 * (high - pivot)
        
        return {
            "pivot": pivot,
            "r1": r1, "r2": r2, "r3": r3,
            "s1": s1, "s2": s2, "s3": s3
        }
    
    @staticmethod
    def trend_strength(prices: pd.Series, period: int = 20) -> Dict[str, any]:
        """Determine trend strength and direction"""
        sma = prices.rolling(window=period).mean()
        current_price = prices.iloc[-1]
        sma_current = sma.iloc[-1]
        
        # Calculate slope
        slope = (sma.iloc[-1] - sma.iloc[-5]) / 5 if len(sma) >= 5 else 0
        
        # Determine trend
        if current_price > sma_current * 1.02:
            trend = "STRONG_UPTREND"
        elif current_price > sma_current:
            trend = "UPTREND"
        elif current_price < sma_current * 0.98:
            trend = "STRONG_DOWNTREND"
        elif current_price < sma_current:
            trend = "DOWNTREND"
        else:
            trend = "SIDEWAYS"
        
        return {
            "trend": trend,
            "slope": slope,
            "price_vs_sma": ((current_price - sma_current) / sma_current) * 100
        }


class OptionsIndicators:
    """Options-specific calculations"""
    
    @staticmethod
    def pcr(put_oi: float, call_oi: float) -> float:
        """Put-Call Ratio"""
        return put_oi / call_oi if call_oi > 0 else 0
    
    @staticmethod
    def max_pain(option_chain: List[Dict]) -> float:
        """Calculate max pain point"""
        strikes = {}
        for opt in option_chain:
            strike = opt['strike_price']
            if strike not in strikes:
                strikes[strike] = {'call_oi': 0, 'put_oi': 0}
            
            if opt['option_type'] == 'CE':
                strikes[strike]['call_oi'] = opt['oi']
            else:
                strikes[strike]['put_oi'] = opt['oi']
        
        # Calculate pain for each strike
        pain_values = {}
        for test_strike in strikes.keys():
            call_pain = sum(max(0, test_strike - s) * strikes[s]['call_oi'] for s in strikes.keys())
            put_pain = sum(max(0, s - test_strike) * strikes[s]['put_oi'] for s in strikes.keys())
            pain_values[test_strike] = call_pain + put_pain
        
        # Return strike with minimum pain
        return min(pain_values, key=pain_values.get) if pain_values else 0
    
    @staticmethod
    def iv_rank(current_iv: float, iv_history: pd.Series) -> float:
        """IV Rank: where current IV stands vs 52-week range"""
        iv_min = iv_history.min()
        iv_max = iv_history.max()
        if iv_max == iv_min:
            return 50.0
        iv_rank = ((current_iv - iv_min) / (iv_max - iv_min)) * 100
        return iv_rank


class CorrelationIndicators:
    """Correlation and cointegration calculations"""
    
    @staticmethod
    def correlation(series1: pd.Series, series2: pd.Series, period: int = 30) -> float:
        """Pearson correlation coefficient"""
        return series1.tail(period).corr(series2.tail(period))
    
    @staticmethod
    def beta(stock_returns: pd.Series, market_returns: pd.Series) -> float:
        """Beta coefficient (hedge ratio)"""
        covariance = stock_returns.cov(market_returns)
        market_variance = market_returns.var()
        return covariance / market_variance if market_variance != 0 else 1.0
    
    @staticmethod
    def z_score(spread: pd.Series) -> float:
        """Z-score of spread for pairs trading"""
        mean = spread.mean()
        std = spread.std()
        current = spread.iloc[-1]
        return (current - mean) / std if std != 0 else 0
    
    @staticmethod
    def half_life(spread: pd.Series) -> float:
        """Half-life of mean reversion in days"""
        lag_spread = spread.shift(1)
        delta_spread = spread - lag_spread
        
        # Linear regression to find mean reversion speed
        df = pd.DataFrame({'spread': lag_spread[1:], 'delta': delta_spread[1:]}).dropna()
        
        if len(df) < 2:
            return 999  # Not enough data
        
        # Simple linear regression
        x = df['spread'].values
        y = df['delta'].values
        lambda_param = -np.polyfit(x, y, 1)[0]
        
        if lambda_param <= 0:
            return 999  # No mean reversion
        
        half_life = -np.log(2) / lambda_param
        return max(1, min(half_life, 999))


def compute_correlation_matrix(data: pd.DataFrame, method: str = 'pearson', period: Optional[str] = None) -> Dict:
    """
    Compute correlation matrix for a DataFrame of asset prices.
    
    Args:
        data: DataFrame where columns are asset symbols and rows are timestamps/dates.
              Values should be prices (Adjusted Close preferred).
        method: Method of correlation: {'pearson', 'kendall', 'spearman'}
        period: Optional period to slice data (e.g., '1y', '6mo') - requires DatetimeIndex
        
    Returns:
        Dictionary representing the correlation matrix
    """
    if data.empty:
        return {"error": "Empty data provided"}
    
    # Calculate returns (percentage change)
    # Correlation is typically calculated on returns, not raw prices, to avoid spurious correlation from trends
    returns = data.pct_change().dropna()
    
    if returns.empty:
        return {"error": "Insufficient data to calculate returns"}
    
    # Compute correlation matrix
    corr_matrix = returns.corr(method=method)
    
    # Convert to dictionary for easier consumption by agents (or JSON serialization)
    # Structure: { "AAPL": {"AAPL": 1.0, "MSFT": 0.85}, "MSFT": {"AAPL": 0.85, "MSFT": 1.0} }
    return corr_matrix.to_dict()


def compute_technical_analysis(ohlcv_df: pd.DataFrame) -> Dict:
    """
    Compute all technical indicators from OHLCV data
    
    Args:
        ohlcv_df: DataFrame with columns [timestamp, open, high, low, close, volume]
    
    Returns:
        Dictionary with all computed indicators (no raw data)
    """
    if ohlcv_df.empty or len(ohlcv_df) < 2:
        return {"error": "Insufficient data"}
    
    close = ohlcv_df['close']
    high = ohlcv_df['high']
    low = ohlcv_df['low']
    open_price = ohlcv_df['open']
    volume = ohlcv_df['volume']
    
    indicators = TechnicalIndicators()
    
    # Moving Averages
    sma_20 = indicators.sma(close, 20).iloc[-1] if len(close) >= 20 else None
    sma_50 = indicators.sma(close, 50).iloc[-1] if len(close) >= 50 else None
    sma_200 = indicators.sma(close, 200).iloc[-1] if len(close) >= 200 else None
    ema_12 = indicators.ema(close, 12).iloc[-1] if len(close) >= 12 else None
    ema_26 = indicators.ema(close, 26).iloc[-1] if len(close) >= 26 else None
    
    # MACD
    macd_line, signal_line, histogram = indicators.macd(close)
    macd_current = macd_line.iloc[-1] if not macd_line.empty else None
    signal_current = signal_line.iloc[-1] if not signal_line.empty else None
    histogram_current = histogram.iloc[-1] if not histogram.empty else None
    macd_crossover = "BULLISH" if macd_current and signal_current and macd_current > signal_current else "BEARISH" if macd_current and signal_current else "NEUTRAL"
    
    # RSI
    rsi = indicators.rsi(close).iloc[-1] if len(close) >= 14 else None
    rsi_signal = "OVERBOUGHT" if rsi and rsi > 70 else "OVERSOLD" if rsi and rsi < 30 else "NEUTRAL"
    
    # Bollinger Bands
    bb_upper, bb_middle, bb_lower = indicators.bollinger_bands(close)
    bb_upper_val = bb_upper.iloc[-1] if not bb_upper.empty else None
    bb_middle_val = bb_middle.iloc[-1] if not bb_middle.empty else None
    bb_lower_val = bb_lower.iloc[-1] if not bb_lower.empty else None
    bb_position = "UPPER" if close.iloc[-1] > bb_upper_val else "LOWER" if close.iloc[-1] < bb_lower_val else "MIDDLE" if bb_upper_val else "UNKNOWN"
    
    # ATR
    atr = indicators.atr(high, low, close).iloc[-1] if len(close) >= 14 else None
    atr_percent = (atr / close.iloc[-1] * 100) if atr else None
    
    # Stochastic
    k, d = indicators.stochastic(high, low, close)
    stoch_k = k.iloc[-1] if not k.empty else None
    stoch_d = d.iloc[-1] if not d.empty else None
    stoch_signal = "OVERBOUGHT" if stoch_k and stoch_k > 80 else "OVERSOLD" if stoch_k and stoch_k < 20 else "NEUTRAL"
    
    # ADX
    adx = indicators.adx(high, low, close).iloc[-1] if len(close) >= 14 else None
    trend_strength = "STRONG" if adx and adx > 25 else "WEAK" if adx else "UNKNOWN"
    
    # Volume
    obv = indicators.obv(close, volume).iloc[-1] if len(close) >= 2 else None
    vwap = indicators.vwap(high, low, close, volume).iloc[-1] if len(close) >= 1 else None
    avg_volume = volume.mean()
    volume_ratio = (volume.iloc[-1] / avg_volume * 100) if avg_volume > 0 else None
    
    # Support/Resistance
    sr_levels = indicators.support_resistance(close)
    
    # Pivot Points (using previous day high/low/close)
    if len(ohlcv_df) >= 2:
        prev_high = high.iloc[-2]
        prev_low = low.iloc[-2]
        prev_close = close.iloc[-2]
        pivots = indicators.pivot_points(prev_high, prev_low, prev_close)
    else:
        pivots = {}
    
    # Trend
    trend_info = indicators.trend_strength(close)
    
    # Current price position
    current_price = close.iloc[-1]
    
    return {
        "current_price": current_price,
        "moving_averages": {
            "sma_20": sma_20,
            "sma_50": sma_50,
            "sma_200": sma_200,
            "ema_12": ema_12,
            "ema_26": ema_26,
            "price_vs_sma200": ((current_price - sma_200) / sma_200 * 100) if sma_200 else None
        },
        "macd": {
            "macd_line": macd_current,
            "signal_line": signal_current,
            "histogram": histogram_current,
            "crossover": macd_crossover
        },
        "rsi": {
            "value": rsi,
            "signal": rsi_signal
        },
        "bollinger_bands": {
            "upper": bb_upper_val,
            "middle": bb_middle_val,
            "lower": bb_lower_val,
            "position": bb_position,
            "bandwidth": ((bb_upper_val - bb_lower_val) / bb_middle_val * 100) if bb_middle_val else None
        },
        "volatility": {
            "atr": atr,
            "atr_percent": atr_percent,
            "adx": adx,
            "trend_strength": trend_strength
        },
        "stochastic": {
            "k": stoch_k,
            "d": stoch_d,
            "signal": stoch_signal
        },
        "volume": {
            "current": volume.iloc[-1],
            "average": avg_volume,
            "ratio_percent": volume_ratio,
            "obv": obv,
            "vwap": vwap,
            "price_vs_vwap": ((current_price - vwap) / vwap * 100) if vwap else None
        },
        "support_resistance": sr_levels,
        "pivot_points": pivots,
        "trend": trend_info
    }