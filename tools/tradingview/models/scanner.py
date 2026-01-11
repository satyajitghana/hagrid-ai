"""Scanner/Technicals API response models."""

from enum import Enum
from pydantic import BaseModel, Field
from typing import Any


class Recommendation(str, Enum):
    """Technical recommendation values."""
    STRONG_BUY = "STRONG_BUY"
    BUY = "BUY"
    NEUTRAL = "NEUTRAL"
    SELL = "SELL"
    STRONG_SELL = "STRONG_SELL"


class TechnicalIndicators(BaseModel):
    """Technical indicators from the scanner API."""
    
    # Recommendations (aggregated signals)
    recommend_all: float | None = Field(default=None, alias="Recommend.All", description="Overall recommendation (-1 to 1)")
    recommend_ma: float | None = Field(default=None, alias="Recommend.MA", description="Moving Average recommendation")
    recommend_other: float | None = Field(default=None, alias="Recommend.Other", description="Other indicators recommendation")
    
    # RSI
    rsi: float | None = Field(default=None, alias="RSI", description="Relative Strength Index")
    rsi_prev: float | None = Field(default=None, alias="RSI[1]", description="Previous RSI value")
    
    # Stochastic
    stoch_k: float | None = Field(default=None, alias="Stoch.K", description="Stochastic %K")
    stoch_d: float | None = Field(default=None, alias="Stoch.D", description="Stochastic %D")
    stoch_k_prev: float | None = Field(default=None, alias="Stoch.K[1]", description="Previous Stochastic %K")
    stoch_d_prev: float | None = Field(default=None, alias="Stoch.D[1]", description="Previous Stochastic %D")
    stoch_rsi_k: float | None = Field(default=None, alias="Stoch.RSI.K", description="Stochastic RSI %K")
    rec_stoch_rsi: float | None = Field(default=None, alias="Rec.Stoch.RSI", description="Stochastic RSI recommendation")
    
    # CCI
    cci20: float | None = Field(default=None, alias="CCI20", description="Commodity Channel Index (20)")
    cci20_prev: float | None = Field(default=None, alias="CCI20[1]", description="Previous CCI value")
    
    # ADX
    adx: float | None = Field(default=None, alias="ADX", description="Average Directional Index")
    adx_plus_di: float | None = Field(default=None, alias="ADX+DI", description="ADX +DI")
    adx_minus_di: float | None = Field(default=None, alias="ADX-DI", description="ADX -DI")
    adx_plus_di_prev: float | None = Field(default=None, alias="ADX+DI[1]", description="Previous ADX +DI")
    adx_minus_di_prev: float | None = Field(default=None, alias="ADX-DI[1]", description="Previous ADX -DI")
    
    # Awesome Oscillator
    ao: float | None = Field(default=None, alias="AO", description="Awesome Oscillator")
    ao_prev: float | None = Field(default=None, alias="AO[1]", description="Previous AO value")
    ao_prev2: float | None = Field(default=None, alias="AO[2]", description="AO value 2 periods ago")
    
    # Momentum
    mom: float | None = Field(default=None, alias="Mom", description="Momentum")
    mom_prev: float | None = Field(default=None, alias="Mom[1]", description="Previous Momentum")
    
    # MACD
    macd_macd: float | None = Field(default=None, alias="MACD.macd", description="MACD line")
    macd_signal: float | None = Field(default=None, alias="MACD.signal", description="MACD signal line")
    
    # Williams %R
    williams_r: float | None = Field(default=None, alias="W.R", description="Williams %R")
    rec_wr: float | None = Field(default=None, alias="Rec.WR", description="Williams %R recommendation")
    
    # Bull/Bear Power
    bb_power: float | None = Field(default=None, alias="BBPower", description="Bull/Bear Power")
    rec_bb_power: float | None = Field(default=None, alias="Rec.BBPower", description="BB Power recommendation")
    
    # Ultimate Oscillator
    uo: float | None = Field(default=None, alias="UO", description="Ultimate Oscillator")
    rec_uo: float | None = Field(default=None, alias="Rec.UO", description="UO recommendation")
    
    # Price
    close: float | None = Field(default=None, description="Closing price")
    
    # Exponential Moving Averages
    ema10: float | None = Field(default=None, alias="EMA10", description="10-period EMA")
    ema20: float | None = Field(default=None, alias="EMA20", description="20-period EMA")
    ema30: float | None = Field(default=None, alias="EMA30", description="30-period EMA")
    ema50: float | None = Field(default=None, alias="EMA50", description="50-period EMA")
    ema100: float | None = Field(default=None, alias="EMA100", description="100-period EMA")
    ema200: float | None = Field(default=None, alias="EMA200", description="200-period EMA")
    
    # Simple Moving Averages
    sma10: float | None = Field(default=None, alias="SMA10", description="10-period SMA")
    sma20: float | None = Field(default=None, alias="SMA20", description="20-period SMA")
    sma30: float | None = Field(default=None, alias="SMA30", description="30-period SMA")
    sma50: float | None = Field(default=None, alias="SMA50", description="50-period SMA")
    sma100: float | None = Field(default=None, alias="SMA100", description="100-period SMA")
    sma200: float | None = Field(default=None, alias="SMA200", description="200-period SMA")
    
    # Ichimoku
    ichimoku_bline: float | None = Field(default=None, alias="Ichimoku.BLine", description="Ichimoku Base Line")
    rec_ichimoku: float | None = Field(default=None, alias="Rec.Ichimoku", description="Ichimoku recommendation")
    
    # VWMA
    vwma: float | None = Field(default=None, alias="VWMA", description="Volume Weighted Moving Average")
    rec_vwma: float | None = Field(default=None, alias="Rec.VWMA", description="VWMA recommendation")
    
    # Hull MA
    hull_ma9: float | None = Field(default=None, alias="HullMA9", description="9-period Hull Moving Average")
    rec_hull_ma9: float | None = Field(default=None, alias="Rec.HullMA9", description="Hull MA recommendation")
    
    # Monthly Classic Pivot Points
    pivot_m_classic_r3: float | None = Field(default=None, alias="Pivot.M.Classic.R3")
    pivot_m_classic_r2: float | None = Field(default=None, alias="Pivot.M.Classic.R2")
    pivot_m_classic_r1: float | None = Field(default=None, alias="Pivot.M.Classic.R1")
    pivot_m_classic_middle: float | None = Field(default=None, alias="Pivot.M.Classic.Middle")
    pivot_m_classic_s1: float | None = Field(default=None, alias="Pivot.M.Classic.S1")
    pivot_m_classic_s2: float | None = Field(default=None, alias="Pivot.M.Classic.S2")
    pivot_m_classic_s3: float | None = Field(default=None, alias="Pivot.M.Classic.S3")
    
    # Monthly Fibonacci Pivot Points
    pivot_m_fibonacci_r3: float | None = Field(default=None, alias="Pivot.M.Fibonacci.R3")
    pivot_m_fibonacci_r2: float | None = Field(default=None, alias="Pivot.M.Fibonacci.R2")
    pivot_m_fibonacci_r1: float | None = Field(default=None, alias="Pivot.M.Fibonacci.R1")
    pivot_m_fibonacci_middle: float | None = Field(default=None, alias="Pivot.M.Fibonacci.Middle")
    pivot_m_fibonacci_s1: float | None = Field(default=None, alias="Pivot.M.Fibonacci.S1")
    pivot_m_fibonacci_s2: float | None = Field(default=None, alias="Pivot.M.Fibonacci.S2")
    pivot_m_fibonacci_s3: float | None = Field(default=None, alias="Pivot.M.Fibonacci.S3")
    
    # Monthly Camarilla Pivot Points
    pivot_m_camarilla_r3: float | None = Field(default=None, alias="Pivot.M.Camarilla.R3")
    pivot_m_camarilla_r2: float | None = Field(default=None, alias="Pivot.M.Camarilla.R2")
    pivot_m_camarilla_r1: float | None = Field(default=None, alias="Pivot.M.Camarilla.R1")
    pivot_m_camarilla_middle: float | None = Field(default=None, alias="Pivot.M.Camarilla.Middle")
    pivot_m_camarilla_s1: float | None = Field(default=None, alias="Pivot.M.Camarilla.S1")
    pivot_m_camarilla_s2: float | None = Field(default=None, alias="Pivot.M.Camarilla.S2")
    pivot_m_camarilla_s3: float | None = Field(default=None, alias="Pivot.M.Camarilla.S3")
    
    # Monthly Woodie Pivot Points
    pivot_m_woodie_r3: float | None = Field(default=None, alias="Pivot.M.Woodie.R3")
    pivot_m_woodie_r2: float | None = Field(default=None, alias="Pivot.M.Woodie.R2")
    pivot_m_woodie_r1: float | None = Field(default=None, alias="Pivot.M.Woodie.R1")
    pivot_m_woodie_middle: float | None = Field(default=None, alias="Pivot.M.Woodie.Middle")
    pivot_m_woodie_s1: float | None = Field(default=None, alias="Pivot.M.Woodie.S1")
    pivot_m_woodie_s2: float | None = Field(default=None, alias="Pivot.M.Woodie.S2")
    pivot_m_woodie_s3: float | None = Field(default=None, alias="Pivot.M.Woodie.S3")
    
    # Monthly DeMark Pivot Points
    pivot_m_demark_r1: float | None = Field(default=None, alias="Pivot.M.Demark.R1")
    pivot_m_demark_middle: float | None = Field(default=None, alias="Pivot.M.Demark.Middle")
    pivot_m_demark_s1: float | None = Field(default=None, alias="Pivot.M.Demark.S1")
    
    @classmethod
    def from_api_response(cls, data: dict[str, Any]) -> "TechnicalIndicators":
        """Create from raw API response."""
        return cls.model_validate(data)
    
    @property
    def overall_recommendation(self) -> Recommendation:
        """Get overall recommendation as enum."""
        if self.recommend_all is None:
            return Recommendation.NEUTRAL
        if self.recommend_all >= 0.5:
            return Recommendation.STRONG_BUY
        elif self.recommend_all >= 0.1:
            return Recommendation.BUY
        elif self.recommend_all <= -0.5:
            return Recommendation.STRONG_SELL
        elif self.recommend_all <= -0.1:
            return Recommendation.SELL
        return Recommendation.NEUTRAL
    
    @property
    def ma_recommendation(self) -> Recommendation:
        """Get MA recommendation as enum."""
        if self.recommend_ma is None:
            return Recommendation.NEUTRAL
        if self.recommend_ma >= 0.5:
            return Recommendation.STRONG_BUY
        elif self.recommend_ma >= 0.1:
            return Recommendation.BUY
        elif self.recommend_ma <= -0.5:
            return Recommendation.STRONG_SELL
        elif self.recommend_ma <= -0.1:
            return Recommendation.SELL
        return Recommendation.NEUTRAL
    
    @property
    def is_oversold(self) -> bool:
        """Check if RSI indicates oversold condition."""
        return self.rsi is not None and self.rsi < 30
    
    @property
    def is_overbought(self) -> bool:
        """Check if RSI indicates overbought condition."""
        return self.rsi is not None and self.rsi > 70
    
    @property
    def macd_histogram(self) -> float | None:
        """Calculate MACD histogram."""
        if self.macd_macd is not None and self.macd_signal is not None:
            return self.macd_macd - self.macd_signal
        return None
    
    @property
    def is_bullish_macd(self) -> bool:
        """Check if MACD is bullish (MACD > Signal)."""
        hist = self.macd_histogram
        return hist is not None and hist > 0
    
    @property
    def is_trending(self) -> bool:
        """Check if ADX indicates trending market (>25)."""
        return self.adx is not None and self.adx > 25
    
    @property
    def is_bullish_trend(self) -> bool:
        """Check if +DI > -DI (bullish trend)."""
        if self.adx_plus_di is not None and self.adx_minus_di is not None:
            return self.adx_plus_di > self.adx_minus_di
        return False
    
    @property
    def price_vs_sma200(self) -> float | None:
        """Get price position relative to SMA200 (percentage)."""
        if self.close is not None and self.sma200 is not None:
            return ((self.close - self.sma200) / self.sma200) * 100
        return None
    
    @property
    def is_above_200_sma(self) -> bool:
        """Check if price is above 200 SMA."""
        if self.close is not None and self.sma200 is not None:
            return self.close > self.sma200
        return False
    
    def get_nearest_support(self) -> float | None:
        """Get nearest classic pivot support level."""
        if self.close is None:
            return None
        supports = [
            self.pivot_m_classic_s1,
            self.pivot_m_classic_s2,
            self.pivot_m_classic_s3,
        ]
        valid_supports = [s for s in supports if s is not None and s < self.close]
        return max(valid_supports) if valid_supports else None
    
    def get_nearest_resistance(self) -> float | None:
        """Get nearest classic pivot resistance level."""
        if self.close is None:
            return None
        resistances = [
            self.pivot_m_classic_r1,
            self.pivot_m_classic_r2,
            self.pivot_m_classic_r3,
        ]
        valid_resistances = [r for r in resistances if r is not None and r > self.close]
        return min(valid_resistances) if valid_resistances else None
    
    def get_all_moving_averages(self) -> dict[str, float | None]:
        """Get all moving averages in a dictionary."""
        return {
            "EMA10": self.ema10,
            "EMA20": self.ema20,
            "EMA30": self.ema30,
            "EMA50": self.ema50,
            "EMA100": self.ema100,
            "EMA200": self.ema200,
            "SMA10": self.sma10,
            "SMA20": self.sma20,
            "SMA30": self.sma30,
            "SMA50": self.sma50,
            "SMA100": self.sma100,
            "SMA200": self.sma200,
            "VWMA": self.vwma,
            "HullMA9": self.hull_ma9,
            "Ichimoku.BLine": self.ichimoku_bline,
        }
    
    def get_classic_pivot_levels(self) -> dict[str, float | None]:
        """Get all classic pivot levels."""
        return {
            "R3": self.pivot_m_classic_r3,
            "R2": self.pivot_m_classic_r2,
            "R1": self.pivot_m_classic_r1,
            "Pivot": self.pivot_m_classic_middle,
            "S1": self.pivot_m_classic_s1,
            "S2": self.pivot_m_classic_s2,
            "S3": self.pivot_m_classic_s3,
        }

    class Config:
        populate_by_name = True


# Standard fields to request for technicals
TECHNICALS_FIELDS = [
    "Recommend.Other", "Recommend.All", "Recommend.MA",
    "RSI", "RSI[1]",
    "Stoch.K", "Stoch.D", "Stoch.K[1]", "Stoch.D[1]",
    "CCI20", "CCI20[1]",
    "ADX", "ADX+DI", "ADX-DI", "ADX+DI[1]", "ADX-DI[1]",
    "AO", "AO[1]", "AO[2]",
    "Mom", "Mom[1]",
    "MACD.macd", "MACD.signal",
    "Rec.Stoch.RSI", "Stoch.RSI.K",
    "Rec.WR", "W.R",
    "Rec.BBPower", "BBPower",
    "Rec.UO", "UO",
    "EMA10", "close", "SMA10",
    "EMA20", "SMA20",
    "EMA30", "SMA30",
    "EMA50", "SMA50",
    "EMA100", "SMA100",
    "EMA200", "SMA200",
    "Rec.Ichimoku", "Ichimoku.BLine",
    "Rec.VWMA", "VWMA",
    "Rec.HullMA9", "HullMA9",
    "Pivot.M.Classic.R3", "Pivot.M.Classic.R2", "Pivot.M.Classic.R1",
    "Pivot.M.Classic.Middle",
    "Pivot.M.Classic.S1", "Pivot.M.Classic.S2", "Pivot.M.Classic.S3",
    "Pivot.M.Fibonacci.R3", "Pivot.M.Fibonacci.R2", "Pivot.M.Fibonacci.R1",
    "Pivot.M.Fibonacci.Middle",
    "Pivot.M.Fibonacci.S1", "Pivot.M.Fibonacci.S2", "Pivot.M.Fibonacci.S3",
    "Pivot.M.Camarilla.R3", "Pivot.M.Camarilla.R2", "Pivot.M.Camarilla.R1",
    "Pivot.M.Camarilla.Middle",
    "Pivot.M.Camarilla.S1", "Pivot.M.Camarilla.S2", "Pivot.M.Camarilla.S3",
    "Pivot.M.Woodie.R3", "Pivot.M.Woodie.R2", "Pivot.M.Woodie.R1",
    "Pivot.M.Woodie.Middle",
    "Pivot.M.Woodie.S1", "Pivot.M.Woodie.S2", "Pivot.M.Woodie.S3",
    "Pivot.M.Demark.R1", "Pivot.M.Demark.Middle", "Pivot.M.Demark.S1",
]