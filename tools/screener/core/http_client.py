"""HTTP client for Screener API and web scraping."""

import logging
from typing import Any
from urllib.parse import urlencode

import httpx
from markdownify import markdownify as md

from .exceptions import (
    ScreenerAPIError,
    ScreenerConnectionError,
    ScreenerRateLimitError,
    ScreenerNotFoundError,
)

logger = logging.getLogger(__name__)


class ScreenerHTTPClient:
    """HTTP client for making requests to Screener.in API and website."""

    BASE_URL = "https://www.screener.in"
    API_BASE = "https://www.screener.in/api"
    DEFAULT_TIMEOUT = 30.0

    def __init__(
        self,
        timeout: float = DEFAULT_TIMEOUT,
    ) -> None:
        """
        Initialize the Screener HTTP client.

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
        """Get default headers for requests."""
        return {
            "Accept": "application/json, text/html",
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept-Language": "en-US,en;q=0.9",
        }

    def _handle_json_response(self, response: httpx.Response) -> dict[str, Any] | list[Any]:
        """
        Handle JSON API response and raise appropriate exceptions.

        Args:
            response: The HTTP response object

        Returns:
            Parsed JSON response

        Raises:
            ScreenerRateLimitError: If rate limit is exceeded
            ScreenerNotFoundError: If resource not found
            ScreenerAPIError: For other API errors
        """
        if response.status_code == 404:
            raise ScreenerNotFoundError(
                "Resource not found",
                details=response.text,
            )

        if response.status_code == 429:
            retry_after = response.headers.get("Retry-After")
            raise ScreenerRateLimitError(
                "Rate limit exceeded",
                retry_after=int(retry_after) if retry_after else None,
            )

        if response.status_code >= 400:
            raise ScreenerAPIError(
                f"API request failed",
                status_code=response.status_code,
                response_body=response.text,
            )

        try:
            data = response.json()
        except Exception as e:
            raise ScreenerAPIError(
                f"Failed to parse JSON response: {e}",
                status_code=response.status_code,
                response_body=response.text,
            )

        return data

    def get_json(
        self,
        endpoint: str,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any] | list[Any]:
        """
        Make a GET request to the API and return JSON.

        Args:
            endpoint: API endpoint (without base URL)
            params: Query parameters

        Returns:
            Parsed JSON response

        Raises:
            ScreenerConnectionError: If connection fails
            ScreenerAPIError: If API returns an error
        """
        try:
            url = f"{self.API_BASE}{endpoint}"
            if params:
                filtered_params = {
                    k: str(v) for k, v in params.items() if v is not None
                }
                if filtered_params:
                    url = f"{url}?{urlencode(filtered_params)}"

            logger.debug(f"GET JSON {url}")
            response = self.client.get(url)
            return self._handle_json_response(response)

        except httpx.ConnectError as e:
            raise ScreenerConnectionError(
                f"Failed to connect to Screener API: {e}"
            ) from e
        except httpx.TimeoutException as e:
            raise ScreenerConnectionError(
                f"Request to Screener API timed out: {e}"
            ) from e

    def get_html(
        self,
        path: str,
    ) -> str:
        """
        Make a GET request to fetch HTML page.

        Args:
            path: Page path (e.g., "/company/RELIANCE/")

        Returns:
            Raw HTML content

        Raises:
            ScreenerConnectionError: If connection fails
            ScreenerNotFoundError: If page not found
            ScreenerAPIError: If request fails
        """
        try:
            url = f"{self.BASE_URL}{path}"
            logger.debug(f"GET HTML {url}")
            response = self.client.get(url)

            if response.status_code == 404:
                raise ScreenerNotFoundError(
                    f"Page not found: {path}",
                )

            if response.status_code == 429:
                retry_after = response.headers.get("Retry-After")
                raise ScreenerRateLimitError(
                    "Rate limit exceeded",
                    retry_after=int(retry_after) if retry_after else None,
                )

            if response.status_code >= 400:
                raise ScreenerAPIError(
                    f"Failed to fetch page",
                    status_code=response.status_code,
                    response_body=response.text[:500],
                )

            return response.text

        except httpx.ConnectError as e:
            raise ScreenerConnectionError(
                f"Failed to connect to Screener.in: {e}"
            ) from e
        except httpx.TimeoutException as e:
            raise ScreenerConnectionError(
                f"Request to Screener.in timed out: {e}"
            ) from e

    def get_markdown(
        self,
        path: str,
        strip_scripts: bool = True,
        strip_styles: bool = True,
        heading_style: str = "ATX",
    ) -> str:
        """
        Fetch HTML page and convert to markdown.

        Args:
            path: Page path (e.g., "/company/RELIANCE/")
            strip_scripts: Remove <script> tags
            strip_styles: Remove <style> tags
            heading_style: Markdown heading style (ATX or SETEXT)

        Returns:
            Markdown content

        Raises:
            ScreenerConnectionError: If connection fails
            ScreenerNotFoundError: If page not found
        """
        html = self.get_html(path)
        
        # Convert HTML to markdown
        markdown = md(
            html,
            heading_style=heading_style,
            strip=["script", "style", "nav", "footer", "header", "aside"] if strip_scripts else None,
        )
        
        # Clean up excessive whitespace
        lines = markdown.split("\n")
        cleaned_lines = []
        prev_empty = False
        
        for line in lines:
            stripped = line.strip()
            is_empty = len(stripped) == 0
            
            # Skip multiple consecutive empty lines
            if is_empty and prev_empty:
                continue
            
            cleaned_lines.append(line)
            prev_empty = is_empty
        
        return "\n".join(cleaned_lines).strip()

    def close(self) -> None:
        """Close the HTTP client."""
        if self._client is not None:
            self._client.close()
            self._client = None

    def __enter__(self) -> "ScreenerHTTPClient":
        """Context manager entry."""
        return self

    def __exit__(self, *args: Any) -> None:
        """Context manager exit."""
        self.close()