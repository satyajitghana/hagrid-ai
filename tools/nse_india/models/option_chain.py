"""Data models for NSE India option chain data."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, computed_field


class OptionContractInfo(BaseModel):
    """Option contract information for a symbol.

    Contains available expiry dates and strike prices.
    """

    model_config = ConfigDict(
        populate_by_name=True,
        str_strip_whitespace=True,
    )

    expiry_dates: list[str] = Field(
        alias="expiryDates", default_factory=list,
        description="Available expiry dates"
    )
    strike_prices: list[str] = Field(
        alias="strikePrice", default_factory=list,
        description="Available strike prices"
    )

    @property
    def strike_prices_float(self) -> list[float]:
        """Get strike prices as floats."""
        return [float(sp) for sp in self.strike_prices]


class OptionData(BaseModel):
    """Data for a single option (CE or PE)."""

    model_config = ConfigDict(
        populate_by_name=True,
        str_strip_whitespace=True,
    )

    strike_price: float = Field(alias="strikePrice", default=0)
    expiry_date: str | None = Field(alias="expiryDate", default=None)
    underlying: str | None = Field(default=None)
    identifier: str | None = Field(default=None)

    # Open Interest
    open_interest: int = Field(alias="openInterest", default=0)
    change_in_oi: int = Field(alias="changeinOpenInterest", default=0)
    pchange_in_oi: float = Field(alias="pchangeinOpenInterest", default=0)

    # Volume and Price
    total_traded_volume: int = Field(alias="totalTradedVolume", default=0)
    implied_volatility: float = Field(alias="impliedVolatility", default=0)
    last_price: float = Field(alias="lastPrice", default=0)
    change: float = Field(default=0)
    pchange: float = Field(default=0)

    # Order Book
    total_buy_quantity: int = Field(alias="totalBuyQuantity", default=0)
    total_sell_quantity: int = Field(alias="totalSellQuantity", default=0)
    bid_price: float = Field(alias="buyPrice1", default=0)
    bid_quantity: int = Field(alias="buyQuantity1", default=0)
    ask_price: float = Field(alias="sellPrice1", default=0)
    ask_quantity: int = Field(alias="sellQuantity1", default=0)

    underlying_value: float = Field(alias="underlyingValue", default=0)

    @property
    def is_valid(self) -> bool:
        """Check if this option data is valid (non-zero strike)."""
        return self.strike_price > 0 and self.underlying is not None

    @property
    def bid_ask_spread(self) -> float:
        """Calculate bid-ask spread."""
        if self.bid_price > 0 and self.ask_price > 0:
            return self.ask_price - self.bid_price
        return 0

    @property
    def bid_ask_spread_pct(self) -> float:
        """Calculate bid-ask spread as percentage of mid price."""
        if self.bid_price > 0 and self.ask_price > 0:
            mid = (self.bid_price + self.ask_price) / 2
            return (self.ask_price - self.bid_price) / mid * 100
        return 0


class OptionChainStrike(BaseModel):
    """Option chain data for a single strike price."""

    model_config = ConfigDict(
        populate_by_name=True,
        str_strip_whitespace=True,
    )

    expiry_dates: str = Field(alias="expiryDates", default="")
    strike_price: float = Field(alias="strikePrice", default=0)
    ce: OptionData | None = Field(alias="CE", default=None)
    pe: OptionData | None = Field(alias="PE", default=None)

    @property
    def has_ce(self) -> bool:
        """Check if CE data is valid."""
        return self.ce is not None and self.ce.is_valid

    @property
    def has_pe(self) -> bool:
        """Check if PE data is valid."""
        return self.pe is not None and self.pe.is_valid

    @property
    def ce_oi(self) -> int:
        """Get CE open interest."""
        return self.ce.open_interest if self.ce else 0

    @property
    def pe_oi(self) -> int:
        """Get PE open interest."""
        return self.pe.open_interest if self.pe else 0

    @property
    def total_oi(self) -> int:
        """Get total open interest for this strike."""
        return self.ce_oi + self.pe_oi


class OptionChainResponse(BaseModel):
    """Response from the option chain API."""

    model_config = ConfigDict(
        populate_by_name=True,
        str_strip_whitespace=True,
    )

    timestamp: str = Field(default="")
    underlying_value: float = Field(alias="underlyingValue", default=0)
    data: list[OptionChainStrike] = Field(default_factory=list)

    @computed_field
    @property
    def total_ce_oi(self) -> int:
        """Total call open interest."""
        return sum(s.ce_oi for s in self.data)

    @computed_field
    @property
    def total_pe_oi(self) -> int:
        """Total put open interest."""
        return sum(s.pe_oi for s in self.data)

    @computed_field
    @property
    def pcr(self) -> float:
        """Put-Call Ratio based on open interest."""
        if self.total_ce_oi > 0:
            return self.total_pe_oi / self.total_ce_oi
        return 0

    @property
    def max_ce_oi_strike(self) -> tuple[float, int]:
        """Get strike with maximum call OI."""
        max_oi = 0
        max_strike = 0
        for s in self.data:
            if s.ce_oi > max_oi:
                max_oi = s.ce_oi
                max_strike = s.strike_price
        return (max_strike, max_oi)

    @property
    def max_pe_oi_strike(self) -> tuple[float, int]:
        """Get strike with maximum put OI."""
        max_oi = 0
        max_strike = 0
        for s in self.data:
            if s.pe_oi > max_oi:
                max_oi = s.pe_oi
                max_strike = s.strike_price
        return (max_strike, max_oi)

    @property
    def atm_strike(self) -> float:
        """Get ATM (at-the-money) strike closest to underlying."""
        if not self.data or self.underlying_value == 0:
            return 0
        valid_strikes = [s.strike_price for s in self.data if s.strike_price > 0]
        if not valid_strikes:
            return 0
        return min(valid_strikes, key=lambda x: abs(x - self.underlying_value))

    def get_strike_data(self, strike: float) -> OptionChainStrike | None:
        """Get option data for a specific strike."""
        for s in self.data:
            if s.strike_price == strike:
                return s
        return None

    def get_atm_data(self) -> OptionChainStrike | None:
        """Get ATM strike data."""
        atm = self.atm_strike
        if atm > 0:
            return self.get_strike_data(atm)
        return None

    def get_itm_calls(self) -> list[OptionChainStrike]:
        """Get in-the-money calls (strike < underlying)."""
        return [s for s in self.data if s.strike_price < self.underlying_value and s.has_ce]

    def get_otm_calls(self) -> list[OptionChainStrike]:
        """Get out-of-the-money calls (strike > underlying)."""
        return [s for s in self.data if s.strike_price > self.underlying_value and s.has_ce]

    def get_itm_puts(self) -> list[OptionChainStrike]:
        """Get in-the-money puts (strike > underlying)."""
        return [s for s in self.data if s.strike_price > self.underlying_value and s.has_pe]

    def get_otm_puts(self) -> list[OptionChainStrike]:
        """Get out-of-the-money puts (strike < underlying)."""
        return [s for s in self.data if s.strike_price < self.underlying_value and s.has_pe]

    def get_strikes_near_atm(self, num_strikes: int = 5) -> list[OptionChainStrike]:
        """Get N strikes above and below ATM."""
        atm = self.atm_strike
        if atm == 0:
            return []

        sorted_data = sorted(self.data, key=lambda x: x.strike_price)
        atm_idx = None
        for i, s in enumerate(sorted_data):
            if s.strike_price == atm:
                atm_idx = i
                break

        if atm_idx is None:
            return []

        start = max(0, atm_idx - num_strikes)
        end = min(len(sorted_data), atm_idx + num_strikes + 1)
        return sorted_data[start:end]


class OptionChainAnalysis(BaseModel):
    """Analysis summary of option chain data."""

    symbol: str
    expiry: str
    underlying_value: float
    timestamp: str

    # PCR
    pcr: float
    total_ce_oi: int
    total_pe_oi: int

    # Max OI
    max_ce_oi_strike: float
    max_ce_oi: int
    max_pe_oi_strike: float
    max_pe_oi: int

    # ATM
    atm_strike: float
    atm_ce_ltp: float = 0
    atm_ce_iv: float = 0
    atm_pe_ltp: float = 0
    atm_pe_iv: float = 0

    # Support/Resistance
    resistance_level: float = 0  # Max call OI strike
    support_level: float = 0  # Max put OI strike

    @property
    def sentiment(self) -> str:
        """Market sentiment based on PCR."""
        if self.pcr > 1.2:
            return "Bullish"
        elif self.pcr < 0.8:
            return "Bearish"
        return "Neutral"

    @classmethod
    def from_option_chain(
        cls, symbol: str, expiry: str, chain: OptionChainResponse
    ) -> "OptionChainAnalysis":
        """Create analysis from option chain response."""
        atm = chain.get_atm_data()
        max_ce = chain.max_ce_oi_strike
        max_pe = chain.max_pe_oi_strike

        return cls(
            symbol=symbol,
            expiry=expiry,
            underlying_value=chain.underlying_value,
            timestamp=chain.timestamp,
            pcr=chain.pcr,
            total_ce_oi=chain.total_ce_oi,
            total_pe_oi=chain.total_pe_oi,
            max_ce_oi_strike=max_ce[0],
            max_ce_oi=max_ce[1],
            max_pe_oi_strike=max_pe[0],
            max_pe_oi=max_pe[1],
            atm_strike=chain.atm_strike,
            atm_ce_ltp=atm.ce.last_price if atm and atm.ce else 0,
            atm_ce_iv=atm.ce.implied_volatility if atm and atm.ce else 0,
            atm_pe_ltp=atm.pe.last_price if atm and atm.pe else 0,
            atm_pe_iv=atm.pe.implied_volatility if atm and atm.pe else 0,
            resistance_level=max_ce[0],
            support_level=max_pe[0],
        )
