"""
Screener.in SDK - Python client for Screener.in stock fundamentals.

This SDK provides a clean, typed interface for accessing Screener.in data,
including company search, historical chart data (prices, PE, margins),
and company fundamentals pages converted to markdown for LLM consumption.

Example:
    >>> from tools.screener import ScreenerClient
    >>> 
    >>> client = ScreenerClient()
    >>> 
    >>> # Search for a company
    >>> results = client.search("reliance")
    >>> company = results.first
    >>> print(f"Found: {company.name} (ID: {company.id})")
    >>> 
    >>> # Get price chart data
    >>> chart = client.get_price_chart(company.id, days=365)
    >>> print(f"Latest price: ₹{chart.price.latest_value}")
    >>> print(f"50 DMA: ₹{chart.dma50.latest_value}")
    >>> 
    >>> # Get company fundamentals as markdown (for LLM)
    >>> markdown = client.get_company_page("RELIANCE")
    >>> print(markdown)
    >>> 
    >>> # Get complete company summary
    >>> summary = client.get_company_summary("TCS")
    >>> print(f"PE: {summary['charts']['valuation'].pe_ratio.latest_value}")
"""

from .client import ScreenerClient
from .toolkit import ScreenerToolkit
from .core.exceptions import (
    ScreenerError,
    ScreenerAPIError,
    ScreenerConnectionError,
    ScreenerRateLimitError,
    ScreenerValidationError,
    ScreenerNotFoundError,
)
from .models.search import (
    CompanySearchResult,
    CompanySearchResponse,
)
from .models.chart import (
    ChartMetric,
    ChartDataPoint,
    ChartDataset,
    ChartResponse,
    PriceChartQuery,
    ValuationChartQuery,
    MarginChartQuery,
)

__version__ = "0.1.0"

__all__ = [
    # Main client
    "ScreenerClient",
    # Toolkit for agents
    "ScreenerToolkit",
    # Exceptions
    "ScreenerError",
    "ScreenerAPIError",
    "ScreenerConnectionError",
    "ScreenerRateLimitError",
    "ScreenerValidationError",
    "ScreenerNotFoundError",
    # Search models
    "CompanySearchResult",
    "CompanySearchResponse",
    # Chart models
    "ChartMetric",
    "ChartDataPoint",
    "ChartDataset",
    "ChartResponse",
    "PriceChartQuery",
    "ValuationChartQuery",
    "MarginChartQuery",
]