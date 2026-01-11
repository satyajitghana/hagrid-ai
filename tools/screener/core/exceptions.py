"""Custom exceptions for Screener SDK."""

from typing import Any


class ScreenerError(Exception):
    """Base exception for all Screener SDK errors."""

    def __init__(self, message: str, details: Any = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details

    def __str__(self) -> str:
        if self.details:
            return f"{self.message} - Details: {self.details}"
        return self.message


class ScreenerAPIError(ScreenerError):
    """Raised when the API returns an error response."""

    def __init__(
        self,
        message: str,
        status_code: int | None = None,
        response_body: Any = None,
    ) -> None:
        super().__init__(message, details=response_body)
        self.status_code = status_code
        self.response_body = response_body

    def __str__(self) -> str:
        parts = [self.message]
        if self.status_code:
            parts.append(f"Status: {self.status_code}")
        if self.response_body:
            parts.append(f"Response: {self.response_body}")
        return " | ".join(parts)


class ScreenerConnectionError(ScreenerError):
    """Raised when connection to the API/website fails."""

    pass


class ScreenerRateLimitError(ScreenerError):
    """Raised when rate limit is exceeded."""

    def __init__(
        self,
        message: str = "Rate limit exceeded",
        retry_after: int | None = None,
    ) -> None:
        super().__init__(message)
        self.retry_after = retry_after


class ScreenerValidationError(ScreenerError):
    """Raised when input validation fails."""

    pass


class ScreenerNotFoundError(ScreenerError):
    """Raised when a company or resource is not found."""

    pass
