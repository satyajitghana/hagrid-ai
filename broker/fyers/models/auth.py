"""
Authentication models for the Fyers SDK.
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class TokenData(BaseModel):
    """Model for storing token data."""
    
    access_token: str = Field(
        ...,
        description="Access token for API requests"
    )
    refresh_token: Optional[str] = Field(
        default=None,
        description="Refresh token for generating new access tokens"
    )
    token_type: str = Field(
        default="Bearer",
        description="Token type (usually 'Bearer')"
    )
    expires_at: Optional[datetime] = Field(
        default=None,
        description="Token expiration timestamp"
    )
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Token creation timestamp"
    )
    
    def is_expired(self) -> bool:
        """Check if the access token has expired."""
        if self.expires_at is None:
            # Assume valid for ~24 hours if no expiration set
            # Fyers tokens typically expire at end of trading day
            return False
        return datetime.utcnow() > self.expires_at
    
    def get_auth_header(self) -> str:
        """Get the authorization header value."""
        return f"{self.access_token}"
    
    def __str__(self) -> str:
        """Safe string representation that doesn't expose tokens."""
        return (
            f"TokenData("
            f"access_token='***REDACTED***', "
            f"has_refresh_token={self.refresh_token is not None}, "
            f"expired={self.is_expired()}, "
            f"created_at={self.created_at.isoformat() if self.created_at else None}"
            f")"
        )
    
    def __repr__(self) -> str:
        """Safe repr that doesn't expose tokens."""
        return self.__str__()
    
    class Config:
        """Pydantic model configuration."""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class AuthCodeResponse(BaseModel):
    """Response from the authorization code redirect."""
    
    s: str = Field(
        ...,
        description="Status: 'ok' or 'error'"
    )
    code: Optional[int] = Field(
        default=None,
        description="Response code"
    )
    message: Optional[str] = Field(
        default=None,
        description="Response message"
    )
    auth_code: Optional[str] = Field(
        default=None,
        description="Authorization code for token generation"
    )
    state: Optional[str] = Field(
        default=None,
        description="State parameter from the request"
    )
    
    def is_success(self) -> bool:
        """Check if the response indicates success."""
        return self.s == "ok"


class TokenResponse(BaseModel):
    """Response from the token validation API."""
    
    s: str = Field(
        ...,
        description="Status: 'ok' or 'error'"
    )
    code: int = Field(
        ...,
        description="Response code"
    )
    message: Optional[str] = Field(
        default="",
        description="Response message"
    )
    access_token: Optional[str] = Field(
        default=None,
        description="Access token for API requests"
    )
    refresh_token: Optional[str] = Field(
        default=None,
        description="Refresh token for generating new access tokens"
    )
    
    def is_success(self) -> bool:
        """Check if the response indicates success."""
        return self.s == "ok" and self.code == 200


class RefreshTokenRequest(BaseModel):
    """Request body for refreshing access token."""
    
    grant_type: str = Field(
        default="refresh_token",
        description="Grant type (always 'refresh_token')"
    )
    appIdHash: str = Field(
        ...,
        description="SHA-256 hash of client_id + secret_key"
    )
    refresh_token: str = Field(
        ...,
        description="Refresh token from previous token response"
    )
    pin: str = Field(
        ...,
        description="User's PIN"
    )


class ValidateAuthCodeRequest(BaseModel):
    """Request body for validating authorization code."""
    
    grant_type: str = Field(
        default="authorization_code",
        description="Grant type (always 'authorization_code')"
    )
    appIdHash: str = Field(
        ...,
        description="SHA-256 hash of client_id + secret_key"
    )
    code: str = Field(
        ...,
        description="Authorization code from Step 1"
    )


class AuthState(BaseModel):
    """Model to track authentication state."""
    
    is_authenticated: bool = Field(
        default=False,
        description="Whether the user is authenticated"
    )
    token_data: Optional[TokenData] = Field(
        default=None,
        description="Current token data"
    )
    last_auth_time: Optional[datetime] = Field(
        default=None,
        description="Last successful authentication time"
    )
    auth_attempts: int = Field(
        default=0,
        description="Number of authentication attempts"
    )
    
    def mark_authenticated(self, token_data: TokenData) -> None:
        """Mark the user as authenticated with the given token."""
        self.is_authenticated = True
        self.token_data = token_data
        self.last_auth_time = datetime.utcnow()
        self.auth_attempts = 0
    
    def mark_unauthenticated(self) -> None:
        """Mark the user as unauthenticated."""
        self.is_authenticated = False
        self.token_data = None
    
    def increment_attempts(self) -> None:
        """Increment the authentication attempts counter."""
        self.auth_attempts += 1