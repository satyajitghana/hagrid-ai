"""
Custom exceptions for the Fyers SDK.
"""


class FyersException(Exception):
    """Base exception for all Fyers-related errors."""

    def __init__(self, message: str, code: int | None = None):
        self.message = message
        self.code = code
        super().__init__(self.message)

    def __str__(self) -> str:
        if self.code:
            return f"[{self.code}] {self.message}"
        return self.message


class FyersAuthenticationError(FyersException):
    """Raised when authentication fails."""

    def __init__(self, message: str = "Authentication failed", code: int | None = None):
        super().__init__(message, code)


class FyersRateLimitError(FyersException):
    """Raised when rate limit is exceeded."""

    def __init__(
        self,
        message: str = "Rate limit exceeded",
        code: int | None = None,
        limit_type: str | None = None,
        retry_after: float | None = None,
    ):
        super().__init__(message, code)
        self.limit_type = limit_type  # "second", "minute", or "day"
        self.retry_after = retry_after  # Seconds until reset

    def __str__(self) -> str:
        base = super().__str__()
        if self.limit_type:
            base += f" (limit type: {self.limit_type})"
        if self.retry_after:
            base += f" (retry after: {self.retry_after:.2f}s)"
        return base


class FyersAPIError(FyersException):
    """Raised when the Fyers API returns an error response."""

    def __init__(
        self,
        message: str,
        code: int | None = None,
        response_data: dict | None = None,
    ):
        super().__init__(message, code)
        self.response_data = response_data or {}

    def __str__(self) -> str:
        base = super().__str__()
        if self.response_data:
            base += f" | Response: {self.response_data}"
        return base


class FyersTokenExpiredError(FyersAuthenticationError):
    """Raised when the access token has expired."""

    def __init__(self, message: str = "Access token has expired", code: int | None = None):
        super().__init__(message, code)


class FyersTokenNotFoundError(FyersAuthenticationError):
    """Raised when no valid token is found."""

    def __init__(self, message: str = "No valid token found", code: int | None = None):
        super().__init__(message, code)


class FyersNetworkError(FyersException):
    """Raised when a network error occurs."""

    def __init__(self, message: str = "Network error occurred", code: int | None = None):
        super().__init__(message, code)