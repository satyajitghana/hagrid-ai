"""Caching infrastructure for NSE India API client.

Cache TTL Categories:
- NO_CACHE (0s): Real-time data that changes every second
- VERY_SHORT (30s): Live quotes, prices during market hours
- SHORT (2min): Live analysis data (OI spurts, most active, gainers/losers)
- MEDIUM (5min): Bulk/block deals, market breadth
- LONG (15min): Announcements, corporate events
- DAILY (24h): Data that changes once per day (after market close)
- WEEKLY (7d): Quarterly data (shareholding, financials)
- STATIC (30d): Metadata, company info, annual reports

Storage:
- Memory cache: Fast access for current session
- File cache: Persistent storage in .cache/nse_india/ for cross-session caching
"""

import hashlib
import json
import logging
import time
from dataclasses import dataclass, field
from enum import IntEnum
from pathlib import Path
from threading import Lock
from typing import Any

logger = logging.getLogger(__name__)

# Default cache directory
DEFAULT_CACHE_DIR = Path(".cache/nse_india")


class CacheTTL(IntEnum):
    """Cache TTL values in seconds."""

    NO_CACHE = 0
    VERY_SHORT = 30  # 30 seconds - live quotes
    SHORT = 120  # 2 minutes - live analysis
    MEDIUM = 300  # 5 minutes - deals, breadth
    LONG = 900  # 15 minutes - announcements
    DAILY = 86400  # 24 hours - end of day data
    WEEKLY = 604800  # 7 days - quarterly data
    STATIC = 2592000  # 30 days - metadata, rarely changes


@dataclass
class CacheEntry:
    """A single cache entry with value and expiration."""

    value: Any
    expires_at: float
    created_at: float = field(default_factory=time.time)

    @property
    def is_expired(self) -> bool:
        """Check if the entry has expired."""
        return time.time() > self.expires_at

    @property
    def ttl_remaining(self) -> float:
        """Get remaining TTL in seconds."""
        return max(0, self.expires_at - time.time())

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "value": self.value,
            "expires_at": self.expires_at,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "CacheEntry":
        """Create from dictionary."""
        return cls(
            value=data["value"],
            expires_at=data["expires_at"],
            created_at=data.get("created_at", time.time()),
        )


class MemoryCache:
    """Thread-safe in-memory cache with TTL support.

    Features:
    - Per-key TTL
    - Thread-safe operations
    - Automatic cleanup of expired entries
    - Cache statistics
    """

    def __init__(self, cleanup_interval: int = 300):
        """Initialize the cache.

        Args:
            cleanup_interval: Interval in seconds between automatic cleanups
        """
        self._cache: dict[str, CacheEntry] = {}
        self._lock = Lock()
        self._cleanup_interval = cleanup_interval
        self._last_cleanup = time.time()

        # Statistics
        self._hits = 0
        self._misses = 0

    def _generate_key(self, endpoint: str, params: dict | None = None) -> str:
        """Generate a cache key from endpoint and parameters.

        Args:
            endpoint: API endpoint
            params: Query parameters

        Returns:
            A unique cache key string
        """
        key_parts = [endpoint]
        if params:
            # Sort params for consistent key generation
            sorted_params = sorted(params.items())
            params_str = json.dumps(sorted_params, sort_keys=True)
            key_parts.append(params_str)

        key_string = "|".join(key_parts)
        return hashlib.sha256(key_string.encode()).hexdigest()[:32]

    def _maybe_cleanup(self) -> None:
        """Run cleanup if enough time has passed."""
        now = time.time()
        if now - self._last_cleanup > self._cleanup_interval:
            self._cleanup_expired()
            self._last_cleanup = now

    def _cleanup_expired(self) -> None:
        """Remove all expired entries."""
        with self._lock:
            expired_keys = [
                key for key, entry in self._cache.items() if entry.is_expired
            ]
            for key in expired_keys:
                del self._cache[key]

    def get(self, endpoint: str, params: dict | None = None) -> tuple[Any, bool]:
        """Get a value from cache.

        Args:
            endpoint: API endpoint
            params: Query parameters

        Returns:
            Tuple of (value, found) where found is True if cache hit
        """
        self._maybe_cleanup()

        key = self._generate_key(endpoint, params)

        with self._lock:
            entry = self._cache.get(key)

            if entry is None:
                self._misses += 1
                return None, False

            if entry.is_expired:
                del self._cache[key]
                self._misses += 1
                return None, False

            self._hits += 1
            return entry.value, True

    def set(
        self,
        endpoint: str,
        params: dict | None,
        value: Any,
        ttl: int | CacheTTL,
    ) -> None:
        """Set a value in cache.

        Args:
            endpoint: API endpoint
            params: Query parameters
            value: Value to cache
            ttl: Time-to-live in seconds
        """
        if ttl == 0 or ttl == CacheTTL.NO_CACHE:
            return  # Don't cache if TTL is 0

        key = self._generate_key(endpoint, params)
        expires_at = time.time() + int(ttl)

        with self._lock:
            self._cache[key] = CacheEntry(value=value, expires_at=expires_at)

    def delete(self, endpoint: str, params: dict | None = None) -> bool:
        """Delete a specific cache entry.

        Args:
            endpoint: API endpoint
            params: Query parameters

        Returns:
            True if entry was deleted, False if not found
        """
        key = self._generate_key(endpoint, params)

        with self._lock:
            if key in self._cache:
                del self._cache[key]
                return True
            return False

    def clear(self) -> None:
        """Clear all cache entries."""
        with self._lock:
            self._cache.clear()
            self._hits = 0
            self._misses = 0

    def clear_pattern(self, endpoint_prefix: str) -> int:
        """Clear all entries matching an endpoint prefix.

        Args:
            endpoint_prefix: Endpoint prefix to match (e.g., "/api/live-analysis")

        Returns:
            Number of entries cleared
        """
        # Since we hash keys, we need to track original endpoints
        # This is a simplified version - for production, maintain a reverse index
        cleared = 0
        with self._lock:
            # Clear all - this is the safe approach when pattern matching isn't feasible
            if endpoint_prefix == "/api/":
                cleared = len(self._cache)
                self._cache.clear()
        return cleared

    @property
    def stats(self) -> dict[str, Any]:
        """Get cache statistics."""
        with self._lock:
            total_requests = self._hits + self._misses
            hit_rate = (self._hits / total_requests * 100) if total_requests > 0 else 0

            return {
                "entries": len(self._cache),
                "hits": self._hits,
                "misses": self._misses,
                "hit_rate_percent": round(hit_rate, 2),
            }

    @property
    def size(self) -> int:
        """Get current cache size (number of entries)."""
        with self._lock:
            return len(self._cache)


class FileCache:
    """File-based persistent cache with TTL support.

    Stores cache entries as JSON files in a directory structure.
    This allows cache to survive process restarts.

    Features:
    - Persistent storage across restarts
    - Per-key TTL with automatic expiration
    - Thread-safe file operations
    - Automatic cleanup of expired entries
    """

    def __init__(
        self,
        cache_dir: Path | str = DEFAULT_CACHE_DIR,
        cleanup_interval: int = 3600,
    ):
        """Initialize the file cache.

        Args:
            cache_dir: Directory to store cache files
            cleanup_interval: Interval in seconds between automatic cleanups
        """
        self._cache_dir = Path(cache_dir)
        self._lock = Lock()
        self._cleanup_interval = cleanup_interval
        self._last_cleanup = time.time()

        # Statistics
        self._hits = 0
        self._misses = 0

        # Ensure cache directory exists
        self._ensure_cache_dir()

    def _ensure_cache_dir(self) -> None:
        """Ensure the cache directory exists."""
        try:
            self._cache_dir.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            logger.warning(f"Could not create cache directory {self._cache_dir}: {e}")

    def _generate_key(self, endpoint: str, params: dict | None = None) -> str:
        """Generate a cache key from endpoint and parameters."""
        key_parts = [endpoint]
        if params:
            sorted_params = sorted(params.items())
            params_str = json.dumps(sorted_params, sort_keys=True)
            key_parts.append(params_str)

        key_string = "|".join(key_parts)
        return hashlib.sha256(key_string.encode()).hexdigest()[:32]

    def _get_cache_path(self, key: str) -> Path:
        """Get the file path for a cache key.

        Uses subdirectories based on first 2 chars of key for better filesystem performance.
        """
        subdir = key[:2]
        return self._cache_dir / subdir / f"{key}.json"

    def _maybe_cleanup(self) -> None:
        """Run cleanup if enough time has passed."""
        now = time.time()
        if now - self._last_cleanup > self._cleanup_interval:
            self._cleanup_expired()
            self._last_cleanup = now

    def _cleanup_expired(self) -> None:
        """Remove all expired cache files."""
        if not self._cache_dir.exists():
            return

        try:
            for subdir in self._cache_dir.iterdir():
                if not subdir.is_dir():
                    continue
                for cache_file in subdir.glob("*.json"):
                    try:
                        data = json.loads(cache_file.read_text())
                        if time.time() > data.get("expires_at", 0):
                            cache_file.unlink()
                    except (json.JSONDecodeError, OSError):
                        # Remove corrupted files
                        try:
                            cache_file.unlink()
                        except OSError:
                            pass
        except OSError as e:
            logger.warning(f"Error during cache cleanup: {e}")

    def get(self, endpoint: str, params: dict | None = None) -> tuple[Any, bool]:
        """Get a value from cache.

        Args:
            endpoint: API endpoint
            params: Query parameters

        Returns:
            Tuple of (value, found) where found is True if cache hit
        """
        self._maybe_cleanup()

        key = self._generate_key(endpoint, params)
        cache_path = self._get_cache_path(key)

        with self._lock:
            if not cache_path.exists():
                self._misses += 1
                return None, False

            try:
                data = json.loads(cache_path.read_text())
                entry = CacheEntry.from_dict(data)

                if entry.is_expired:
                    # Remove expired file
                    try:
                        cache_path.unlink()
                    except OSError:
                        pass
                    self._misses += 1
                    return None, False

                self._hits += 1
                return entry.value, True

            except (json.JSONDecodeError, OSError, KeyError) as e:
                logger.debug(f"Cache read error for {key}: {e}")
                self._misses += 1
                return None, False

    def set(
        self,
        endpoint: str,
        params: dict | None,
        value: Any,
        ttl: int | CacheTTL,
    ) -> None:
        """Set a value in cache.

        Args:
            endpoint: API endpoint
            params: Query parameters
            value: Value to cache
            ttl: Time-to-live in seconds
        """
        if ttl == 0 or ttl == CacheTTL.NO_CACHE:
            return

        key = self._generate_key(endpoint, params)
        cache_path = self._get_cache_path(key)
        expires_at = time.time() + int(ttl)

        entry = CacheEntry(value=value, expires_at=expires_at)

        with self._lock:
            try:
                # Ensure subdirectory exists
                cache_path.parent.mkdir(parents=True, exist_ok=True)
                cache_path.write_text(json.dumps(entry.to_dict()))
            except (OSError, TypeError) as e:
                logger.debug(f"Cache write error for {key}: {e}")

    def delete(self, endpoint: str, params: dict | None = None) -> bool:
        """Delete a specific cache entry."""
        key = self._generate_key(endpoint, params)
        cache_path = self._get_cache_path(key)

        with self._lock:
            if cache_path.exists():
                try:
                    cache_path.unlink()
                    return True
                except OSError:
                    return False
            return False

    def clear(self) -> None:
        """Clear all cache entries."""
        with self._lock:
            if self._cache_dir.exists():
                try:
                    import shutil

                    for subdir in self._cache_dir.iterdir():
                        if subdir.is_dir():
                            shutil.rmtree(subdir)
                except OSError as e:
                    logger.warning(f"Error clearing cache: {e}")

            self._hits = 0
            self._misses = 0

    @property
    def stats(self) -> dict[str, Any]:
        """Get cache statistics."""
        total_requests = self._hits + self._misses
        hit_rate = (self._hits / total_requests * 100) if total_requests > 0 else 0

        # Count files
        file_count = 0
        if self._cache_dir.exists():
            for subdir in self._cache_dir.iterdir():
                if subdir.is_dir():
                    file_count += len(list(subdir.glob("*.json")))

        return {
            "entries": file_count,
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate_percent": round(hit_rate, 2),
            "cache_dir": str(self._cache_dir),
        }

    @property
    def size(self) -> int:
        """Get current cache size (number of entries)."""
        if not self._cache_dir.exists():
            return 0

        count = 0
        for subdir in self._cache_dir.iterdir():
            if subdir.is_dir():
                count += len(list(subdir.glob("*.json")))
        return count


class HybridCache:
    """Hybrid cache combining memory and file-based storage.

    Uses memory cache for fast access and file cache for persistence.
    On read:
        1. Check memory cache first
        2. If miss, check file cache
        3. If found in file, populate memory cache
    On write:
        1. Write to both memory and file cache
    """

    def __init__(
        self,
        cache_dir: Path | str = DEFAULT_CACHE_DIR,
        memory_cleanup_interval: int = 300,
        file_cleanup_interval: int = 3600,
    ):
        """Initialize hybrid cache.

        Args:
            cache_dir: Directory for file cache
            memory_cleanup_interval: Cleanup interval for memory cache
            file_cleanup_interval: Cleanup interval for file cache
        """
        self._memory = MemoryCache(cleanup_interval=memory_cleanup_interval)
        self._file = FileCache(
            cache_dir=cache_dir, cleanup_interval=file_cleanup_interval
        )

    def get(self, endpoint: str, params: dict | None = None) -> tuple[Any, bool]:
        """Get a value from cache (memory first, then file)."""
        # Try memory cache first
        value, found = self._memory.get(endpoint, params)
        if found:
            return value, True

        # Try file cache
        value, found = self._file.get(endpoint, params)
        if found:
            # Populate memory cache from file
            # Use a short TTL for memory since we don't know original TTL
            # The file cache entry will be authoritative
            self._memory.set(endpoint, params, value, CacheTTL.MEDIUM)
            return value, True

        return None, False

    def set(
        self,
        endpoint: str,
        params: dict | None,
        value: Any,
        ttl: int | CacheTTL,
    ) -> None:
        """Set a value in both memory and file cache."""
        self._memory.set(endpoint, params, value, ttl)
        self._file.set(endpoint, params, value, ttl)

    def delete(self, endpoint: str, params: dict | None = None) -> bool:
        """Delete from both caches."""
        memory_deleted = self._memory.delete(endpoint, params)
        file_deleted = self._file.delete(endpoint, params)
        return memory_deleted or file_deleted

    def clear(self) -> None:
        """Clear both caches."""
        self._memory.clear()
        self._file.clear()

    @property
    def stats(self) -> dict[str, Any]:
        """Get combined cache statistics."""
        memory_stats = self._memory.stats
        file_stats = self._file.stats

        return {
            "memory": memory_stats,
            "file": file_stats,
            "total_hits": memory_stats["hits"] + file_stats["hits"],
            "total_misses": max(memory_stats["misses"], file_stats["misses"]),
        }

    @property
    def size(self) -> int:
        """Get file cache size (memory is transient)."""
        return self._file.size


# Endpoint to TTL mapping
# This defines the appropriate cache duration for each API endpoint
ENDPOINT_TTL_MAP: dict[str, CacheTTL] = {
    # === NO CACHE - Real-time live data ===
    # These change every second during market hours
    "/api/allIndices": CacheTTL.VERY_SHORT,  # Index prices (30s acceptable)
    "/api/live-analysis-stocksTraded": CacheTTL.VERY_SHORT,
    "/api/live-analysis-oi-spurts-underlyings": CacheTTL.SHORT,
    "/api/live-analysis-most-active-securities": CacheTTL.SHORT,
    "/api/live-analysis-most-active-sme": CacheTTL.SHORT,
    "/api/live-analysis-most-active-etf": CacheTTL.SHORT,
    "/api/live-analysis-variations": CacheTTL.SHORT,
    "/api/live-analysis-volume-gainers": CacheTTL.SHORT,
    "/api/live-analysis-advance": CacheTTL.SHORT,
    "/api/live-analysis-decline": CacheTTL.SHORT,
    "/api/live-analysis-price-band-hitter": CacheTTL.SHORT,
    "/api/market-data-pre-open": CacheTTL.VERY_SHORT,  # Pre-open changes rapidly
    "/api/option-chain-v3": CacheTTL.SHORT,  # OI/prices change
    # === MEDIUM CACHE - Updates periodically ===
    "/api/snapshot-capital-market-largedeal": CacheTTL.MEDIUM,  # Deals update periodically
    "/api/corporate-announcements": CacheTTL.LONG,  # New announcements come through
    # === LONG CACHE - Changes infrequently ===
    "/api/event-calendar": CacheTTL.LONG,
    "/api/corporate-insider-plan": CacheTTL.LONG,
    "/api/corporates-pit": CacheTTL.LONG,  # Insider transactions
    "/api/option-chain-contract-info": CacheTTL.DAILY,  # Expiry dates change on expiry
    # === WEEKLY CACHE - Quarterly data ===
    "/api/corporates-financial-results": CacheTTL.WEEKLY,
    "/api/results-comparision": CacheTTL.WEEKLY,
    "/api/corporate-share-holdings-master": CacheTTL.WEEKLY,
    "/api/corporate-share-holdings-equities": CacheTTL.WEEKLY,
    # === STATIC CACHE - Rarely changes ===
    "/api/annual-reports": CacheTTL.STATIC,
}

# Quote API function TTL mapping
QUOTE_API_TTL_MAP: dict[str, CacheTTL] = {
    # === STATIC - Almost never changes ===
    "getSymbolName": CacheTTL.STATIC,  # Company name
    "getMetaData": CacheTTL.STATIC,  # ISIN, sector, industry
    "getIndexList": CacheTTL.STATIC,  # Index membership
    # === WEEKLY - Quarterly data ===
    "getShareholdingPattern": CacheTTL.WEEKLY,
    "getFinancialStatus": CacheTTL.WEEKLY,
    "getFinancialResultData": CacheTTL.WEEKLY,
    "getYearwiseData": CacheTTL.WEEKLY,
    "getIntegratedFilingData": CacheTTL.WEEKLY,
    # === DAILY - Changes once per day ===
    "getCorpAnnualReport": CacheTTL.DAILY,
    "getCorpBrsr": CacheTTL.DAILY,
    "getCorpAction": CacheTTL.DAILY,  # Corporate actions
    "getCorpBoardMeeting": CacheTTL.DAILY,
    # === LONG - Updates periodically ===
    "getCorporateAnnouncement": CacheTTL.LONG,
    # === SHORT - Live data ===
    "getSymbolData": CacheTTL.VERY_SHORT,  # Live price data
    "getDerivativesMostActive": CacheTTL.SHORT,
    "getSymbolDerivativesData": CacheTTL.SHORT,
    "getSymbolDerivativesFilter": CacheTTL.MEDIUM,  # Expiry dates
    "getOptionChainDropdown": CacheTTL.MEDIUM,
    "getOptionChainData": CacheTTL.SHORT,
}


def get_endpoint_ttl(endpoint: str) -> CacheTTL:
    """Get the appropriate TTL for an endpoint.

    Args:
        endpoint: API endpoint path

    Returns:
        CacheTTL value for the endpoint
    """
    # Check exact match first
    if endpoint in ENDPOINT_TTL_MAP:
        return ENDPOINT_TTL_MAP[endpoint]

    # Check if it's a Quote API call
    if "/api/NextApi/apiClient/GetQuoteApi" in endpoint:
        return CacheTTL.SHORT  # Default for quote API

    # Default TTL for unknown endpoints
    return CacheTTL.MEDIUM


def get_quote_api_ttl(function_name: str) -> CacheTTL:
    """Get the appropriate TTL for a Quote API function.

    Args:
        function_name: Quote API function name

    Returns:
        CacheTTL value for the function
    """
    return QUOTE_API_TTL_MAP.get(function_name, CacheTTL.MEDIUM)


class CacheConfig:
    """Configuration for caching behavior."""

    def __init__(
        self,
        enabled: bool = True,
        default_ttl: CacheTTL = CacheTTL.MEDIUM,
        max_entries: int = 10000,
        cleanup_interval: int = 300,
        cache_dir: Path | str = DEFAULT_CACHE_DIR,
    ):
        """Initialize cache configuration.

        Args:
            enabled: Whether caching is enabled
            default_ttl: Default TTL for endpoints not in the map
            max_entries: Maximum number of cache entries (not enforced currently)
            cleanup_interval: Interval between automatic cleanups in seconds
            cache_dir: Directory for file-based cache storage
        """
        self.enabled = enabled
        self.default_ttl = default_ttl
        self.max_entries = max_entries
        self.cleanup_interval = cleanup_interval
        self.cache_dir = Path(cache_dir)


# Global cache instance
_cache_instance: HybridCache | None = None
_cache_dir: Path = DEFAULT_CACHE_DIR


def get_cache(cache_dir: Path | str | None = None) -> HybridCache:
    """Get the global cache instance (singleton).

    Args:
        cache_dir: Optional custom cache directory. Only used on first call.

    Returns:
        The global HybridCache instance
    """
    global _cache_instance, _cache_dir
    if _cache_instance is None:
        if cache_dir is not None:
            _cache_dir = Path(cache_dir)
        _cache_instance = HybridCache(cache_dir=_cache_dir)
    return _cache_instance


def clear_cache() -> None:
    """Clear the global cache (both memory and file)."""
    global _cache_instance
    if _cache_instance is not None:
        _cache_instance.clear()


def set_cache_dir(cache_dir: Path | str) -> None:
    """Set the cache directory for new cache instances.

    Note: This only affects future cache instances, not existing ones.
    Call clear_cache() and re-initialize if needed.

    Args:
        cache_dir: Directory for file-based cache storage
    """
    global _cache_dir
    _cache_dir = Path(cache_dir)
