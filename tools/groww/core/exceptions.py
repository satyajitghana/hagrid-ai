"""Custom exceptions for Groww toolkit."""

from typing import Any


class GrowwError(Exception):
    """Base exception for all Groww errors."""

    def __init__(self, message: str, details: Any = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details

    def __str__(self) -> str:
        if self.details:
            return f"{self.message} - Details: {self.details}"
        return self.message


class GrowwAPIError(GrowwError):
    """Raised when the Groww API returns an error response."""

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


class GrowwConnectionError(GrowwError):
    """Raised when connection to Groww API fails."""

    pass


class GrowwNotFoundError(GrowwError):
    """Raised when a resource is not found."""

    pass


class GrowwParseError(GrowwError):
    """Raised when parsing response data fails."""

    pass
