"""Client for fetching public market data from various sources."""

import logging
from datetime import date
from urllib.parse import quote

from .core.http_client import PublicMarketDataHTTPClient
from .core.exceptions import (
    PublicMarketDataError,
    PublicMarketDataNotFoundError,
)

logger = logging.getLogger(__name__)


class PublicMarketDataClient:
    """Client for fetching public market data.

    Currently supports:
    - CDSL FII/FPI data (monthly and fortnightly reports)

    For Groww market data (options, prices, indices), see tools.groww module.
    """

    # CDSL FII data URLs
    CDSL_FII_MONTHLY_URL = "https://www.cdslindia.com/eservices/publications/FIIMonthly"
    CDSL_FII_FORTNIGHTLY_BASE_URL = "https://www.cdslindia.com/publications/FII/FortnightlySecWisePages"

    # Known available fortnightly report dates (in reverse chronological order)
    # Format: "Month DD, YYYY" or "Month DD,YYYY" (inconsistent spacing in actual URLs)
    AVAILABLE_FORTNIGHTLY_DATES = [
        "December 31, 2025",
        "December 15, 2025",
        "November 30, 2025",
        "November 15, 2025",
        "October 31, 2025",
        "October 15,2025",
        "September 30,2025",
        "September 15,2025",
        "August 31,2025",
        "August 15,2025",
        "July 31,2025",
        "July 15,2025",
        "June 30,2025",
        "June 15,2025",
        "May 31, 2025",
        "May 15, 2025",
        "April 30, 2025",
        "April 15, 2025",
        "March 31, 2025",
        "March 15, 2025",
        "February 28, 2025",
        "February 15, 2025",
        "January 31, 2025",
        "January 15, 2025",
        "December 31, 2024",
        "December 15, 2024",
        "November 30, 2024",
        "November 15, 2024",
        "October 31, 2024",
        "October 15, 2024",
        "September 30, 2024",
        "September 15, 2024",
        "August 31, 2024",
        "August 15, 2024",
        "July 31, 2024",
        "July 15, 2024",
        "June 30, 2024",
        "June 15, 2024",
        "May 31, 2024",
        "May 15, 2024",
        "April 30, 2024",
        "April 15, 2024",
        "March 31, 2024",
        "March 15, 2024",
        "February 29, 2024",
        "February 15, 2024",
        "January 31, 2024",
    ]

    def __init__(self, timeout: float = 30.0) -> None:
        """Initialize the client.

        Args:
            timeout: Request timeout in seconds
        """
        self.http_client = PublicMarketDataHTTPClient(timeout=timeout)

    def get_fii_monthly_data(self) -> str:
        """Fetch FII/FPI monthly investment and derivative trading data from CDSL.

        Returns daily trends in FII/FPI investments including:
        - Investments by asset class (Equity, Debt, Hybrid, MF, AIFs)
        - Investment routes (Stock Exchange, Primary Market)
        - Gross purchases, sales, and net investment
        - Daily derivative trading data (Index/Stock futures & options)

        Returns:
            Markdown formatted content of the FII Monthly page

        Raises:
            PublicMarketDataConnectionError: If connection fails
            PublicMarketDataAPIError: If request fails
        """
        return self.http_client.get_markdown(
            self.CDSL_FII_MONTHLY_URL,
            strip_tags=["script", "style", "nav", "header", "aside"],
        )

    def get_fii_fortnightly_data(self, report_date: str | None = None) -> str:
        """Fetch FII/FPI fortnightly sector-wise investment data from CDSL.

        Returns sector-level FPI investment data including:
        - Assets Under Custody (AUC) at start and end of period
        - Net investment by sector for the fortnight
        - Data for Equity, Debt, Hybrid, MF, and AIFs
        - Top companies in debt holdings

        Args:
            report_date: Report date string (e.g., "December 31, 2025").
                        If None, fetches the most recent available report.

        Returns:
            Markdown formatted content of the fortnightly report

        Raises:
            PublicMarketDataNotFoundError: If the report date is not available
            PublicMarketDataConnectionError: If connection fails
            PublicMarketDataAPIError: If request fails
        """
        if report_date is None:
            report_date = self.AVAILABLE_FORTNIGHTLY_DATES[0]

        # Construct the URL with URL-encoded date
        url = f"{self.CDSL_FII_FORTNIGHTLY_BASE_URL}/{quote(report_date)}.html"

        return self.http_client.get_markdown(
            url,
            strip_tags=["script", "style", "nav", "header", "aside"],
        )

    def list_available_fortnightly_dates(self) -> list[str]:
        """List all available fortnightly report dates.

        Returns:
            List of available date strings in reverse chronological order
        """
        return self.AVAILABLE_FORTNIGHTLY_DATES.copy()

    def close(self) -> None:
        """Close the HTTP client."""
        self.http_client.close()

    def __enter__(self) -> "PublicMarketDataClient":
        """Context manager entry."""
        return self

    def __exit__(self, *args) -> None:
        """Context manager exit."""
        self.close()
