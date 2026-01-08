"""
Configuration models for the Fyers SDK.
"""

from pydantic import BaseModel, Field, field_validator
from typing import Optional
import hashlib


class FyersConfig(BaseModel):
    """Configuration for the Fyers client."""
    
    client_id: str = Field(
        ...,
        description="App ID received after creating the app (e.g., 'TX4LY7JMLL-100')"
    )
    secret_key: str = Field(
        ...,
        description="App secret key"
    )
    redirect_uri: str = Field(
        default="https://trade.fyers.in/api-login/redirect-uri/index.html",
        description="Redirect URI for OAuth flow"
    )
    
    # API endpoints
    api_base_url: str = Field(
        default="https://api-t1.fyers.in/api/v3",
        description="Base URL for Fyers API v3"
    )
    data_api_base_url: str = Field(
        default="https://api-t1.fyers.in/data",
        description="Base URL for data API"
    )
    
    # Token storage
    token_file_path: Optional[str] = Field(
        default=None,
        description="File path to store tokens (optional)"
    )
    
    # Rate limit counter file
    rate_limit_file_path: Optional[str] = Field(
        default=None,
        description="File path to store rate limit counters (optional)"
    )
    
    # Logging
    log_level: str = Field(
        default="INFO",
        description="Logging level"
    )
    log_file: Optional[str] = Field(
        default=None,
        description="Log file path (optional)"
    )
    
    @field_validator("client_id")
    @classmethod
    def validate_client_id(cls, v: str) -> str:
        """Validate client ID format."""
        if not v or len(v) < 5:
            raise ValueError("Invalid client_id format")
        return v
    
    @field_validator("redirect_uri")
    @classmethod
    def validate_redirect_uri(cls, v: str) -> str:
        """Validate redirect URI format."""
        if not v.startswith("http://") and not v.startswith("https://"):
            raise ValueError("redirect_uri must start with http:// or https://")
        return v
    
    def get_app_id_hash(self) -> str:
        """
        Generate SHA-256 hash of client_id + secret_key.
        Required for token validation API.
        
        Returns:
            SHA-256 hash string
        """
        combined = f"{self.client_id}{self.secret_key}"
        return hashlib.sha256(combined.encode()).hexdigest()
    
    class Config:
        """Pydantic model configuration."""
        extra = "forbid"  # Disallow extra fields


class FyersEnvironment(BaseModel):
    """Environment-specific configuration."""
    
    is_production: bool = Field(
        default=False,
        description="Whether to use production environment"
    )
    
    @property
    def api_base_url(self) -> str:
        """Get API base URL based on environment."""
        # Fyers uses the same URL for both environments
        # but this could change in the future
        return "https://api-t1.fyers.in/api/v3"
    
    @property
    def auth_base_url(self) -> str:
        """Get authentication base URL."""
        return "https://api-t1.fyers.in/api/v3"