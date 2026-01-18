"""Data models for NSE India API."""

from .announcement import (
    Announcement,
    AnnualReport,
    DebtAnnouncement,
    EquityAnnouncement,
    ShareholdingPattern,
)
from .enums import AnnouncementIndex, AnnouncementSubject, FinancialResultPeriod
from .event_calendar import CorporateEvent
from .financial_results import (
    FinancialResult,
    FinancialResultPeriodData,
    FinancialResultsComparison,
)
from .insider_trading import (
    InsiderTradingPlan,
    InsiderTransaction,
    InsiderTransactionResponse,
)
from .indices import AllIndicesResponse, IndexCategory, IndexData
from .oi_spurts import OISpurtData, OISpurtsResponse
from .most_active import (
    MostActiveEquity,
    MostActiveETF,
    MostActiveETFResponse,
    MostActiveResponse,
    MostActiveSME,
    MostActiveSMEResponse,
    PriceVariation,
    PriceVariationsResponse,
    VolumeGainer,
    VolumeGainersResponse,
)
from .option_chain import (
    OptionChainAnalysis,
    OptionChainResponse,
    OptionChainStrike,
    OptionContractInfo,
    OptionData,
)
from .deals import (
    BlockDeal,
    BulkDeal,
    DealType,
    LargeDealsSnapshot,
    ShortSelling,
)
from .advances_declines import (
    AdvancesResponse,
    DeclinesResponse,
    MarketBreadthCount,
    MarketBreadthSnapshot,
    MarketMover,
)
from .stocks_traded import (
    StockTraded,
    StocksTradedCount,
    StocksTradedResponse,
)
from .shareholding import (
    BeneficialOwner,
    DetailedShareholdingPattern,
    ShareholderDetail,
    ShareholdingDeclaration,
    ShareholdingSummary,
)
from .price_band import (
    PriceBandCategory,
    PriceBandCount,
    PriceBandHitter,
    PriceBandResponse,
)
from .pre_open import (
    PreOpenMarketDetail,
    PreOpenMarketSnapshot,
    PreOpenOrder,
    PreOpenResponse,
    PreOpenStock,
    PreOpenStockMetadata,
)
from .securities import (
    SecuritiesResponse,
    Security,
    TradingSeries,
)
from .index_constituents import (
    IndexAdvanceDecline,
    IndexConstituent,
    IndexConstituentsResponse,
    IndexMaster,
    StockMeta,
)
from .chart import (
    ChartCandle,
    ChartDataResponse,
    ChartSymbol,
    ChartType,
    SymbolSearchResponse,
    SymbolType,
)
from .index_summary import (
    IndexAdvanceDeclineData,
    IndexAnnouncement,
    IndexBoardMeeting,
    IndexChartData,
    IndexChartPoint,
    IndexContributor,
    IndexFacts,
    IndexHeatmapStock,
    IndexPriceData,
    IndexReturns,
    IndexSummaryData,
    IndexTopMover,
)

__all__ = [
    "Announcement",
    "AnnualReport",
    "DebtAnnouncement",
    "EquityAnnouncement",
    "ShareholdingPattern",
    "AnnouncementIndex",
    "AnnouncementSubject",
    # Event calendar
    "CorporateEvent",
    # Financial results
    "FinancialResult",
    "FinancialResultPeriod",
    "FinancialResultPeriodData",
    "FinancialResultsComparison",
    # Insider trading
    "InsiderTradingPlan",
    "InsiderTransaction",
    "InsiderTransactionResponse",
    # Detailed shareholding models
    "BeneficialOwner",
    "DetailedShareholdingPattern",
    "ShareholderDetail",
    "ShareholdingDeclaration",
    "ShareholdingSummary",
    # Market indices
    "AllIndicesResponse",
    "IndexCategory",
    "IndexData",
    # OI Spurts
    "OISpurtData",
    "OISpurtsResponse",
    # Most Active Securities
    "MostActiveEquity",
    "MostActiveETF",
    "MostActiveETFResponse",
    "MostActiveResponse",
    "MostActiveSME",
    "MostActiveSMEResponse",
    "PriceVariation",
    "PriceVariationsResponse",
    "VolumeGainer",
    "VolumeGainersResponse",
    # Option chain
    "OptionChainAnalysis",
    "OptionChainResponse",
    "OptionChainStrike",
    "OptionContractInfo",
    "OptionData",
    # Deals (bulk, block, short selling)
    "BlockDeal",
    "BulkDeal",
    "DealType",
    "LargeDealsSnapshot",
    "ShortSelling",
    # Advances/Declines (market breadth)
    "AdvancesResponse",
    "DeclinesResponse",
    "MarketBreadthCount",
    "MarketBreadthSnapshot",
    "MarketMover",
    # Stocks Traded
    "StockTraded",
    "StocksTradedCount",
    "StocksTradedResponse",
    # Price Band Hitters
    "PriceBandCategory",
    "PriceBandCount",
    "PriceBandHitter",
    "PriceBandResponse",
    # Pre-Open Market
    "PreOpenMarketDetail",
    "PreOpenMarketSnapshot",
    "PreOpenOrder",
    "PreOpenResponse",
    "PreOpenStock",
    "PreOpenStockMetadata",
    # Securities (Listed Stocks)
    "SecuritiesResponse",
    "Security",
    "TradingSeries",
    # Index Constituents
    "IndexAdvanceDecline",
    "IndexConstituent",
    "IndexConstituentsResponse",
    "IndexMaster",
    "StockMeta",
    # Chart/Historical Data
    "ChartCandle",
    "ChartDataResponse",
    "ChartSymbol",
    "ChartType",
    "SymbolSearchResponse",
    "SymbolType",
    # Index Summary/Tracker
    "IndexAdvanceDeclineData",
    "IndexAnnouncement",
    "IndexBoardMeeting",
    "IndexChartData",
    "IndexChartPoint",
    "IndexContributor",
    "IndexFacts",
    "IndexHeatmapStock",
    "IndexPriceData",
    "IndexReturns",
    "IndexSummaryData",
    "IndexTopMover",
]
