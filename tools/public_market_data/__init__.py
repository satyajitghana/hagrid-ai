"""Public Market Data toolkit for fetching publicly available market information.

This toolkit provides access to:
- CDSL FII/FPI investment data (monthly and fortnightly reports)
"""

from .client import PublicMarketDataClient
from .toolkit import PublicMarketDataToolkit
from .core.exceptions import (
    PublicMarketDataError,
    PublicMarketDataAPIError,
    PublicMarketDataConnectionError,
    PublicMarketDataNotFoundError,
    PublicMarketDataParseError,
)

__all__ = [
    "PublicMarketDataClient",
    "PublicMarketDataToolkit",
    "PublicMarketDataError",
    "PublicMarketDataAPIError",
    "PublicMarketDataConnectionError",
    "PublicMarketDataNotFoundError",
    "PublicMarketDataParseError",
]
