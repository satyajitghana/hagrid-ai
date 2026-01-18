"""Data models for NSE India charting/historical data API."""

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ChartType(StrEnum):
    """Chart type for historical data."""

    INTRADAY = "I"  # Intraday data
    DAILY = "D"  # Daily data


class SymbolType(StrEnum):
    """Type of symbol/instrument."""

    EQUITY = "Equity"
    FUTURES = "Futures"
    OPTIONS = "Options"
    INDEX = "Index"


class ChartSymbol(BaseModel):
    """Symbol information from charting API.

    Represents a tradeable symbol with its scripcode (token) for chart data.
    """

    model_config = ConfigDict(
        populate_by_name=True,
        str_strip_whitespace=True,
    )

    symbol: str = Field(description="Trading symbol (e.g., RELIANCE-EQ)")
    scripcode: str = Field(description="Unique token/scripcode for the symbol")
    description: str = Field(description="Full description/name")
    symbol_type: str = Field(alias="type", description="Type of instrument")

    @property
    def is_equity(self) -> bool:
        """Check if this is an equity symbol."""
        return self.symbol_type == SymbolType.EQUITY

    @property
    def is_futures(self) -> bool:
        """Check if this is a futures symbol."""
        return self.symbol_type == SymbolType.FUTURES

    @property
    def is_options(self) -> bool:
        """Check if this is an options symbol."""
        return self.symbol_type == SymbolType.OPTIONS

    @property
    def base_symbol(self) -> str:
        """Get the base symbol without suffix (e.g., RELIANCE from RELIANCE-EQ)."""
        if "-" in self.symbol:
            return self.symbol.split("-")[0]
        return self.symbol


class ChartCandle(BaseModel):
    """OHLCV candle data for a single time period.

    Represents one candlestick with open, high, low, close, and volume.
    """

    model_config = ConfigDict(str_strip_whitespace=True)

    time: datetime = Field(description="Candle timestamp")
    open: float = Field(description="Opening price")
    high: float = Field(description="Highest price")
    low: float = Field(description="Lowest price")
    close: float = Field(description="Closing price")
    volume: int = Field(description="Trading volume")

    @field_validator("time", mode="before")
    @classmethod
    def parse_time(cls, v: Any) -> datetime:
        """Parse time from unix milliseconds."""
        if isinstance(v, datetime):
            return v
        if isinstance(v, int | float):
            # NSE charting API returns time in milliseconds
            return datetime.fromtimestamp(v / 1000)
        if isinstance(v, str):
            # Try parsing ISO format
            try:
                return datetime.fromisoformat(v)
            except ValueError:
                # Try as timestamp
                return datetime.fromtimestamp(float(v) / 1000)
        raise ValueError(f"Cannot parse time: {v}")

    @property
    def change(self) -> float:
        """Calculate absolute price change (close - open)."""
        return self.close - self.open

    @property
    def change_percent(self) -> float:
        """Calculate percentage change from open to close."""
        if self.open == 0:
            return 0.0
        return ((self.close - self.open) / self.open) * 100

    @property
    def is_bullish(self) -> bool:
        """Check if this is a bullish (green) candle."""
        return self.close >= self.open

    @property
    def is_bearish(self) -> bool:
        """Check if this is a bearish (red) candle."""
        return self.close < self.open

    @property
    def body_size(self) -> float:
        """Get the candle body size (absolute)."""
        return abs(self.close - self.open)

    @property
    def upper_wick(self) -> float:
        """Get the upper wick size."""
        return self.high - max(self.open, self.close)

    @property
    def lower_wick(self) -> float:
        """Get the lower wick size."""
        return min(self.open, self.close) - self.low

    @property
    def range(self) -> float:
        """Get the full candle range (high - low)."""
        return self.high - self.low


class ChartDataResponse(BaseModel):
    """Response containing historical chart data.

    Contains a list of OHLCV candles for a symbol.
    """

    model_config = ConfigDict(str_strip_whitespace=True)

    symbol: str = Field(description="Symbol for which data was fetched")
    symbol_type: str = Field(default="Equity", description="Type of symbol")
    chart_type: str = Field(default="D", description="Chart type (I=Intraday, D=Daily)")
    interval: int = Field(default=1, description="Time interval (minutes for intraday)")
    candles: list[ChartCandle] = Field(
        default_factory=list,
        description="List of OHLCV candles",
    )

    @property
    def total_candles(self) -> int:
        """Get total number of candles."""
        return len(self.candles)

    @property
    def first_candle(self) -> ChartCandle | None:
        """Get the first (oldest) candle."""
        return self.candles[0] if self.candles else None

    @property
    def last_candle(self) -> ChartCandle | None:
        """Get the last (most recent) candle."""
        return self.candles[-1] if self.candles else None

    @property
    def start_time(self) -> datetime | None:
        """Get the start time of the data."""
        return self.candles[0].time if self.candles else None

    @property
    def end_time(self) -> datetime | None:
        """Get the end time of the data."""
        return self.candles[-1].time if self.candles else None

    @property
    def period_high(self) -> float | None:
        """Get the highest price in the period."""
        if not self.candles:
            return None
        return max(c.high for c in self.candles)

    @property
    def period_low(self) -> float | None:
        """Get the lowest price in the period."""
        if not self.candles:
            return None
        return min(c.low for c in self.candles)

    @property
    def total_volume(self) -> int:
        """Get total volume across all candles."""
        return sum(c.volume for c in self.candles)

    @property
    def average_volume(self) -> float:
        """Get average volume per candle."""
        if not self.candles:
            return 0.0
        return self.total_volume / len(self.candles)

    @property
    def period_change(self) -> float | None:
        """Get price change from first to last candle."""
        if not self.candles or len(self.candles) < 2:
            return None
        return self.candles[-1].close - self.candles[0].open

    @property
    def period_change_percent(self) -> float | None:
        """Get percentage change from first to last candle."""
        if not self.candles or len(self.candles) < 2:
            return None
        first_open = self.candles[0].open
        if first_open == 0:
            return None
        return ((self.candles[-1].close - first_open) / first_open) * 100

    def get_bullish_candles(self) -> list[ChartCandle]:
        """Get all bullish (green) candles."""
        return [c for c in self.candles if c.is_bullish]

    def get_bearish_candles(self) -> list[ChartCandle]:
        """Get all bearish (red) candles."""
        return [c for c in self.candles if c.is_bearish]

    def get_candles_in_range(
        self, start: datetime, end: datetime
    ) -> list[ChartCandle]:
        """Get candles within a specific time range."""
        return [c for c in self.candles if start <= c.time <= end]

    def get_latest_candles(self, count: int = 10) -> list[ChartCandle]:
        """Get the most recent N candles."""
        return self.candles[-count:] if self.candles else []

    def get_vwap(self) -> float | None:
        """Calculate Volume Weighted Average Price."""
        if not self.candles:
            return None
        total_volume = sum(c.volume for c in self.candles)
        if total_volume == 0:
            return None
        # Use typical price (HLC/3) for VWAP
        weighted_sum = sum(
            ((c.high + c.low + c.close) / 3) * c.volume for c in self.candles
        )
        return weighted_sum / total_volume


class SymbolSearchResponse(BaseModel):
    """Response from symbol search API.

    Contains list of matching symbols for a search query.
    """

    model_config = ConfigDict(str_strip_whitespace=True)

    query: str = Field(description="Original search query")
    symbols: list[ChartSymbol] = Field(
        default_factory=list,
        description="List of matching symbols",
    )

    @property
    def total_count(self) -> int:
        """Get total number of matching symbols."""
        return len(self.symbols)

    def get_equity_symbols(self) -> list[ChartSymbol]:
        """Get only equity symbols."""
        return [s for s in self.symbols if s.is_equity]

    def get_futures_symbols(self) -> list[ChartSymbol]:
        """Get only futures symbols."""
        return [s for s in self.symbols if s.is_futures]

    def get_options_symbols(self) -> list[ChartSymbol]:
        """Get only options symbols."""
        return [s for s in self.symbols if s.is_options]

    def get_by_scripcode(self, scripcode: str) -> ChartSymbol | None:
        """Get symbol by scripcode/token."""
        for sym in self.symbols:
            if sym.scripcode == scripcode:
                return sym
        return None

    def get_by_symbol(self, symbol: str) -> ChartSymbol | None:
        """Get symbol by exact symbol match."""
        symbol_upper = symbol.upper()
        for sym in self.symbols:
            if sym.symbol.upper() == symbol_upper:
                return sym
        return None
