"""Data models for NSE India pre-open market data."""

from pydantic import BaseModel, ConfigDict, Field, computed_field


class PreOpenOrder(BaseModel):
    """Individual order in the pre-open order book."""

    model_config = ConfigDict(
        populate_by_name=True,
        str_strip_whitespace=True,
    )

    price: float = Field(default=0, description="Order price")
    buy_qty: int = Field(alias="buyQty", default=0, description="Buy quantity at this price")
    sell_qty: int = Field(alias="sellQty", default=0, description="Sell quantity at this price")
    iep: bool = Field(alias="iep", default=False, description="Is this the IEP price level")


class PreOpenMarketDetail(BaseModel):
    """Pre-open market details including order book and IEP."""

    model_config = ConfigDict(
        populate_by_name=True,
        str_strip_whitespace=True,
    )

    preopen: list[PreOpenOrder] = Field(default_factory=list, description="Order book")
    iep: float = Field(alias="IEP", default=0, description="Indicative Equilibrium Price")
    total_traded_volume: int = Field(
        alias="totalTradedVolume", default=0,
        description="Total traded volume"
    )
    final_price: float = Field(alias="finalPrice", default=0, description="Final price")
    final_quantity: int = Field(
        alias="finalQuantity", default=0,
        description="Final quantity"
    )
    last_update_time: str = Field(
        alias="lastUpdateTime", default="",
        description="Last update timestamp"
    )
    total_buy_quantity: int = Field(
        alias="totalBuyQuantity", default=0,
        description="Total buy quantity"
    )
    total_sell_quantity: int = Field(
        alias="totalSellQuantity", default=0,
        description="Total sell quantity"
    )
    at_buyer_risk: str = Field(
        alias="atBuyerRisk", default="-",
        description="At buyer's risk indicator"
    )
    at_seller_risk: str = Field(
        alias="atSellerRisk", default="-",
        description="At seller's risk indicator"
    )

    @computed_field
    @property
    def buy_sell_ratio(self) -> float:
        """Calculate buy/sell ratio."""
        if self.total_sell_quantity > 0:
            return self.total_buy_quantity / self.total_sell_quantity
        return float('inf') if self.total_buy_quantity > 0 else 0

    @property
    def buy_pressure(self) -> str:
        """Determine buy/sell pressure based on order imbalance."""
        ratio = self.buy_sell_ratio
        if ratio > 2:
            return "Strong Buy Pressure"
        elif ratio > 1.2:
            return "Moderate Buy Pressure"
        elif ratio > 0.8:
            return "Balanced"
        elif ratio > 0.5:
            return "Moderate Sell Pressure"
        else:
            return "Strong Sell Pressure"


class PreOpenStockMetadata(BaseModel):
    """Stock metadata in pre-open market."""

    model_config = ConfigDict(
        populate_by_name=True,
        str_strip_whitespace=True,
    )

    symbol: str = Field(default="", description="Stock symbol")
    identifier: str = Field(default="", description="Unique identifier")
    purpose: str = Field(default="-", description="Corporate action purpose if any")

    # Price data
    last_price: float = Field(alias="lastPrice", default=0, description="Last traded price")
    change: float = Field(default=0, description="Absolute price change")
    pchange: float = Field(alias="pChange", default=0, description="Percentage change")
    previous_close: float = Field(alias="previousClose", default=0, description="Previous close price")
    iep: float = Field(default=0, description="Indicative Equilibrium Price")

    # Volume and turnover
    final_quantity: int = Field(alias="finalQuantity", default=0, description="Final quantity")
    total_turnover: float = Field(alias="totalTurnover", default=0, description="Total turnover")

    # Market cap
    market_cap: float = Field(alias="marketCap", default=0, description="Market capitalization")
    ffm_cap: float = Field(alias="ffmCap", default=0, description="Free float market cap")

    # 52-week data
    year_high: float = Field(alias="yearHigh", default=0, description="52-week high")
    year_low: float = Field(alias="yearLow", default=0, description="52-week low")

    @property
    def is_gapping_up(self) -> bool:
        """Check if stock is gapping up (IEP > previous close)."""
        return self.iep > self.previous_close if self.iep > 0 else False

    @property
    def is_gapping_down(self) -> bool:
        """Check if stock is gapping down (IEP < previous close)."""
        return self.iep < self.previous_close if self.iep > 0 else False

    @property
    def gap_percentage(self) -> float:
        """Calculate gap percentage from previous close."""
        if self.previous_close > 0 and self.iep > 0:
            return ((self.iep - self.previous_close) / self.previous_close) * 100
        return 0

    @property
    def near_52_week_high(self) -> bool:
        """Check if IEP is within 5% of 52-week high."""
        if self.year_high > 0 and self.iep > 0:
            return self.iep >= self.year_high * 0.95
        return False

    @property
    def near_52_week_low(self) -> bool:
        """Check if IEP is within 5% of 52-week low."""
        if self.year_low > 0 and self.iep > 0:
            return self.iep <= self.year_low * 1.05
        return False


class PreOpenDetail(BaseModel):
    """Detail section containing pre-open market data."""

    model_config = ConfigDict(
        populate_by_name=True,
        str_strip_whitespace=True,
    )

    pre_open_market: PreOpenMarketDetail = Field(
        alias="preOpenMarket",
        default_factory=PreOpenMarketDetail
    )


class PreOpenStock(BaseModel):
    """Combined pre-open stock data with metadata and market details."""

    model_config = ConfigDict(
        populate_by_name=True,
        str_strip_whitespace=True,
    )

    metadata: PreOpenStockMetadata = Field(default_factory=PreOpenStockMetadata)
    detail: PreOpenDetail = Field(default_factory=PreOpenDetail)

    @property
    def symbol(self) -> str:
        """Get stock symbol."""
        return self.metadata.symbol

    @property
    def iep(self) -> float:
        """Get Indicative Equilibrium Price."""
        return self.metadata.iep or self.detail.pre_open_market.iep

    @property
    def pchange(self) -> float:
        """Get percentage change."""
        return self.metadata.pchange

    @property
    def total_buy_quantity(self) -> int:
        """Get total buy quantity."""
        return self.detail.pre_open_market.total_buy_quantity

    @property
    def total_sell_quantity(self) -> int:
        """Get total sell quantity."""
        return self.detail.pre_open_market.total_sell_quantity

    @property
    def buy_sell_ratio(self) -> float:
        """Get buy/sell ratio."""
        return self.detail.pre_open_market.buy_sell_ratio


class PreOpenResponse(BaseModel):
    """Response from the pre-open market API."""

    model_config = ConfigDict(
        populate_by_name=True,
        str_strip_whitespace=True,
    )

    declines: int = Field(default=0, description="Number of declining stocks")
    advances: int = Field(default=0, description="Number of advancing stocks")
    unchanged: int = Field(default=0, description="Number of unchanged stocks")
    data: list[PreOpenStock] = Field(default_factory=list, description="Pre-open stock data")

    @computed_field
    @property
    def total_stocks(self) -> int:
        """Total number of stocks in the response."""
        return len(self.data)

    @computed_field
    @property
    def advance_decline_ratio(self) -> float:
        """Calculate advance/decline ratio."""
        if self.declines > 0:
            return self.advances / self.declines
        return float('inf') if self.advances > 0 else 0

    @property
    def market_sentiment(self) -> str:
        """Determine market sentiment based on advance/decline ratio."""
        ratio = self.advance_decline_ratio
        if ratio > 1.5:
            return "Strong Bullish"
        elif ratio > 1.0:
            return "Bullish"
        elif ratio > 0.67:
            return "Neutral"
        elif ratio > 0.5:
            return "Bearish"
        else:
            return "Strong Bearish"

    @property
    def top_gainers(self) -> list[PreOpenStock]:
        """Get top gainers sorted by percentage change."""
        return sorted(self.data, key=lambda x: x.pchange, reverse=True)

    @property
    def top_losers(self) -> list[PreOpenStock]:
        """Get top losers sorted by percentage change."""
        return sorted(self.data, key=lambda x: x.pchange)

    @property
    def stocks_with_buy_pressure(self) -> list[PreOpenStock]:
        """Get stocks with more buy orders than sell orders."""
        return [s for s in self.data if s.buy_sell_ratio > 1]

    @property
    def stocks_with_sell_pressure(self) -> list[PreOpenStock]:
        """Get stocks with more sell orders than buy orders."""
        return [s for s in self.data if s.buy_sell_ratio < 1]

    @property
    def gapping_up(self) -> list[PreOpenStock]:
        """Get stocks gapping up from previous close."""
        return [s for s in self.data if s.metadata.is_gapping_up]

    @property
    def gapping_down(self) -> list[PreOpenStock]:
        """Get stocks gapping down from previous close."""
        return [s for s in self.data if s.metadata.is_gapping_down]

    def get_by_symbol(self, symbol: str) -> PreOpenStock | None:
        """Get stock data by symbol."""
        symbol_upper = symbol.upper()
        for stock in self.data:
            if stock.symbol == symbol_upper:
                return stock
        return None

    def filter_by_gap(self, min_gap_pct: float = 1.0) -> list[PreOpenStock]:
        """Filter stocks by minimum gap percentage (absolute value).

        Args:
            min_gap_pct: Minimum gap percentage (default 1%)

        Returns:
            Stocks with gap >= min_gap_pct
        """
        return [
            s for s in self.data
            if abs(s.metadata.gap_percentage) >= min_gap_pct
        ]


class PreOpenMarketSnapshot(BaseModel):
    """Snapshot of pre-open market for multiple indices."""

    timestamp: str = Field(default="", description="Data timestamp")
    nifty_50: PreOpenResponse | None = Field(default=None, description="NIFTY 50 pre-open data")
    nifty_bank: PreOpenResponse | None = Field(default=None, description="NIFTY Bank pre-open data")
    nifty_it: PreOpenResponse | None = Field(default=None, description="NIFTY IT pre-open data")
    fo_securities: PreOpenResponse | None = Field(default=None, description="F&O securities pre-open data")
    all_indices: PreOpenResponse | None = Field(default=None, description="All indices pre-open data")

    @property
    def available_indices(self) -> list[str]:
        """Get list of available indices in this snapshot."""
        indices = []
        if self.nifty_50:
            indices.append("NIFTY")
        if self.nifty_bank:
            indices.append("BANKNIFTY")
        if self.nifty_it:
            indices.append("NIFTYIT")
        if self.fo_securities:
            indices.append("FO")
        if self.all_indices:
            indices.append("ALL")
        return indices
