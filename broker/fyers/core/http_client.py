"""
HTTP client for the Fyers SDK.

Provides rate-limited HTTP requests with automatic retry and error handling.
"""

import time
from typing import Any, Dict, Optional, Union

import httpx

from broker.fyers.core.exceptions import (
    FyersAPIError,
    FyersAuthenticationError,
    FyersNetworkError,
    FyersRateLimitError,
)
from broker.fyers.core.logger import get_logger
from broker.fyers.core.rate_limiter import RateLimiter
from broker.fyers.models.config import FyersConfig
from broker.fyers.models.rate_limit import RateLimitConfig

logger = get_logger("fyers.http_client")


class HTTPClient:
    """
    Rate-limited HTTP client for Fyers API.
    
    Features:
    - Automatic rate limiting (10/s, 200/min, 100k/day)
    - Request/response logging
    - Error handling and retries
    - Authentication header management
    """
    
    def __init__(
        self,
        config: FyersConfig,
        rate_limiter: Optional[RateLimiter] = None,
        timeout: float = 30.0,
    ):
        """
        Initialize the HTTP client.
        
        Args:
            config: Fyers configuration
            rate_limiter: Optional rate limiter (creates one if not provided)
            timeout: Request timeout in seconds
        """
        self.config = config
        self.timeout = timeout
        
        # Initialize rate limiter
        if rate_limiter:
            self.rate_limiter = rate_limiter
        else:
            rate_limit_config = RateLimitConfig()
            self.rate_limiter = RateLimiter(
                config=rate_limit_config,
                persistence_path=config.rate_limit_file_path,
            )
        
        # Access token (set after authentication)
        self._access_token: Optional[str] = None
        
        logger.info(f"HTTP client initialized for {config.api_base_url}")
    
    def set_access_token(self, token: str) -> None:
        """
        Set the access token for authenticated requests.
        
        Args:
            token: The access token
        """
        self._access_token = token
        logger.debug("Access token set")
    
    def clear_access_token(self) -> None:
        """Clear the stored access token."""
        self._access_token = None
        logger.debug("Access token cleared")
    
    def _get_headers(self, additional_headers: Optional[Dict[str, str]] = None) -> Dict[str, str]:
        """
        Get headers for the request.
        
        Args:
            additional_headers: Additional headers to include
            
        Returns:
            Headers dictionary
        """
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        
        # Add authorization header if token is set
        if self._access_token:
            headers["Authorization"] = f"{self.config.client_id}:{self._access_token}"
        
        # Merge additional headers
        if additional_headers:
            headers.update(additional_headers)
        
        return headers
    
    def _build_url(self, endpoint: str, base_url: Optional[str] = None) -> str:
        """
        Build the full URL for an endpoint.
        
        Args:
            endpoint: API endpoint path
            base_url: Optional base URL override
            
        Returns:
            Full URL string
        """
        base = base_url or self.config.api_base_url
        
        # Remove trailing slash from base and leading slash from endpoint
        base = base.rstrip("/")
        endpoint = endpoint.lstrip("/")
        
        return f"{base}/{endpoint}"
    
    async def _handle_response(
        self,
        response: httpx.Response,
        endpoint: str,
    ) -> Dict[str, Any]:
        """
        Handle API response.
        
        Args:
            response: HTTP response object
            endpoint: The endpoint called (for logging)
            
        Returns:
            Response data as dictionary
            
        Raises:
            FyersAPIError: If API returns an error
            FyersAuthenticationError: If authentication fails
        """
        try:
            data = response.json()
        except Exception:
            data = {"raw_response": response.text}
        
        status_code = response.status_code
        
        # Log response
        logger.debug(
            f"Response from {endpoint}: status={status_code}, "
            f"data={str(data)[:200]}..."
        )
        
        # Check for HTTP errors
        if status_code >= 400:
            if status_code == 401:
                raise FyersAuthenticationError(
                    "Authentication failed. Token may be expired.",
                    code=status_code,
                )
            elif status_code == 429:
                raise FyersRateLimitError(
                    "Rate limit exceeded (HTTP 429)",
                    code=status_code,
                )
            else:
                raise FyersAPIError(
                    f"API request failed with status {status_code}",
                    code=status_code,
                    response_data=data,
                )
        
        # Check for API-level errors in response
        if isinstance(data, dict):
            status = data.get("s", "").lower()
            code = data.get("code")
            message = data.get("message", "")
            
            if status == "error":
                # Check for specific error types
                if code == 401 or "unauthorized" in message.lower():
                    raise FyersAuthenticationError(
                        f"Authentication error: {message}",
                        code=code,
                    )
                raise FyersAPIError(
                    message or "API returned an error",
                    code=code,
                    response_data=data,
                )
        
        return data
    
    async def request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        json_data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        base_url: Optional[str] = None,
        skip_rate_limit: bool = False,
    ) -> Dict[str, Any]:
        """
        Make an HTTP request with rate limiting.
        
        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            endpoint: API endpoint
            params: Query parameters
            json_data: JSON body data
            headers: Additional headers
            base_url: Optional base URL override
            skip_rate_limit: Skip rate limiting (use carefully)
            
        Returns:
            Response data as dictionary
            
        Raises:
            FyersRateLimitError: If rate limit is exceeded
            FyersAPIError: If API returns an error
            FyersNetworkError: If network error occurs
        """
        # Check rate limit
        if not skip_rate_limit:
            try:
                await self.rate_limiter.acquire()
            except FyersRateLimitError:
                logger.error(f"Rate limit blocked request to {endpoint}")
                raise
        
        url = self._build_url(endpoint, base_url)
        request_headers = self._get_headers(headers)
        
        start_time = time.time()
        
        try:
            logger.debug(f"Making {method} request to {url}")
            
            async with httpx.AsyncClient() as client:
                response = await client.request(
                    method=method.upper(),
                    url=url,
                    params=params,
                    json=json_data,
                    headers=request_headers,
                    timeout=self.timeout,
                )
            
            elapsed_ms = (time.time() - start_time) * 1000
            
            # Record the request
            if not skip_rate_limit:
                await self.rate_limiter.record(endpoint=endpoint, success=True)
            
            logger.debug(f"{method} {endpoint} completed in {elapsed_ms:.0f}ms")
            
            return await self._handle_response(response, endpoint)
            
        except httpx.RequestError as e:
            elapsed_ms = (time.time() - start_time) * 1000
            
            # Record failed request
            if not skip_rate_limit:
                await self.rate_limiter.record(endpoint=endpoint, success=False)
            
            logger.error(f"Network error for {method} {endpoint}: {e}")
            raise FyersNetworkError(f"Network error: {e}")
            
        except (FyersRateLimitError, FyersAPIError, FyersAuthenticationError):
            # Re-raise known exceptions
            if not skip_rate_limit:
                await self.rate_limiter.record(endpoint=endpoint, success=False)
            raise
            
        except Exception as e:
            if not skip_rate_limit:
                await self.rate_limiter.record(endpoint=endpoint, success=False)
            logger.error(f"Unexpected error for {method} {endpoint}: {e}")
            raise FyersAPIError(f"Unexpected error: {e}")
    
    async def get(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Make a GET request.
        
        Args:
            endpoint: API endpoint
            params: Query parameters
            **kwargs: Additional arguments passed to request()
            
        Returns:
            Response data
        """
        return await self.request("GET", endpoint, params=params, **kwargs)
    
    async def post(
        self,
        endpoint: str,
        json_data: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Make a POST request.
        
        Args:
            endpoint: API endpoint
            json_data: JSON body data
            **kwargs: Additional arguments passed to request()
            
        Returns:
            Response data
        """
        return await self.request("POST", endpoint, json_data=json_data, **kwargs)
    
    async def put(
        self,
        endpoint: str,
        json_data: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Make a PUT request.
        
        Args:
            endpoint: API endpoint
            json_data: JSON body data
            **kwargs: Additional arguments passed to request()
            
        Returns:
            Response data
        """
        return await self.request("PUT", endpoint, json_data=json_data, **kwargs)
    
    async def delete(
        self,
        endpoint: str,
        json_data: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Make a DELETE request.
        
        Args:
            endpoint: API endpoint
            json_data: JSON body data
            **kwargs: Additional arguments passed to request()
            
        Returns:
            Response data
        """
        return await self.request("DELETE", endpoint, json_data=json_data, **kwargs)
    
    def get_rate_limit_status(self) -> Dict[str, Any]:
        """
        Get the current rate limit status.
        
        Returns:
            Rate limit summary dictionary
        """
        return self.rate_limiter.get_summary()
    
    def get_remaining_daily_calls(self) -> int:
        """
        Get remaining daily API calls.
        
        Returns:
            Number of remaining calls
        """
        return self.rate_limiter.get_remaining_daily_calls()
    
    def is_daily_limit_reached(self) -> bool:
        """
        Check if daily rate limit has been reached.
        
        Returns:
            True if limit reached
        """
        return self.rate_limiter.is_daily_limit_reached()