"""HTTP client for Public Market Data toolkit."""

import logging
import re
from typing import Any

import httpx
from lxml import html as lxml_html
from markdownify import markdownify as md

from .exceptions import (
    PublicMarketDataAPIError,
    PublicMarketDataConnectionError,
    PublicMarketDataNotFoundError,
)

logger = logging.getLogger(__name__)


class PublicMarketDataHTTPClient:
    """HTTP client for fetching public market data from various sources."""

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
        """Get default headers for requests."""
        return {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept-Language": "en-US,en;q=0.9",
        }

    def get_html(self, url: str) -> str:
        """Fetch HTML from a URL.

        Args:
            url: Full URL to fetch

        Returns:
            Raw HTML content

        Raises:
            PublicMarketDataConnectionError: If connection fails
            PublicMarketDataNotFoundError: If page not found
            PublicMarketDataAPIError: If request fails
        """
        try:
            logger.debug(f"GET HTML {url}")
            response = self.client.get(url)

            if response.status_code == 404:
                raise PublicMarketDataNotFoundError(
                    f"Page not found: {url}",
                )

            if response.status_code >= 400:
                raise PublicMarketDataAPIError(
                    f"Failed to fetch page",
                    status_code=response.status_code,
                    response_body=response.text[:500],
                )

            return response.text

        except httpx.ConnectError as e:
            raise PublicMarketDataConnectionError(
                f"Failed to connect to {url}: {e}"
            ) from e
        except httpx.TimeoutException as e:
            raise PublicMarketDataConnectionError(
                f"Request to {url} timed out: {e}"
            ) from e

    def get_json(
        self,
        url: str,
        headers: dict[str, str] | None = None,
    ) -> dict[str, Any] | list[Any]:
        """Fetch JSON from a URL.

        Args:
            url: Full URL to fetch
            headers: Optional additional headers to merge with defaults

        Returns:
            Parsed JSON response

        Raises:
            PublicMarketDataConnectionError: If connection fails
            PublicMarketDataNotFoundError: If page not found
            PublicMarketDataAPIError: If request fails or JSON parsing fails
        """
        try:
            logger.debug(f"GET JSON {url}")

            # Merge headers if provided
            request_headers = self._get_default_headers()
            request_headers["Accept"] = "application/json"
            if headers:
                request_headers.update(headers)

            response = self.client.get(url, headers=request_headers)

            if response.status_code == 404:
                raise PublicMarketDataNotFoundError(
                    f"Resource not found: {url}",
                )

            if response.status_code >= 400:
                raise PublicMarketDataAPIError(
                    f"API request failed",
                    status_code=response.status_code,
                    response_body=response.text[:500],
                )

            try:
                return response.json()
            except Exception as e:
                raise PublicMarketDataAPIError(
                    f"Failed to parse JSON response: {e}",
                    status_code=response.status_code,
                    response_body=response.text[:500],
                )

        except httpx.ConnectError as e:
            raise PublicMarketDataConnectionError(
                f"Failed to connect to {url}: {e}"
            ) from e
        except httpx.TimeoutException as e:
            raise PublicMarketDataConnectionError(
                f"Request to {url} timed out: {e}"
            ) from e

    def _clean_html(self, html_content: str, remove_tags: list[str]) -> str:
        """Remove specified tags and their content from HTML.

        Args:
            html_content: Raw HTML string
            remove_tags: List of tag names to remove (with their content)

        Returns:
            Cleaned HTML string
        """
        try:
            tree = lxml_html.fromstring(html_content)

            # Remove specified tags completely (including their content)
            for tag in remove_tags:
                for element in tree.xpath(f"//{tag}"):
                    element.getparent().remove(element)

            return lxml_html.tostring(tree, encoding="unicode")
        except Exception as e:
            logger.warning(f"Failed to parse HTML with lxml: {e}, falling back to regex")
            # Fallback to regex-based removal
            result = html_content
            for tag in remove_tags:
                # Remove tag with content (non-greedy)
                result = re.sub(
                    rf"<{tag}[^>]*>.*?</{tag}>",
                    "",
                    result,
                    flags=re.DOTALL | re.IGNORECASE,
                )
                # Remove self-closing tags
                result = re.sub(
                    rf"<{tag}[^>]*/?>",
                    "",
                    result,
                    flags=re.IGNORECASE,
                )
            return result

    def get_markdown(
        self,
        url: str,
        strip_tags: list[str] | None = None,
        heading_style: str = "ATX",
    ) -> str:
        """Fetch HTML and convert to markdown.

        Args:
            url: Full URL to fetch
            strip_tags: List of HTML tags to remove completely (default: script, style, nav, footer, header, aside)
            heading_style: Markdown heading style (ATX or SETEXT)

        Returns:
            Markdown content

        Raises:
            PublicMarketDataConnectionError: If connection fails
            PublicMarketDataNotFoundError: If page not found
        """
        html = self.get_html(url)

        if strip_tags is None:
            strip_tags = ["script", "style", "nav", "footer", "header", "aside", "noscript"]

        # Pre-process HTML to completely remove unwanted tags
        cleaned_html = self._clean_html(html, strip_tags)

        # Convert HTML to markdown
        markdown = md(
            cleaned_html,
            heading_style=heading_style,
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

    def __enter__(self) -> "PublicMarketDataHTTPClient":
        """Context manager entry."""
        return self

    def __exit__(self, *args: Any) -> None:
        """Context manager exit."""
        self.close()
