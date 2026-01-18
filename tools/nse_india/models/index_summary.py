"""Data models for NSE India index summary data."""

from pydantic import BaseModel, ConfigDict, Field, computed_field


class IndexPriceData(BaseModel):
    """Index price and valuation data."""

    model_config = ConfigDict(
        populate_by_name=True,
        str_strip_whitespace=True,
    )

    index_name: str = Field(alias="indexName", default="", description="Index name")
    open: float = Field(default=0, description="Opening value")
    high: float = Field(default=0, description="Day high")
    low: float = Field(default=0, description="Day low")
    last: float = Field(default=0, description="Last traded value")
    previous_close: float = Field(alias="previousClose", default=0, description="Previous close")
    perc_change: float = Field(alias="percChange", default=0, description="Percentage change")

    # 52-week data
    year_high: float = Field(alias="yearHigh", default=0, description="52-week high")
    year_low: float = Field(alias="yearLow", default=0, description="52-week low")

    # Valuation metrics
    pe_ratio: float = Field(alias="peRatio", default=0, description="Price to Earnings ratio")
    pb_ratio: float = Field(alias="pbRatio", default=0, description="Price to Book ratio")
    dividend_yield: float = Field(alias="dividentYield", default=0, description="Dividend yield %")

    # Market cap
    ffm: float = Field(default=0, description="Free float market cap (in trillion)")
    full: float = Field(default=0, description="Full market cap")

    # Volume and value
    volume: float = Field(default=0, description="Traded volume (in crore)")
    value: float = Field(default=0, description="Traded value (in crore)")

    # Timestamp
    time_val: str = Field(alias="timeVal", default="", description="Data timestamp")

    @property
    def change(self) -> float:
        """Calculate absolute change."""
        return self.last - self.previous_close

    @property
    def near_52_week_high(self) -> bool:
        """Check if within 5% of 52-week high."""
        if self.year_high > 0:
            return self.last >= self.year_high * 0.95
        return False

    @property
    def near_52_week_low(self) -> bool:
        """Check if within 5% of 52-week low."""
        if self.year_low > 0:
            return self.last <= self.year_low * 1.05
        return False

    @property
    def pct_from_high(self) -> float:
        """Percentage away from 52-week high."""
        if self.year_high > 0:
            return ((self.year_high - self.last) / self.year_high) * 100
        return 0

    @property
    def pct_from_low(self) -> float:
        """Percentage above 52-week low."""
        if self.year_low > 0:
            return ((self.last - self.year_low) / self.year_low) * 100
        return 0


class IndexReturns(BaseModel):
    """Index returns across multiple time periods."""

    model_config = ConfigDict(
        populate_by_name=True,
        str_strip_whitespace=True,
    )

    yesterday: float = Field(alias="yesterday_chng_per", default=0, description="Yesterday's change %")
    one_week: float = Field(alias="one_week_chng_per", default=0, description="1 week return %")
    one_month: float = Field(alias="one_month_chng_per", default=0, description="1 month return %")
    three_month: float = Field(alias="three_month_chng_per", default=0, description="3 month return %")
    six_month: float = Field(alias="six_month_chng_per", default=0, description="6 month return %")
    one_year: float = Field(alias="one_year_chng_per", default=0, description="1 year return %")
    two_year: float = Field(alias="two_year_chng_per", default=0, description="2 year return %")
    three_year: float = Field(alias="three_year_chng_per", default=0, description="3 year return %")
    five_year: float = Field(alias="five_year_chng_per", default=0, description="5 year return %")

    one_week_date: str = Field(alias="one_week_date", default="", description="1 week ago date")

    @property
    def trend(self) -> str:
        """Determine overall trend based on returns."""
        if self.one_week > 0 and self.one_month > 0 and self.three_month > 0:
            return "Strong Uptrend"
        elif self.one_week > 0 and self.one_month > 0:
            return "Uptrend"
        elif self.one_week < 0 and self.one_month < 0 and self.three_month < 0:
            return "Strong Downtrend"
        elif self.one_week < 0 and self.one_month < 0:
            return "Downtrend"
        else:
            return "Sideways"


class IndexFacts(BaseModel):
    """Index factsheet and methodology information."""

    model_config = ConfigDict(
        populate_by_name=True,
        str_strip_whitespace=True,
    )

    long_name: str = Field(alias="indiceslongName", default="", description="Full index name")
    constituents_csv: str | None = Field(
        alias="indexConstituents", default=None,
        description="URL to constituents CSV"
    )
    methodology_pdf: str | None = Field(
        alias="methodology", default=None,
        description="URL to methodology PDF"
    )
    description: str = Field(default="", description="Index description")
    factsheet_pdf: str | None = Field(
        alias="factsheet", default=None,
        description="URL to factsheet PDF"
    )


class IndexAdvanceDeclineData(BaseModel):
    """Advance/Decline data for an index."""

    model_config = ConfigDict(
        populate_by_name=True,
        str_strip_whitespace=True,
    )

    index_name: str = Field(alias="indexName", default="", description="Index name")
    advances: int = Field(alias="advance_symbol", default=0, description="Advancing stocks")
    declines: int = Field(alias="decline_symbol", default=0, description="Declining stocks")
    unchanged: int = Field(alias="unchanged_symbol", default=0, description="Unchanged stocks")
    total: int = Field(alias="total_symbol", default=0, description="Total stocks")

    # Turnover by category
    advance_turnover: float = Field(
        alias="advance_top_turnover", default=0,
        description="Turnover of advancing stocks"
    )
    decline_turnover: float = Field(
        alias="decline_top_turnover", default=0,
        description="Turnover of declining stocks"
    )
    total_turnover: float = Field(
        alias="total_top_turnover", default=0,
        description="Total turnover"
    )

    # Circuit breakers
    upper_circuit_count: int = Field(alias="upper_cktcount", default=0)
    lower_circuit_count: int = Field(alias="lower_cktcount", default=0)

    @computed_field
    @property
    def advance_decline_ratio(self) -> float:
        """Calculate A/D ratio."""
        if self.declines > 0:
            return self.advances / self.declines
        return float('inf') if self.advances > 0 else 0

    @property
    def market_sentiment(self) -> str:
        """Determine market sentiment."""
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
    def breadth_percentage(self) -> float:
        """Percentage of stocks advancing."""
        if self.total > 0:
            return (self.advances / self.total) * 100
        return 0


class IndexContributor(BaseModel):
    """Stock contributing to index movement."""

    model_config = ConfigDict(
        populate_by_name=True,
        str_strip_whitespace=True,
    )

    symbol: str = Field(alias="icSymbol", default="", description="Stock symbol")
    company_name: str = Field(alias="icSecurity", default="", description="Company name")
    last_price: float = Field(alias="lastTradedPrice", default=0, description="Last traded price")
    close_price: float = Field(alias="closePrice", default=0, description="Previous close")
    change_pct: float = Field(alias="changePer", default=0, description="% change")
    change_points: float = Field(alias="changePoints", default=0, description="Index points contribution")
    rank_positive: int = Field(alias="rnPositive", default=0, description="Rank among positive contributors")
    rank_negative: int = Field(alias="rnNegative", default=0, description="Rank among negative contributors")
    is_positive: str = Field(alias="isPositive", default="", description="Y/N for positive contribution")

    @property
    def is_positive_contributor(self) -> bool:
        """Check if stock is a positive contributor."""
        return self.is_positive == "Y"


class IndexHeatmapStock(BaseModel):
    """Stock data for index heatmap."""

    model_config = ConfigDict(
        populate_by_name=True,
        str_strip_whitespace=True,
    )

    symbol: str = Field(default="", description="Stock symbol")
    identifier: str = Field(default="", description="Identifier")
    series: str = Field(default="", description="Series")
    last_price: float = Field(alias="lastPrice", default=0, description="Last price")
    change: float = Field(default=0, description="Absolute change")
    pchange: float = Field(default=0, description="Percentage change")
    vwap: float = Field(default=0, description="Volume weighted avg price")
    high: float = Field(default=0, description="Day high")
    low: float = Field(default=0, description="Day low")
    traded_volume: int = Field(alias="tradedVolume", default=0, description="Traded volume")
    traded_value: float = Field(alias="tradedValue", default=0, description="Traded value")


class IndexTopMover(BaseModel):
    """Top gainer or loser in the index."""

    model_config = ConfigDict(
        populate_by_name=True,
        str_strip_whitespace=True,
    )

    symbol: str = Field(default="", description="Stock symbol")
    series: str = Field(default="", description="Series")
    open_price: float = Field(alias="openPrice", default=0, description="Open price")
    high_price: float = Field(alias="highPrice", default=0, description="52-week high")
    low_price: float = Field(alias="lowPrice", default=0, description="52-week low")
    last_price: float = Field(alias="lastPrice", default=0, description="Last price")
    previous_close: float = Field(alias="previousClose", default=0, description="Previous close")
    change: float = Field(default=0, description="Absolute change")
    pchange: float = Field(default=0, description="Percentage change")
    total_traded_volume: int = Field(alias="totalTradedVolume", default=0, description="Volume")
    total_traded_value: float = Field(alias="totalTradedValue", default=0, description="Value")
    ca_ex_date: str | None = Field(alias="caExDt", default=None, description="Corporate action ex-date")
    ca_purpose: str | None = Field(alias="caPurpose", default=None, description="Corporate action purpose")


class IndexAnnouncement(BaseModel):
    """Corporate announcement for index constituent."""

    model_config = ConfigDict(
        populate_by_name=True,
        str_strip_whitespace=True,
    )

    company_name: str = Field(alias="companyName", default="", description="Company name")
    symbol: str = Field(default="", description="Stock symbol")
    subject: str = Field(default="", description="Announcement subject")
    details: str = Field(default="", description="Announcement details")
    broadcast_date: str = Field(alias="broadcastDate", default="", description="Broadcast date")
    attachment: str | None = Field(default=None, description="Attachment URL")
    file_size: str | None = Field(alias="fileSize", default=None, description="File size")


class IndexBoardMeeting(BaseModel):
    """Board meeting for index constituent."""

    model_config = ConfigDict(
        populate_by_name=True,
        str_strip_whitespace=True,
    )

    symbol: str = Field(alias="bm_symbol", default="", description="Stock symbol")
    company_name: str = Field(alias="sm_name", default="", description="Company name")
    meeting_date: str = Field(alias="bm_date", default="", description="Meeting date")
    purpose: str = Field(alias="bm_purpose", default="", description="Meeting purpose")
    attachment: str | None = Field(default=None, description="Attachment URL")
    ixbrl: str | None = Field(default=None, description="iXBRL URL")
    timestamp: str = Field(alias="bm_timestamp", default="", description="Intimation timestamp")


class IndexChartPoint(BaseModel):
    """Single point in index chart data."""

    timestamp: int = Field(description="Unix timestamp in milliseconds")
    value: float = Field(description="Index value")
    market_phase: str = Field(default="", description="Market phase (PO=Pre-open, NM=Normal)")


class IndexChartData(BaseModel):
    """Index chart data."""

    model_config = ConfigDict(
        populate_by_name=True,
        str_strip_whitespace=True,
    )

    identifier: str = Field(default="", description="Index identifier")
    name: str = Field(default="", description="Index name")
    data_points: list[IndexChartPoint] = Field(default_factory=list, description="Chart data points")


class IndexSummaryData(BaseModel):
    """Comprehensive index summary data."""

    model_config = ConfigDict(
        populate_by_name=True,
        str_strip_whitespace=True,
    )

    # Basic info
    index_name: str = Field(default="", description="Index name")
    timestamp: str = Field(default="", description="Data timestamp")

    # Price and valuation
    price_data: IndexPriceData | None = Field(default=None, description="Price and valuation data")

    # Returns
    returns: IndexReturns | None = Field(default=None, description="Returns data")

    # Facts
    facts: IndexFacts | None = Field(default=None, description="Index facts and methodology")

    # Breadth
    advance_decline: IndexAdvanceDeclineData | None = Field(default=None, description="Advance/decline data")

    # Contributors
    top_contributors: list[IndexContributor] = Field(
        default_factory=list,
        description="Top point contributors (positive)"
    )
    bottom_contributors: list[IndexContributor] = Field(
        default_factory=list,
        description="Bottom point contributors (negative)"
    )

    # Gainers and losers
    top_gainers: list[IndexTopMover] = Field(default_factory=list, description="Top gainers")
    top_losers: list[IndexTopMover] = Field(default_factory=list, description="Top losers")

    # Heatmap
    heatmap: list[IndexHeatmapStock] = Field(default_factory=list, description="All stocks heatmap data")

    # Corporate events
    announcements: list[IndexAnnouncement] = Field(
        default_factory=list,
        description="Recent announcements"
    )
    board_meetings: list[IndexBoardMeeting] = Field(
        default_factory=list,
        description="Upcoming board meetings"
    )

    @property
    def constituent_count(self) -> int:
        """Get number of constituents."""
        return len(self.heatmap)

    @property
    def advancing_count(self) -> int:
        """Count of advancing stocks."""
        return sum(1 for s in self.heatmap if s.pchange > 0)

    @property
    def declining_count(self) -> int:
        """Count of declining stocks."""
        return sum(1 for s in self.heatmap if s.pchange < 0)

    def format_summary(self) -> str:
        """Format index summary as readable text."""
        lines = []

        # Header
        lines.append(f"# {self.index_name} Summary")
        lines.append(f"*As of {self.timestamp}*\n")

        # Price data
        if self.price_data:
            pd = self.price_data
            lines.append("## Price & Valuation")
            lines.append(f"- **Last:** {pd.last:,.2f} ({pd.perc_change:+.2f}%)")
            lines.append(f"- **Day Range:** {pd.low:,.2f} - {pd.high:,.2f}")
            lines.append(f"- **52W Range:** {pd.year_low:,.2f} - {pd.year_high:,.2f}")
            lines.append(f"- **P/E Ratio:** {pd.pe_ratio:.2f}")
            lines.append(f"- **P/B Ratio:** {pd.pb_ratio:.2f}")
            lines.append(f"- **Dividend Yield:** {pd.dividend_yield:.2f}%")
            lines.append(f"- **Turnover:** ₹{pd.value:,.2f} Cr")
            lines.append("")

        # Returns
        if self.returns:
            ret = self.returns
            lines.append("## Returns")
            lines.append(f"- **1 Week:** {ret.one_week:+.2f}%")
            lines.append(f"- **1 Month:** {ret.one_month:+.2f}%")
            lines.append(f"- **3 Month:** {ret.three_month:+.2f}%")
            lines.append(f"- **6 Month:** {ret.six_month:+.2f}%")
            lines.append(f"- **1 Year:** {ret.one_year:+.2f}%")
            lines.append(f"- **Trend:** {ret.trend}")
            lines.append("")

        # Market breadth
        if self.advance_decline:
            ad = self.advance_decline
            lines.append("## Market Breadth")
            lines.append(f"- **Advances:** {ad.advances} | **Declines:** {ad.declines} | **Unchanged:** {ad.unchanged}")
            lines.append(f"- **A/D Ratio:** {ad.advance_decline_ratio:.2f}")
            lines.append(f"- **Sentiment:** {ad.market_sentiment}")
            lines.append("")

        # Top contributors
        if self.top_contributors:
            lines.append("## Top Point Contributors")
            for c in self.top_contributors[:5]:
                lines.append(f"- {c.symbol}: {c.change_points:+.2f} pts ({c.change_pct:+.2f}%)")
            lines.append("")

        # Top gainers
        if self.top_gainers:
            lines.append("## Top Gainers")
            for g in self.top_gainers[:5]:
                lines.append(f"- {g.symbol}: {g.last_price:,.2f} ({g.pchange:+.2f}%)")
            lines.append("")

        # Top losers
        if self.top_losers:
            lines.append("## Top Losers")
            for l in self.top_losers[:5]:
                lines.append(f"- {l.symbol}: {l.last_price:,.2f} ({l.pchange:+.2f}%)")
            lines.append("")

        # Board meetings
        if self.board_meetings:
            lines.append("## Upcoming Board Meetings")
            for bm in self.board_meetings[:5]:
                lines.append(f"- {bm.symbol} ({bm.meeting_date}): {bm.purpose}")
            lines.append("")

        # Announcements
        if self.announcements:
            lines.append("## Recent Announcements")
            for ann in self.announcements[:5]:
                lines.append(f"- {ann.symbol}: {ann.subject}")
            lines.append("")

        # Facts
        if self.facts and self.facts.description:
            lines.append("## About This Index")
            lines.append(self.facts.description[:500] + "..." if len(self.facts.description) > 500 else self.facts.description)
            lines.append("")

        return "\n".join(lines)
