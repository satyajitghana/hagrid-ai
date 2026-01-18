"""Custom exceptions for NSE India API client."""

from typing import Any


class NSEIndiaError(Exception):
    """Base exception for all NSE India related errors."""

    def __init__(self, message: str, details: Any = None):
        self.message = message
        self.details = details
        super().__init__(message)

    def __str__(self) -> str:
        if self.details:
            return f"{self.message} - Details: {self.details}"
        return self.message


class NSEIndiaAPIError(NSEIndiaError):
    """Error returned by NSE India API."""

    def __init__(
        self,
        message: str,
        status_code: int,
        response_body: str | None = None,
    ):
        self.status_code = status_code
        self.response_body = response_body
        super().__init__(message, details={"status_code": status_code, "response": response_body})

    def __str__(self) -> str:
        return f"{self.message} (status={self.status_code})"


class NSEIndiaRateLimitError(NSEIndiaError):
    """Rate limit exceeded by NSE India API."""

    def __init__(
        self,
        message: str = "Rate limit exceeded",
        retry_after: int | None = None,
    ):
        self.retry_after = retry_after
        super().__init__(message, details={"retry_after": retry_after})

    def __str__(self) -> str:
        if self.retry_after:
            return f"{self.message} - Retry after {self.retry_after} seconds"
        return self.message


class NSEIndiaConnectionError(NSEIndiaError):
    """Network/connection error when accessing NSE India API."""

    def __init__(self, message: str = "Connection error"):
        super().__init__(message)


class NSEIndiaParseError(NSEIndiaError):
    """Error parsing response from NSE India API."""

    def __init__(self, message: str = "Failed to parse response", raw_data: str | None = None):
        self.raw_data = raw_data
        super().__init__(message, details={"raw_data": raw_data[:500] if raw_data else None})
