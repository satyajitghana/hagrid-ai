"""HTTP client for Groww toolkit."""

import logging
from typing import Any

import httpx

from .exceptions import (
    GrowwAPIError,
    GrowwConnectionError,
    GrowwNotFoundError,
)

logger = logging.getLogger(__name__)


class GrowwHTTPClient:
    """HTTP client for fetching data from Groww APIs."""

    DEFAULT_TIMEOUT = 30.0

    def __init__(
        self,
        timeout: float = DEFAULT_TIMEOUT,
    ) -> None:
        """Initialize the HTTP client.

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
                follow_redirects=True,
            )
        return self._client

    def _get_default_headers(self) -> dict[str, str]:
        """Get default headers for Groww API requests."""
        return {
            "Accept": "application/json, text/plain, */*",
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept-Language": "en-US,en;q=0.9",
            "x-app-id": "growwWeb",
            "x-platform": "web",
        }

    def get_json(
        self,
        url: str,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> dict[str, Any] | list[Any]:
        """Fetch JSON from a Groww API URL.

        Args:
            url: Full URL to fetch
            params: Optional query parameters
            headers: Optional additional headers to merge with defaults

        Returns:
            Parsed JSON response

        Raises:
            GrowwConnectionError: If connection fails
            GrowwNotFoundError: If resource not found
            GrowwAPIError: If request fails or JSON parsing fails
        """
        try:
            logger.debug(f"GET JSON {url} params={params}")

            # Merge headers if provided
            request_headers = self._get_default_headers()
            if headers:
                request_headers.update(headers)

            response = self.client.get(url, params=params, headers=request_headers)

            if response.status_code == 404:
                raise GrowwNotFoundError(
                    f"Resource not found: {url}",
                )

            if response.status_code >= 400:
                raise GrowwAPIError(
                    f"API request failed",
                    status_code=response.status_code,
                    response_body=response.text[:500],
                )

            try:
                return response.json()
            except Exception as e:
                raise GrowwAPIError(
                    f"Failed to parse JSON response: {e}",
                    status_code=response.status_code,
                    response_body=response.text[:500],
                )

        except httpx.ConnectError as e:
            raise GrowwConnectionError(
                f"Failed to connect to {url}: {e}"
            ) from e
        except httpx.TimeoutException as e:
            raise GrowwConnectionError(
                f"Request to {url} timed out: {e}"
            ) from e

    def close(self) -> None:
        """Close the HTTP client."""
        if self._client is not None:
            self._client.close()
            self._client = None

    def __enter__(self) -> "GrowwHTTPClient":
        """Context manager entry."""
        return self

    def __exit__(self, *args: Any) -> None:
        """Context manager exit."""
        self.close()
