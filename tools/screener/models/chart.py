"""Chart API response models."""

import datetime as dt
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class ChartMetric(str, Enum):
    """Available chart metrics."""
    
    # Price metrics
    PRICE = "Price"
    DMA50 = "DMA50"
    DMA200 = "DMA200"
    VOLUME = "Volume"
    
    # Valuation metrics
    PRICE_TO_EARNING = "Price to Earning"
    MEDIAN_PE = "Median PE"
    EPS = "EPS"
    MARKET_CAP_TO_SALES = "Market Cap to Sales"
    MEDIAN_MARKET_CAP_TO_SALES = "Median Market Cap to Sales"
    SALES = "Sales"
    
    # Margin metrics
    GPM = "GPM"  # Gross Profit Margin
    OPM = "OPM"  # Operating Profit Margin
    NPM = "NPM"  # Net Profit Margin
    QUARTER_SALES = "Quarter Sales"


class ChartDataPoint(BaseModel):
    """Single data point in a chart series."""
    
    data_date: dt.date = Field(description="Date of the data point")
    value: float | None = Field(default=None, description="Value at this date")
    extra: dict[str, Any] | None = Field(
        default=None,
        description="Additional data (e.g., delivery percentage for volume)"
    )
    
    @classmethod
    def from_raw(cls, raw: list) -> "ChartDataPoint":
        """Create from raw API data.
        
        Raw data can be:
        - [date, value]
        - [date, value, extra_dict]
        """
        date_str = raw[0]
        value = raw[1] if len(raw) > 1 else None
        extra = raw[2] if len(raw) > 2 else None
        
        # Parse date
        parsed_date = dt.datetime.strptime(date_str, "%Y-%m-%d").date()
        
        # Handle string values (e.g., "1239.85")
        if isinstance(value, str):
            try:
                value = float(value)
            except (ValueError, TypeError):
                value = None
        
        return cls(data_date=parsed_date, value=value, extra=extra)


class ChartDataset(BaseModel):
    """Single dataset in chart response."""
    
    metric: str = Field(description="Metric identifier")
    label: str = Field(description="Display label for this dataset")
    values: list[ChartDataPoint] = Field(
        default_factory=list,
        description="Data points in this dataset"
    )
    meta: dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata"
    )
    
    @property
    def is_weekly(self) -> bool:
        """Check if data is weekly."""
        return self.meta.get("is_weekly", False)
    
    @property
    def latest_value(self) -> float | None:
        """Get the most recent value."""
        if self.values:
            return self.values[-1].value
        return None
    
    @property
    def latest_date(self) -> dt.date | None:
        """Get the most recent date."""
        if self.values:
            return self.values[-1].data_date
        return None
    
    def get_value_at(self, target_date: dt.date) -> float | None:
        """Get value at a specific date."""
        for point in self.values:
            if point.data_date == target_date:
                return point.value
        return None
    
    def to_dict(self) -> dict[str, float | None]:
        """Convert to date:value dictionary."""
        return {str(point.data_date): point.value for point in self.values}


class ChartResponse(BaseModel):
    """Response from chart API."""
    
    datasets: list[ChartDataset] = Field(
        default_factory=list,
        description="Chart datasets"
    )
    
    @classmethod
    def from_api_response(cls, data: dict) -> "ChartResponse":
        """Create response from raw API data."""
        datasets = []
        
        for raw_dataset in data.get("datasets", []):
            values = [
                ChartDataPoint.from_raw(v) 
                for v in raw_dataset.get("values", [])
            ]
            
            dataset = ChartDataset(
                metric=raw_dataset.get("metric", ""),
                label=raw_dataset.get("label", ""),
                values=values,
                meta=raw_dataset.get("meta", {}),
            )
            datasets.append(dataset)
        
        return cls(datasets=datasets)
    
    def get_dataset(self, metric: str) -> ChartDataset | None:
        """Get a specific dataset by metric name."""
        for dataset in self.datasets:
            if dataset.metric == metric:
                return dataset
        return None
    
    @property
    def price(self) -> ChartDataset | None:
        """Get price dataset."""
        return self.get_dataset("Price")
    
    @property
    def dma50(self) -> ChartDataset | None:
        """Get 50-day moving average dataset."""
        return self.get_dataset("DMA50")
    
    @property
    def dma200(self) -> ChartDataset | None:
        """Get 200-day moving average dataset."""
        return self.get_dataset("DMA200")
    
    @property
    def volume(self) -> ChartDataset | None:
        """Get volume dataset."""
        return self.get_dataset("Volume")
    
    @property
    def pe_ratio(self) -> ChartDataset | None:
        """Get PE ratio dataset."""
        return self.get_dataset("Price to Earning")
    
    @property
    def eps(self) -> ChartDataset | None:
        """Get EPS dataset."""
        return self.get_dataset("EPS")
    
    @property
    def gpm(self) -> ChartDataset | None:
        """Get Gross Profit Margin dataset."""
        return self.get_dataset("GPM")
    
    @property
    def opm(self) -> ChartDataset | None:
        """Get Operating Profit Margin dataset."""
        return self.get_dataset("OPM")
    
    @property
    def npm(self) -> ChartDataset | None:
        """Get Net Profit Margin dataset."""
        return self.get_dataset("NPM")


class PriceChartQuery(str, Enum):
    """Predefined chart queries for price data."""
    
    PRICE_WITH_MA = "Price-DMA50-DMA200-Volume"
    PRICE_ONLY = "Price"
    PRICE_VOLUME = "Price-Volume"


class ValuationChartQuery(str, Enum):
    """Predefined chart queries for valuation data."""
    
    PE_EPS = "Price+to+Earning-Median+PE-EPS"
    MARKET_CAP_SALES = "Market+Cap+to+Sales-Median+Market+Cap+to+Sales-Sales"


class MarginChartQuery(str, Enum):
    """Predefined chart queries for margin data."""
    
    ALL_MARGINS = "GPM-OPM-NPM-Quarter+Sales"
    OPM_ONLY = "OPM"
    NPM_ONLY = "NPM"