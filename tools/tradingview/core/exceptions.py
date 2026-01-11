"""Custom exceptions for TradingView SDK."""

from typing import Any


class TradingViewError(Exception):
    """Base exception for all TradingView SDK errors."""

    def __init__(self, message: str, details: Any = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details

    def __str__(self) -> str:
        if self.details:
            return f"{self.message} - Details: {self.details}"
        return self.message


class TradingViewAPIError(TradingViewError):
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


class TradingViewConnectionError(TradingViewError):
    """Raised when connection to the API fails."""

    pass


class TradingViewRateLimitError(TradingViewError):
    """Raised when API rate limit is exceeded."""

    def __init__(
        self,
        message: str = "Rate limit exceeded",
        retry_after: int | None = None,
    ) -> None:
        super().__init__(message)
        self.retry_after = retry_after


class TradingViewValidationError(TradingViewError):
    """Raised when input validation fails."""

    pass


class TradingViewNotFoundError(TradingViewError):
    """Raised when a requested resource is not found."""

    pass