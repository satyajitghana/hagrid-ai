"""HTTP client for TradingView API."""

import logging
from typing import Any
from urllib.parse import urlencode

import httpx

from .exceptions import (
    TradingViewAPIError,
    TradingViewConnectionError,
    TradingViewRateLimitError,
)

logger = logging.getLogger(__name__)


class TradingViewHTTPClient:
    """HTTP client for making requests to TradingView APIs."""

    # TradingView uses multiple API endpoints
    SYMBOL_SEARCH_URL = "https://symbol-search.tradingview.com"
    NEWS_URL = "https://news-mediator.tradingview.com"
    SCANNER_URL = "https://scanner.tradingview.com"
    LOGO_URL = "https://s3-symbol-logo.tradingview.com"
    
    DEFAULT_TIMEOUT = 30.0

    def __init__(
        self,
        timeout: float = DEFAULT_TIMEOUT,
    ) -> None:
        """
        Initialize the TradingView HTTP client.

        Args:
            timeout: Request timeout in seconds
        """
        self.timeout = timeout
        self._client: httpx.Client | None = None

    @property
    def client(self) -> httpx.Client:
        """Get or create the HTTP client instance."""
        if self._client is None:
            self._client = httpx.Client(
                timeout=self.timeout,
                headers=self._get_default_headers(),
            )
        return self._client

    def _get_default_headers(self) -> dict[str, str]:
        """Get default headers for API requests."""
        return {
            "Accept": "application/json",
            "Accept-Language": "en-US,en;q=0.9",
            "Cache-Control": "no-cache",
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
        }

    def _handle_response(self, response: httpx.Response) -> dict[str, Any] | list[Any]:
        """
        Handle API response and raise appropriate exceptions.

        Args:
            response: The HTTP response object

        Returns:
            Parsed JSON response

        Raises:
            TradingViewRateLimitError: If rate limit is exceeded
            TradingViewAPIError: For other API errors
        """
        if response.status_code == 429:
            retry_after = response.headers.get("Retry-After")
            raise TradingViewRateLimitError(
                "Rate limit exceeded",
                retry_after=int(retry_after) if retry_after else None,
            )

        if response.status_code >= 400:
            raise TradingViewAPIError(
                f"API request failed",
                status_code=response.status_code,
                response_body=response.text,
            )

        try:
            return response.json()
        except Exception as e:
            raise TradingViewAPIError(
                f"Failed to parse JSON response: {e}",
                status_code=response.status_code,
                response_body=response.text,
            )

    def _build_url(self, base_url: str, endpoint: str, params: dict[str, Any] | None = None) -> str:
        """Build full URL with query parameters."""
        url = f"{base_url}{endpoint}"
        if params:
            filtered_params = {
                k: str(v) for k, v in params.items() if v is not None
            }
            if filtered_params:
                url = f"{url}?{urlencode(filtered_params)}"
        return url

    def get(
        self,
        base_url: str,
        endpoint: str,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any] | list[Any]:
        """
        Make a GET request to the API.

        Args:
            base_url: Base URL for the API
            endpoint: API endpoint (without base URL)
            params: Query parameters

        Returns:
            Parsed JSON response

        Raises:
            TradingViewConnectionError: If connection fails
            TradingViewAPIError: If API returns an error
        """
        try:
            url = self._build_url(base_url, endpoint, params)
            logger.debug(f"GET {url}")
            response = self.client.get(url)
            return self._handle_response(response)

        except httpx.ConnectError as e:
            raise TradingViewConnectionError(
                f"Failed to connect to TradingView API: {e}"
            ) from e
        except httpx.TimeoutException as e:
            raise TradingViewConnectionError(
                f"Request to TradingView API timed out: {e}"
            ) from e

    # Convenience methods for each TradingView service
    
    def symbol_search(
        self,
        endpoint: str,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any] | list[Any]:
        """Make a request to the symbol search API."""
        return self.get(self.SYMBOL_SEARCH_URL, endpoint, params)

    def news(
        self,
        endpoint: str,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any] | list[Any]:
        """Make a request to the news API."""
        return self.get(self.NEWS_URL, endpoint, params)

    def scanner(
        self,
        endpoint: str,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any] | list[Any]:
        """Make a request to the scanner API."""
        return self.get(self.SCANNER_URL, endpoint, params)

    def get_logo_url(self, logoid: str, extension: str = "svg") -> str:
        """
        Get the URL for a symbol's logo.
        
        Args:
            logoid: Logo ID from symbol data
            extension: File extension (svg, png)
            
        Returns:
            Full URL to the logo image
        """
        return f"{self.LOGO_URL}/{logoid}.{extension}"

    def close(self) -> None:
        """Close the HTTP client."""
        if self._client is not None:
            self._client.close()
            self._client = None

    def __enter__(self) -> "TradingViewHTTPClient":
        """Context manager entry."""
        return self

    def __exit__(self, *args: Any) -> None:
        """Context manager exit."""
        self.close()