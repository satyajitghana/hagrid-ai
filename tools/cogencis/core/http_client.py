"""HTTP client for Cogencis API."""

import logging
from typing import Any
from urllib.parse import urlencode

import httpx

from .exceptions import (
    CogencisAPIError,
    CogencisAuthError,
    CogencisConnectionError,
    CogencisRateLimitError,
)

logger = logging.getLogger(__name__)


class CogencisHTTPClient:
    """HTTP client for making requests to Cogencis API."""

    BASE_URL = "https://data.cogencis.com/api/v1"
    DEFAULT_TIMEOUT = 30.0

    def __init__(
        self,
        bearer_token: str,
        base_url: str | None = None,
        timeout: float = DEFAULT_TIMEOUT,
    ) -> None:
        """
        Initialize the Cogencis HTTP client.

        Args:
            bearer_token: JWT bearer token for authentication
            base_url: Optional custom base URL for the API
            timeout: Request timeout in seconds
        """
        self.base_url = base_url or self.BASE_URL
        self.bearer_token = bearer_token
        self.timeout = timeout
        self._client: httpx.Client | None = None

    @property
    def client(self) -> httpx.Client:
        """Get or create the HTTP client instance."""
        if self._client is None:
            self._client = httpx.Client(
                base_url=self.base_url,
                timeout=self.timeout,
                headers=self._get_default_headers(),
            )
        return self._client

    def _get_default_headers(self) -> dict[str, str]:
        """Get default headers for API requests (browser-like headers for CORS compatibility)."""
        return {
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "en-GB,en;q=0.9,en-US;q=0.8",
            "Authorization": f"Bearer {self.bearer_token}",
            "Cache-Control": "no-cache",
            "DNT": "1",
            "Origin": "https://iinvest.cogencis.com",
            "Pragma": "no-cache",
            "Priority": "u=1, i",
            "Sec-CH-UA": '"Chromium";v="142", "Google Chrome";v="142", "Not_A Brand";v="99"',
            "Sec-CH-UA-Mobile": "?0",
            "Sec-CH-UA-Platform": '"macOS"',
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-site",
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36",
        }

    def _handle_response(self, response: httpx.Response) -> dict[str, Any]:
        """
        Handle API response and raise appropriate exceptions.

        Args:
            response: The HTTP response object

        Returns:
            Parsed JSON response

        Raises:
            CogencisAuthError: If authentication fails
            CogencisRateLimitError: If rate limit is exceeded
            CogencisAPIError: For other API errors
        """
        if response.status_code == 401:
            raise CogencisAuthError(
                "Authentication failed. Token may be invalid or expired.",
                details=response.text,
            )

        if response.status_code == 429:
            retry_after = response.headers.get("Retry-After")
            raise CogencisRateLimitError(
                "Rate limit exceeded",
                retry_after=int(retry_after) if retry_after else None,
            )

        if response.status_code >= 400:
            raise CogencisAPIError(
                f"API request failed",
                status_code=response.status_code,
                response_body=response.text,
            )

        try:
            data = response.json()
        except Exception as e:
            raise CogencisAPIError(
                f"Failed to parse JSON response: {e}",
                status_code=response.status_code,
                response_body=response.text,
            )

        # Check for API-level errors in response
        if isinstance(data, dict) and data.get("status") is False:
            raise CogencisAPIError(
                data.get("message", "API returned error status"),
                status_code=response.status_code,
                response_body=data,
            )

        return data

    def get(
        self,
        endpoint: str,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Make a GET request to the API.

        Args:
            endpoint: API endpoint (without base URL)
            params: Query parameters

        Returns:
            Parsed JSON response

        Raises:
            CogencisConnectionError: If connection fails
            CogencisAPIError: If API returns an error
        """
        try:
            # Build URL with query params
            url = endpoint
            if params:
                # Filter out None values and convert to string
                filtered_params = {
                    k: str(v) for k, v in params.items() if v is not None
                }
                if filtered_params:
                    url = f"{endpoint}?{urlencode(filtered_params)}"

            logger.debug(f"GET {url}")
            response = self.client.get(url)
            return self._handle_response(response)

        except httpx.ConnectError as e:
            raise CogencisConnectionError(
                f"Failed to connect to Cogencis API: {e}"
            ) from e
        except httpx.TimeoutException as e:
            raise CogencisConnectionError(
                f"Request to Cogencis API timed out: {e}"
            ) from e

    def post(
        self,
        endpoint: str,
        data: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Make a POST request to the API.

        Args:
            endpoint: API endpoint (without base URL)
            data: Request body data
            params: Query parameters

        Returns:
            Parsed JSON response

        Raises:
            CogencisConnectionError: If connection fails
            CogencisAPIError: If API returns an error
        """
        try:
            url = endpoint
            if params:
                filtered_params = {
                    k: str(v) for k, v in params.items() if v is not None
                }
                if filtered_params:
                    url = f"{endpoint}?{urlencode(filtered_params)}"

            logger.debug(f"POST {url}")
            response = self.client.post(url, json=data)
            return self._handle_response(response)

        except httpx.ConnectError as e:
            raise CogencisConnectionError(
                f"Failed to connect to Cogencis API: {e}"
            ) from e
        except httpx.TimeoutException as e:
            raise CogencisConnectionError(
                f"Request to Cogencis API timed out: {e}"
            ) from e

    def close(self) -> None:
        """Close the HTTP client."""
        if self._client is not None:
            self._client.close()
            self._client = None

    def __enter__(self) -> "CogencisHTTPClient":
        """Context manager entry."""
        return self

    def __exit__(self, *args: Any) -> None:
        """Context manager exit."""
        self.close()