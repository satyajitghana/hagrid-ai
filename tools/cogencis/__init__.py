"""
Cogencis SDK - Python client for Cogencis Market Data API.

This SDK provides a clean, typed interface for interacting with the Cogencis API,
including symbol lookup, auditor information, news data, shareholders, block deals,
insider trading, SAST transactions, capital history, announcements, corporate actions,
and tribunal cases.

Example:
    >>> from tools.cogencis import CogencisClient
    >>> 
    >>> client = CogencisClient(bearer_token="your_token")
    >>> 
    >>> # Search for symbols
    >>> symbols = client.symbol_lookup("reliance")
    >>> for symbol in symbols:
    ...     print(f"{symbol.company_name}: ₹{symbol.last_price}")
    >>> 
    >>> # Get news for a symbol
    >>> news = client.get_news(symbols[0].isin, page_size=5)
    >>> for story in news:
    ...     print(f"- {story.headline}")
    >>> 
    >>> # Get corporate actions
    >>> actions = client.get_corporate_actions(symbols[0].path)
    >>> for action in actions:
    ...     print(f"{action.purpose}: Ex-date {action.ex_date_parsed}")
"""

from .client import CogencisClient
from .core.exceptions import (
    CogencisError,
    CogencisAPIError,
    CogencisAuthError,
    CogencisConnectionError,
    CogencisRateLimitError,
    CogencisValidationError,
)
from .models.symbol import (
    SymbolData,
    SymbolLookupResponse,
    SearchOn,
)
from .models.auditor import (
    AuditorData,
    AuditorResponse,
)
from .models.news import (
    NewsStory,
    NewsResponse,
)
from .models.shareholder import (
    ShareholdingValue,
    KeyShareholder,
    KeyShareholderResponse,
)
from .models.block_deal import (
    BlockDeal,
    BlockDealResponse,
    BlockDealType,
    TransactionType,
)
from .models.insider_trading import (
    InsiderTrade,
    InsiderTradingResponse,
)
from .models.sast import (
    SASTTransaction,
    SASTResponse,
)
from .models.capital_history import (
    CapitalHistoryEntry,
    CapitalHistoryResponse,
)
from .models.announcement import (
    Announcement,
    AnnouncementResponse,
)
from .models.corporate_action import (
    CorporateAction,
    CorporateActionResponse,
)
from .models.tribunal import (
    TribunalCase,
    TribunalResponse,
)
from .models.common import (
    PagingInfo,
    ColumnDefinition,
)

__version__ = "0.3.0"

__all__ = [
    # Main client
    "CogencisClient",
    # Exceptions
    "CogencisError",
    "CogencisAPIError",
    "CogencisAuthError",
    "CogencisConnectionError",
    "CogencisRateLimitError",
    "CogencisValidationError",
    # Symbol models
    "SymbolData",
    "SymbolLookupResponse",
    "SearchOn",
    # Auditor models
    "AuditorData",
    "AuditorResponse",
    # News models
    "NewsStory",
    "NewsResponse",
    # Shareholder models
    "ShareholdingValue",
    "KeyShareholder",
    "KeyShareholderResponse",
    # Block deal models
    "BlockDeal",
    "BlockDealResponse",
    "BlockDealType",
    "TransactionType",
    # Insider trading models
    "InsiderTrade",
    "InsiderTradingResponse",
    # SAST models
    "SASTTransaction",
    "SASTResponse",
    # Capital history models
    "CapitalHistoryEntry",
    "CapitalHistoryResponse",
    # Announcement models
    "Announcement",
    "AnnouncementResponse",
    # Corporate action models
    "CorporateAction",
    "CorporateActionResponse",
    # Tribunal models
    "TribunalCase",
    "TribunalResponse",
    # Common models
    "PagingInfo",
    "ColumnDefinition",
]