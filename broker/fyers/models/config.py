"""
Configuration models for the Fyers SDK.
"""

import os
from pydantic import BaseModel, Field, field_validator, model_validator
from typing import Optional
import hashlib


class FyersConfig(BaseModel):
    """
    Configuration for the Fyers client.
    
    Supports loading credentials from environment variables:
    - FYERS_CLIENT_ID: App ID
    - FYERS_SECRET_KEY: App secret
    - FYERS_REDIRECT_URI: OAuth redirect URI (optional)
    - FYERS_TOKEN_FILE: Token file path (optional)
    
    Example:
        ```python
        # From environment variables
        config = FyersConfig.from_env()
        
        # Or explicitly
        config = FyersConfig(
            client_id="TX4LY7JMLL-100",
            secret_key="YOUR_SECRET",
        )
        ```
    """
    
    client_id: str = Field(
        default="",
        description="App ID received after creating the app (e.g., 'TX4LY7JMLL-100')"
    )
    secret_key: str = Field(
        default="",
        description="App secret key"
    )
    redirect_uri: str = Field(
        default="http://127.0.0.1:9000/",
        description="Redirect URI for OAuth flow (default: localhost for easy local auth)"
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
    
    @model_validator(mode="after")
    def validate_credentials(self) -> "FyersConfig":
        """Ensure credentials are provided."""
        if not self.client_id or not self.secret_key:
            raise ValueError(
                "client_id and secret_key are required. "
                "Provide them directly or set FYERS_CLIENT_ID and FYERS_SECRET_KEY environment variables."
            )
        return self
    
    @classmethod
    def from_env(
        cls,
        token_file: Optional[str] = None,
        rate_limit_file: Optional[str] = None,
    ) -> "FyersConfig":
        """
        Create configuration from environment variables.
        
        Environment variables:
        - FYERS_CLIENT_ID: App ID (required)
        - FYERS_SECRET_KEY: App secret (required)
        - FYERS_REDIRECT_URI: OAuth redirect URI (optional)
        - FYERS_TOKEN_FILE: Token file path (optional)
        
        Args:
            token_file: Override for token file path
            rate_limit_file: Override for rate limit file path
            
        Returns:
            FyersConfig instance
            
        Raises:
            ValueError: If required environment variables are not set
            
        Example:
            ```python
            # Set environment variables first:
            # export FYERS_CLIENT_ID="TX4LY7JMLL-100"
            # export FYERS_SECRET_KEY="YOUR_SECRET"
            
            config = FyersConfig.from_env()
            client = FyersClient(config)
            ```
        """
        client_id = os.environ.get("FYERS_CLIENT_ID", "")
        secret_key = os.environ.get("FYERS_SECRET_KEY", "")
        redirect_uri = os.environ.get("FYERS_REDIRECT_URI", "http://127.0.0.1:9000/")
        env_token_file = os.environ.get("FYERS_TOKEN_FILE")
        
        return cls(
            client_id=client_id,
            secret_key=secret_key,
            redirect_uri=redirect_uri,
            token_file_path=token_file or env_token_file,
            rate_limit_file_path=rate_limit_file,
        )
    
    def get_app_id_hash(self) -> str:
        """
        Generate SHA-256 hash of client_id:secret_key.
        Required for token validation API.
        
        Note: Fyers requires the format to be 'client_id:secret_key' with colon separator.
        
        Returns:
            SHA-256 hash string
        """
        combined = f"{self.client_id}:{self.secret_key}"
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