"""HTTP client for NSE India API with browser-like headers and caching."""

from pathlib import Path
from typing import Any

import httpx

from .cache import (
    CacheConfig,
    CacheTTL,
    HybridCache,
    get_cache,
    get_endpoint_ttl,
    get_quote_api_ttl,
)
from .exceptions import (
    NSEIndiaAPIError,
    NSEIndiaConnectionError,
    NSEIndiaRateLimitError,
)


class NSEIndiaHTTPClient:
    """HTTP client for NSE India API.

    NSE India blocks requests without proper browser headers.
    This client mimics a real browser to access the API.

    Features:
    - Browser-like headers for NSE compatibility
    - Automatic session management with cookies
    - Built-in caching with configurable TTLs
    - Rate limit handling
    """

    BASE_URL = "https://www.nseindia.com"

    def __init__(
        self,
        timeout: float = 30.0,
        cache_config: CacheConfig | None = None,
        cache: HybridCache | None = None,
    ):
        """Initialize the HTTP client.

        Args:
            timeout: Request timeout in seconds
            cache_config: Cache configuration (defaults to enabled)
            cache: Optional custom cache instance (uses global hybrid cache if not provided)
        """
        self._client: httpx.Client | None = None
        self.timeout = timeout

        # Cache setup
        self._cache_config = cache_config or CacheConfig(enabled=True)
        self._cache = cache or get_cache()

    def _get_default_headers(self) -> dict[str, str]:
        """Get browser-like headers required by NSE India."""
        return {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "*/*",
            "Accept-Language": "en-US,en;q=0.9",
            "Connection": "keep-alive",
            "Cache-Control": "no-cache",
        }

    @property
    def client(self) -> httpx.Client:
        """Lazy initialization of HTTP client with session cookies."""
        if self._client is None:
            self._client = httpx.Client(
                base_url=self.BASE_URL,
                headers=self._get_default_headers(),
                timeout=self.timeout,
                follow_redirects=True,
            )
            # Visit the main page first to get session cookies
            self._init_session()
        return self._client

    def _init_session(self) -> None:
        """Initialize session by visiting the main page to get cookies."""
        try:
            # Visit main page to establish session
            self._client.get("/")
        except httpx.HTTPError:
            # Continue even if this fails - some endpoints might still work
            pass

    def _handle_response(self, response: httpx.Response) -> httpx.Response:
        """Handle HTTP response and raise appropriate exceptions."""
        if response.status_code == 429:
            retry_after = response.headers.get("Retry-After")
            raise NSEIndiaRateLimitError(
                message="Rate limit exceeded by NSE India",
                retry_after=int(retry_after) if retry_after else None,
            )

        if response.status_code >= 400:
            raise NSEIndiaAPIError(
                message=f"NSE India API error: {response.status_code}",
                status_code=response.status_code,
                response_body=response.text[:1000] if response.text else None,
            )

        return response

    def get(
        self,
        endpoint: str,
        params: dict | None = None,
        skip_cache: bool = False,
    ) -> httpx.Response:
        """Make a GET request to NSE India API.

        Args:
            endpoint: API endpoint path (e.g., "/api/corporate-announcements")
            params: Query parameters
            skip_cache: If True, bypass cache (used for fresh data)

        Returns:
            httpx.Response object
        """
        try:
            response = self.client.get(endpoint, params=params)
            return self._handle_response(response)
        except httpx.ConnectError as e:
            raise NSEIndiaConnectionError(f"Failed to connect to NSE India: {e}") from e
        except httpx.TimeoutException as e:
            raise NSEIndiaConnectionError(f"Request to NSE India timed out: {e}") from e

    def get_csv(
        self,
        endpoint: str,
        params: dict | None = None,
        skip_cache: bool = False,
        ttl: CacheTTL | int | None = None,
    ) -> str:
        """Fetch CSV data from NSE India API with caching.

        Args:
            endpoint: API endpoint path
            params: Query parameters
            skip_cache: If True, bypass cache
            ttl: Optional override for cache TTL

        Returns:
            Raw CSV content as string
        """
        cache_key_params = params.copy() if params else {}
        cache_key_params["_format"] = "csv"  # Distinguish from JSON

        # Check cache first
        if self._cache_config.enabled and not skip_cache:
            cached_value, found = self._cache.get(endpoint, cache_key_params)
            if found:
                return cached_value

        # Fetch from API
        response = self.get(endpoint, params=params)
        result = response.text

        # Cache the result
        if self._cache_config.enabled:
            effective_ttl = ttl if ttl is not None else get_endpoint_ttl(endpoint)
            self._cache.set(endpoint, cache_key_params, result, effective_ttl)

        return result

    def get_json(
        self,
        endpoint: str,
        params: dict | None = None,
        skip_cache: bool = False,
        ttl: CacheTTL | int | None = None,
    ) -> dict | list | Any:
        """Fetch JSON data from NSE India API with caching.

        Args:
            endpoint: API endpoint path
            params: Query parameters
            skip_cache: If True, bypass cache
            ttl: Optional override for cache TTL

        Returns:
            Parsed JSON as dict/list
        """
        # Check cache first
        if self._cache_config.enabled and not skip_cache:
            cached_value, found = self._cache.get(endpoint, params)
            if found:
                return cached_value

        # Fetch from API
        response = self.get(endpoint, params=params)
        result = response.json()

        # Cache the result
        if self._cache_config.enabled:
            # Determine TTL
            if ttl is not None:
                effective_ttl = ttl
            elif "/api/NextApi/apiClient/GetQuoteApi" in endpoint and params:
                # Quote API - use function-specific TTL
                function_name = params.get("functionName", "")
                effective_ttl = get_quote_api_ttl(function_name)
            else:
                effective_ttl = get_endpoint_ttl(endpoint)

            self._cache.set(endpoint, params, result, effective_ttl)

        return result

    def post_json(
        self,
        url: str,
        payload: dict,
        skip_cache: bool = False,
        ttl: CacheTTL | int | None = None,
    ) -> dict | list | Any:
        """Make a POST request with JSON payload and caching.

        Args:
            url: Full URL to POST to
            payload: JSON payload to send
            skip_cache: If True, bypass cache
            ttl: Optional override for cache TTL

        Returns:
            Parsed JSON response as dict/list
        """
        import json

        # Create cache key from URL and payload
        cache_key = f"POST:{url}"
        cache_params = {"_payload_hash": hash(json.dumps(payload, sort_keys=True))}

        # Check cache first
        if self._cache_config.enabled and not skip_cache:
            cached_value, found = self._cache.get(cache_key, cache_params)
            if found:
                return cached_value

        # Make POST request
        try:
            # Create a client for external URLs (charting API uses different domain)
            with httpx.Client(
                headers={
                    **self._get_default_headers(),
                    "Content-Type": "application/json",
                },
                timeout=self.timeout,
                follow_redirects=True,
            ) as post_client:
                response = post_client.post(url, json=payload)
                self._handle_response(response)
                result = response.json()

        except httpx.ConnectError as e:
            raise NSEIndiaConnectionError(f"Failed to connect: {e}") from e
        except httpx.TimeoutException as e:
            raise NSEIndiaConnectionError(f"Request timed out: {e}") from e

        # Cache the result
        if self._cache_config.enabled:
            effective_ttl = ttl if ttl is not None else CacheTTL.INTRADAY
            self._cache.set(cache_key, cache_params, result, effective_ttl)

        return result

    def download_file(self, url: str, save_path: Path) -> Path:
        """Download a file (e.g., PDF attachment) from NSE India.

        Note: File downloads are NOT cached.

        Args:
            url: Full URL to download
            save_path: Local path to save the file

        Returns:
            Path to the saved file
        """
        # Create a separate client for external URLs
        try:
            with httpx.Client(
                headers=self._get_default_headers(),
                timeout=self.timeout,
                follow_redirects=True,
            ) as download_client:
                response = download_client.get(url)
                self._handle_response(response)

                # Ensure parent directory exists
                save_path.parent.mkdir(parents=True, exist_ok=True)

                # Write content to file
                save_path.write_bytes(response.content)
                return save_path

        except httpx.ConnectError as e:
            raise NSEIndiaConnectionError(f"Failed to download file: {e}") from e
        except httpx.TimeoutException as e:
            raise NSEIndiaConnectionError(f"Download timed out: {e}") from e

    def invalidate_cache(self, endpoint: str, params: dict | None = None) -> bool:
        """Invalidate a specific cache entry.

        Args:
            endpoint: API endpoint
            params: Query parameters

        Returns:
            True if entry was invalidated
        """
        return self._cache.delete(endpoint, params)

    def clear_cache(self) -> None:
        """Clear all cached data."""
        self._cache.clear()

    @property
    def cache_stats(self) -> dict[str, Any]:
        """Get cache statistics."""
        return self._cache.stats

    @property
    def cache_enabled(self) -> bool:
        """Check if caching is enabled."""
        return self._cache_config.enabled

    def disable_cache(self) -> None:
        """Disable caching."""
        self._cache_config.enabled = False

    def enable_cache(self) -> None:
        """Enable caching."""
        self._cache_config.enabled = True

    def close(self) -> None:
        """Close the HTTP client."""
        if self._client is not None:
            self._client.close()
            self._client = None

    def __enter__(self) -> "NSEIndiaHTTPClient":
        return self

    def __exit__(self, *args) -> None:
        self.close()
