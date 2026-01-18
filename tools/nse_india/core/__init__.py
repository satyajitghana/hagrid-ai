"""Core utilities for NSE India API client."""

from .cache import (
    DEFAULT_CACHE_DIR,
    CacheConfig,
    CacheTTL,
    FileCache,
    HybridCache,
    MemoryCache,
    clear_cache,
    get_cache,
    get_endpoint_ttl,
    get_quote_api_ttl,
    set_cache_dir,
)
from .exceptions import (
    NSEIndiaAPIError,
    NSEIndiaConnectionError,
    NSEIndiaError,
    NSEIndiaParseError,
    NSEIndiaRateLimitError,
)
from .http_client import NSEIndiaHTTPClient

__all__ = [
    # HTTP Client
    "NSEIndiaHTTPClient",
    # Cache
    "DEFAULT_CACHE_DIR",
    "CacheConfig",
    "CacheTTL",
    "FileCache",
    "HybridCache",
    "MemoryCache",
    "get_cache",
    "clear_cache",
    "set_cache_dir",
    "get_endpoint_ttl",
    "get_quote_api_ttl",
    # Exceptions
    "NSEIndiaError",
    "NSEIndiaAPIError",
    "NSEIndiaRateLimitError",
    "NSEIndiaConnectionError",
    "NSEIndiaParseError",
]
