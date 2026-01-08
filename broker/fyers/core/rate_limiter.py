"""
Rate limiter for the Fyers SDK.

Implements rate limiting with tracking for:
- Per second: 10 requests
- Per minute: 200 requests
- Per day: 100,000 requests

Includes persistence for daily counters to survive restarts.
"""

import asyncio
import json
import time
from datetime import datetime, date, timedelta
from pathlib import Path
from typing import Optional, Callable, Any
from collections import deque

from broker.fyers.core.exceptions import FyersRateLimitError
from broker.fyers.core.logger import get_logger
from broker.fyers.models.rate_limit import (
    RateLimitConfig,
    RateLimitState,
    RateLimitType,
    APICallRecord,
    DailyRateLimitRecord,
)

logger = get_logger("fyers.rate_limiter")


class RateLimiter:
    """
    Rate limiter with sliding window tracking and persistence.
    
    Tracks API calls across three time windows:
    - Second: 10 requests/second
    - Minute: 200 requests/minute
    - Day: 100,000 requests/day
    
    After 100,000 daily calls, all API requests are blocked until the next day.
    """
    
    def __init__(
        self,
        config: Optional[RateLimitConfig] = None,
        persistence_path: Optional[str] = None,
    ):
        """
        Initialize the rate limiter.
        
        Args:
            config: Rate limit configuration
            persistence_path: File path to persist daily counters
        """
        self.config = config or RateLimitConfig()
        self.persistence_path = Path(persistence_path) if persistence_path else None
        
        # Sliding window tracking using deques
        self._second_window: deque = deque()
        self._minute_window: deque = deque()
        
        # State tracking
        self._state = RateLimitState()
        self._lock = asyncio.Lock()
        
        # Load persisted state if available
        self._load_persisted_state()
        
        logger.info(
            f"Rate limiter initialized: {self.config.requests_per_second}/s, "
            f"{self.config.requests_per_minute}/min, {self.config.requests_per_day}/day"
        )
    
    def _load_persisted_state(self) -> None:
        """Load persisted daily counter from file."""
        if not self.persistence_path or not self.persistence_path.exists():
            self._state.current_day = date.today()
            return
        
        try:
            with open(self.persistence_path, "r") as f:
                data = json.load(f)
            
            persisted_date = date.fromisoformat(data.get("date", ""))
            
            if persisted_date == date.today():
                # Same day, restore counter
                self._state.day_count = data.get("total_calls", 0)
                self._state.current_day = persisted_date
                self._state.is_day_limit_reached = (
                    self._state.day_count >= self.config.requests_per_day
                )
                logger.info(
                    f"Restored daily counter: {self._state.day_count} calls today"
                )
            else:
                # New day, reset counter
                self._state.day_count = 0
                self._state.current_day = date.today()
                self._state.is_day_limit_reached = False
                logger.info("New day detected, reset daily counter")
                
        except (json.JSONDecodeError, ValueError, KeyError) as e:
            logger.warning(f"Failed to load persisted state: {e}")
            self._state.current_day = date.today()
    
    def _persist_state(self) -> None:
        """Persist daily counter to file."""
        if not self.persistence_path:
            return
        
        try:
            # Ensure directory exists
            self.persistence_path.parent.mkdir(parents=True, exist_ok=True)
            
            record = DailyRateLimitRecord(
                date=self._state.current_day or date.today(),
                total_calls=self._state.day_count,
                successful_calls=self._state.day_count,  # Simplified
                last_updated=datetime.utcnow(),
            )
            
            with open(self.persistence_path, "w") as f:
                json.dump(record.model_dump(mode="json"), f, default=str)
                
        except Exception as e:
            logger.error(f"Failed to persist rate limit state: {e}")
    
    def _check_day_rollover(self) -> None:
        """Check if the day has rolled over and reset counters if needed."""
        today = date.today()
        
        if self._state.current_day != today:
            logger.info(
                f"Day rollover detected: {self._state.current_day} -> {today}. "
                f"Resetting daily counter from {self._state.day_count}"
            )
            self._state.day_count = 0
            self._state.current_day = today
            self._state.is_day_limit_reached = False
            self._persist_state()
    
    def _cleanup_windows(self, now: float) -> None:
        """Remove expired entries from sliding windows."""
        # Clean second window (1 second)
        second_cutoff = now - 1.0
        while self._second_window and self._second_window[0] < second_cutoff:
            self._second_window.popleft()
        
        # Clean minute window (60 seconds)
        minute_cutoff = now - 60.0
        while self._minute_window and self._minute_window[0] < minute_cutoff:
            self._minute_window.popleft()
    
    def _can_make_request(self) -> tuple[bool, Optional[RateLimitType], Optional[float]]:
        """
        Check if a request can be made without exceeding rate limits.
        
        Returns:
            Tuple of (can_make_request, limit_type_exceeded, retry_after_seconds)
        """
        self._check_day_rollover()
        
        now = time.time()
        self._cleanup_windows(now)
        
        # Check daily limit first (most restrictive for blocking)
        if self._state.day_count >= self.config.requests_per_day:
            self._state.is_day_limit_reached = True
            # Calculate time until midnight
            tomorrow = datetime.combine(date.today() + timedelta(days=1), datetime.min.time())
            retry_after = (tomorrow - datetime.now()).total_seconds()
            return False, RateLimitType.DAY, retry_after
        
        # Check second limit
        second_count = len(self._second_window)
        if second_count >= self.config.requests_per_second:
            # Retry after oldest request expires from second window
            retry_after = max(0.0, self._second_window[0] + 1.0 - now)
            return False, RateLimitType.SECOND, retry_after
        
        # Check minute limit
        minute_count = len(self._minute_window)
        if minute_count >= self.config.requests_per_minute:
            # Retry after oldest request expires from minute window
            retry_after = max(0.0, self._minute_window[0] + 60.0 - now)
            return False, RateLimitType.MINUTE, retry_after
        
        return True, None, None
    
    def _record_request(self, endpoint: str = "", success: bool = True) -> None:
        """Record a request in the sliding windows."""
        now = time.time()
        
        self._second_window.append(now)
        self._minute_window.append(now)
        self._state.day_count += 1
        
        # Update state counters for reporting
        self._state.second_count = len(self._second_window)
        self._state.minute_count = len(self._minute_window)
        
        # Persist daily counter periodically (every 100 requests)
        if self._state.day_count % 100 == 0:
            self._persist_state()
        
        # Log at warning level when approaching limits
        day_usage = (self._state.day_count / self.config.requests_per_day) * 100
        if day_usage >= 90:
            logger.warning(
                f"Daily rate limit at {day_usage:.1f}%: "
                f"{self._state.day_count}/{self.config.requests_per_day}"
            )
        elif day_usage >= 75:
            logger.info(
                f"Daily rate limit at {day_usage:.1f}%: "
                f"{self._state.day_count}/{self.config.requests_per_day}"
            )
    
    async def acquire(self) -> None:
        """
        Acquire permission to make an API request.
        
        Raises:
            FyersRateLimitError: If rate limit is exceeded
        """
        async with self._lock:
            can_proceed, limit_type, retry_after = self._can_make_request()
            
            if not can_proceed:
                self._state.last_rate_limit_error = datetime.utcnow()
                
                if limit_type == RateLimitType.DAY:
                    logger.error(
                        f"DAILY RATE LIMIT REACHED: {self._state.day_count} calls. "
                        f"No more API calls allowed today!"
                    )
                    raise FyersRateLimitError(
                        message=f"Daily rate limit exceeded ({self.config.requests_per_day} requests/day). "
                               f"No more API calls allowed until tomorrow.",
                        limit_type="day",
                        retry_after=retry_after,
                    )
                
                logger.warning(
                    f"Rate limit exceeded ({limit_type}). Retry after {retry_after:.2f}s"
                )
                raise FyersRateLimitError(
                    message=f"Rate limit exceeded for {limit_type}",
                    limit_type=limit_type,
                    retry_after=retry_after,
                )
    
    async def record(self, endpoint: str = "", success: bool = True) -> None:
        """
        Record that a request was made.
        
        Args:
            endpoint: The API endpoint called
            success: Whether the request was successful
        """
        async with self._lock:
            self._record_request(endpoint, success)
    
    async def acquire_and_record(self, endpoint: str = "") -> None:
        """
        Acquire permission and record the request in one operation.
        
        Args:
            endpoint: The API endpoint being called
            
        Raises:
            FyersRateLimitError: If rate limit is exceeded
        """
        async with self._lock:
            can_proceed, limit_type, retry_after = self._can_make_request()
            
            if not can_proceed:
                self._state.last_rate_limit_error = datetime.utcnow()
                raise FyersRateLimitError(
                    message=f"Rate limit exceeded for {limit_type}",
                    limit_type=limit_type,
                    retry_after=retry_after,
                )
            
            self._record_request(endpoint)
    
    async def wait_if_needed(self) -> float:
        """
        Wait if necessary to avoid rate limiting.
        
        Returns:
            Seconds waited (0 if no wait needed)
        """
        async with self._lock:
            can_proceed, limit_type, retry_after = self._can_make_request()
            
            if can_proceed:
                return 0.0
            
            if limit_type == RateLimitType.DAY:
                # Don't wait for daily limit, raise error
                raise FyersRateLimitError(
                    message="Daily rate limit exceeded. Cannot wait.",
                    limit_type="day",
                    retry_after=retry_after,
                )
            
            wait_time = retry_after or 0.1
            logger.debug(f"Waiting {wait_time:.2f}s to avoid rate limit ({limit_type})")
            
        await asyncio.sleep(wait_time)
        return wait_time
    
    def get_state(self) -> RateLimitState:
        """Get the current rate limit state."""
        self._check_day_rollover()
        now = time.time()
        self._cleanup_windows(now)
        
        self._state.second_count = len(self._second_window)
        self._state.minute_count = len(self._minute_window)
        
        return self._state
    
    def get_summary(self) -> dict:
        """Get a summary of the current rate limit state."""
        state = self.get_state()
        return state.to_summary_dict(self.config)
    
    def is_daily_limit_reached(self) -> bool:
        """Check if the daily limit has been reached."""
        self._check_day_rollover()
        return self._state.day_count >= self.config.requests_per_day
    
    def get_remaining_daily_calls(self) -> int:
        """Get the number of remaining daily calls."""
        self._check_day_rollover()
        return max(0, self.config.requests_per_day - self._state.day_count)
    
    def force_persist(self) -> None:
        """Force persistence of current state."""
        self._persist_state()
    
    async def reset_for_testing(self) -> None:
        """Reset all counters (for testing only)."""
        async with self._lock:
            self._second_window.clear()
            self._minute_window.clear()
            self._state = RateLimitState()
            self._state.current_day = date.today()
            logger.warning("Rate limiter reset (testing only)")


def create_rate_limited_decorator(rate_limiter: RateLimiter):
    """
    Create a decorator that applies rate limiting to async functions.
    
    Args:
        rate_limiter: The rate limiter instance to use
        
    Returns:
        Decorator function
    """
    def decorator(func: Callable) -> Callable:
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            # Try to wait if needed
            await rate_limiter.wait_if_needed()
            
            # Acquire permission
            await rate_limiter.acquire()
            
            try:
                result = await func(*args, **kwargs)
                await rate_limiter.record(endpoint=func.__name__, success=True)
                return result
            except Exception:
                await rate_limiter.record(endpoint=func.__name__, success=False)
                raise
        
        wrapper.__name__ = func.__name__
        wrapper.__doc__ = func.__doc__
        return wrapper
    
    return decorator