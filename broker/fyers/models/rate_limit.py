"""
Rate limiting models for the Fyers SDK.

Rate Limits:
- Per second: 10 requests
- Per minute: 200 requests
- Per day: 100,000 requests
"""

from __future__ import annotations

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime, date
from enum import Enum


class RateLimitType(str, Enum):
    """Types of rate limits."""
    SECOND = "second"
    MINUTE = "minute"
    DAY = "day"


class RateLimitConfig(BaseModel):
    """Configuration for rate limiting."""
    
    requests_per_second: int = Field(
        default=10,
        description="Maximum requests per second"
    )
    requests_per_minute: int = Field(
        default=200,
        description="Maximum requests per minute"
    )
    requests_per_day: int = Field(
        default=100000,
        description="Maximum requests per day"
    )
    
    # Safety margins to avoid hitting limits
    second_margin: float = Field(
        default=0.1,
        description="Safety margin for per-second limit (0.1 = 10%)"
    )
    minute_margin: float = Field(
        default=0.1,
        description="Safety margin for per-minute limit"
    )
    day_margin: float = Field(
        default=0.05,
        description="Safety margin for per-day limit"
    )
    
    def get_effective_limit(self, limit_type: RateLimitType) -> int:
        """Get the effective limit after applying safety margin."""
        if limit_type == RateLimitType.SECOND:
            return int(self.requests_per_second * (1 - self.second_margin))
        elif limit_type == RateLimitType.MINUTE:
            return int(self.requests_per_minute * (1 - self.minute_margin))
        elif limit_type == RateLimitType.DAY:
            return int(self.requests_per_day * (1 - self.day_margin))
        return 0


class APICallRecord(BaseModel):
    """Record of an individual API call."""
    
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="Timestamp of the API call"
    )
    endpoint: str = Field(
        ...,
        description="API endpoint called"
    )
    method: str = Field(
        default="GET",
        description="HTTP method used"
    )
    success: bool = Field(
        default=True,
        description="Whether the call was successful"
    )
    response_time_ms: Optional[float] = Field(
        default=None,
        description="Response time in milliseconds"
    )
    status_code: Optional[int] = Field(
        default=None,
        description="HTTP status code"
    )
    
    class Config:
        """Pydantic model configuration."""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class RateLimitState(BaseModel):
    """Current state of rate limiting counters."""
    
    # Counters
    second_count: int = Field(
        default=0,
        description="Number of requests in the current second"
    )
    minute_count: int = Field(
        default=0,
        description="Number of requests in the current minute"
    )
    day_count: int = Field(
        default=0,
        description="Number of requests today"
    )
    
    # Timestamps for window tracking
    current_second: Optional[datetime] = Field(
        default=None,
        description="Start of current second window"
    )
    current_minute: Optional[datetime] = Field(
        default=None,
        description="Start of current minute window"
    )
    current_day: Optional[date] = Field(
        default=None,
        description="Current day for daily counter"
    )
    
    # Historical data
    recent_calls: List[APICallRecord] = Field(
        default_factory=list,
        description="Recent API calls (for debugging)"
    )
    
    # State tracking
    is_day_limit_reached: bool = Field(
        default=False,
        description="Whether daily limit has been reached"
    )
    last_rate_limit_error: Optional[datetime] = Field(
        default=None,
        description="Timestamp of last rate limit error"
    )
    
    def get_remaining_calls(self, limit_type: RateLimitType, config: RateLimitConfig) -> int:
        """Get remaining calls for the given limit type."""
        if limit_type == RateLimitType.SECOND:
            return max(0, config.requests_per_second - self.second_count)
        elif limit_type == RateLimitType.MINUTE:
            return max(0, config.requests_per_minute - self.minute_count)
        elif limit_type == RateLimitType.DAY:
            return max(0, config.requests_per_day - self.day_count)
        return 0
    
    def get_usage_percentage(self, limit_type: RateLimitType, config: RateLimitConfig) -> float:
        """Get usage percentage for the given limit type."""
        if limit_type == RateLimitType.SECOND:
            return (self.second_count / config.requests_per_second) * 100
        elif limit_type == RateLimitType.MINUTE:
            return (self.minute_count / config.requests_per_minute) * 100
        elif limit_type == RateLimitType.DAY:
            return (self.day_count / config.requests_per_day) * 100
        return 0.0
    
    def to_summary_dict(self, config: RateLimitConfig) -> dict:
        """Get a summary dictionary of the current state."""
        return {
            "second": {
                "count": self.second_count,
                "limit": config.requests_per_second,
                "remaining": self.get_remaining_calls(RateLimitType.SECOND, config),
                "usage_percent": round(self.get_usage_percentage(RateLimitType.SECOND, config), 2),
            },
            "minute": {
                "count": self.minute_count,
                "limit": config.requests_per_minute,
                "remaining": self.get_remaining_calls(RateLimitType.MINUTE, config),
                "usage_percent": round(self.get_usage_percentage(RateLimitType.MINUTE, config), 2),
            },
            "day": {
                "count": self.day_count,
                "limit": config.requests_per_day,
                "remaining": self.get_remaining_calls(RateLimitType.DAY, config),
                "usage_percent": round(self.get_usage_percentage(RateLimitType.DAY, config), 2),
                "is_limit_reached": self.is_day_limit_reached,
            },
            "current_day": str(self.current_day) if self.current_day else None,
        }
    
    class Config:
        """Pydantic model configuration."""
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            date: lambda v: v.isoformat(),
        }


class DailyRateLimitRecord(BaseModel):
    """Record of daily API usage for persistence."""
    
    record_date: date = Field(
        ...,
        description="Date of the record"
    )
    total_calls: int = Field(
        default=0,
        description="Total API calls made on this date"
    )
    successful_calls: int = Field(
        default=0,
        description="Successful API calls"
    )
    failed_calls: int = Field(
        default=0,
        description="Failed API calls"
    )
    rate_limit_errors: int = Field(
        default=0,
        description="Number of rate limit errors"
    )
    last_updated: datetime = Field(
        default_factory=datetime.utcnow,
        description="Last update timestamp"
    )
    
    class Config:
        """Pydantic model configuration."""
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            date: lambda v: v.isoformat(),
        }