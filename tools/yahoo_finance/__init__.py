"""
Yahoo Finance Tool - wrapper around yfinance library.

This module provides:
- YFinanceClient: Direct client for Yahoo Finance API
- YahooFinanceToolkit: Agno toolkit for agent integration

Example usage:
    from tools.yahoo_finance import YFinanceClient, YahooFinanceToolkit

    # Direct client usage
    client = YFinanceClient()
    info = client.get_ticker_info("AAPL")

    # Toolkit for agents
    toolkit = YahooFinanceToolkit()
    result = toolkit.get_stock_info("AAPL")
"""

from .client import YFinanceClient
from .toolkit import YahooFinanceToolkit
from .models.ticker import (
    TickerInfo, TickerHistory, TickerFinancials,
    TickerHolders, TickerAnalysis, TickerCalendar,
    TickerOptions, TickerSustainability,
    TickerFastInfo, TickerDividends, TickerSplits,
    TickerActions, TickerCapitalGains, TickerShares,
    TickerSECFilings, TickerISIN, FundsData,
    TickerHistoryMetadata,
)
from .models.market import (
    GlobalIndex, MarketStatus, CalendarsData,
    SearchResults, LookupResults, SectorData,
    IndustryData, ScreenerResult, BulkDownloadResult,
)

__all__ = [
    # Main classes
    "YFinanceClient",
    "YahooFinanceToolkit",

    # Ticker models
    "TickerInfo",
    "TickerHistory",
    "TickerFinancials",
    "TickerHolders",
    "TickerAnalysis",
    "TickerCalendar",
    "TickerOptions",
    "TickerSustainability",
    "TickerFastInfo",
    "TickerDividends",
    "TickerSplits",
    "TickerActions",
    "TickerCapitalGains",
    "TickerShares",
    "TickerSECFilings",
    "TickerISIN",
    "TickerHistoryMetadata",
    "FundsData",

    # Market models
    "GlobalIndex",
    "MarketStatus",
    "CalendarsData",
    "SearchResults",
    "LookupResults",
    "SectorData",
    "IndustryData",
    "ScreenerResult",
    "BulkDownloadResult",
]