"""NSE India API client for corporate announcements and annual reports."""

from .client import NSEIndiaClient
from .core.cache import CacheConfig, CacheTTL, clear_cache, get_cache
from .models.announcement import (
    Announcement,
    AnnualReport,
    DebtAnnouncement,
    EquityAnnouncement,
    ShareholdingPattern,
)
from .models.enums import AnnouncementIndex, AnnouncementSubject, FinancialResultPeriod
from .models.financial_results import FinancialResult
from .models.indices import AllIndicesResponse, IndexCategory, IndexData
from .models.oi_spurts import OISpurtData, OISpurtsResponse
from .models.deals import BlockDeal, BulkDeal, DealType, LargeDealsSnapshot, ShortSelling
from .models.stocks_traded import StockTraded, StocksTradedCount, StocksTradedResponse
from .models.price_band import (
    PriceBandCategory,
    PriceBandCount,
    PriceBandHitter,
    PriceBandResponse,
)
from .models.securities import SecuritiesResponse, Security, TradingSeries
from .models.chart import (
    ChartCandle,
    ChartDataResponse,
    ChartSymbol,
    ChartType,
    SymbolSearchResponse,
    SymbolType,
)
from .storage.tracker import AnnouncementTracker, ProcessedAnnouncement
from .toolkit import NSEIndiaToolkit

__all__ = [
    # Main client
    "NSEIndiaClient",
    # Toolkit
    "NSEIndiaToolkit",
    # Cache
    "CacheConfig",
    "CacheTTL",
    "get_cache",
    "clear_cache",
    # Models
    "Announcement",
    "AnnualReport",
    "DebtAnnouncement",
    "EquityAnnouncement",
    "ShareholdingPattern",
    "FinancialResult",
    # Indices
    "AllIndicesResponse",
    "IndexCategory",
    "IndexData",
    # OI Spurts
    "OISpurtData",
    "OISpurtsResponse",
    # Enums
    "AnnouncementIndex",
    "AnnouncementSubject",
    "FinancialResultPeriod",
    # Storage
    "AnnouncementTracker",
    "ProcessedAnnouncement",
    # Deals (bulk, block, short selling)
    "BlockDeal",
    "BulkDeal",
    "DealType",
    "LargeDealsSnapshot",
    "ShortSelling",
    # Stocks Traded
    "StockTraded",
    "StocksTradedCount",
    "StocksTradedResponse",
    # Price Band Hitters
    "PriceBandCategory",
    "PriceBandCount",
    "PriceBandHitter",
    "PriceBandResponse",
    # Securities (Listed Stocks)
    "SecuritiesResponse",
    "Security",
    "TradingSeries",
    # Chart/Historical Data
    "ChartCandle",
    "ChartDataResponse",
    "ChartSymbol",
    "ChartType",
    "SymbolSearchResponse",
    "SymbolType",
]
