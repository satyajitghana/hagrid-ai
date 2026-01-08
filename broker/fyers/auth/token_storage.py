"""
Token storage for the Fyers SDK.

Provides mechanisms to store and retrieve tokens securely.
"""

import json
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import Optional

from broker.fyers.core.exceptions import FyersTokenNotFoundError
from broker.fyers.core.logger import get_logger
from broker.fyers.models.auth import TokenData

logger = get_logger("fyers.token_storage")


class TokenStorage(ABC):
    """Abstract base class for token storage."""
    
    @abstractmethod
    async def save_token(self, token_data: TokenData) -> None:
        """Save token data."""
        pass
    
    @abstractmethod
    async def load_token(self) -> Optional[TokenData]:
        """Load token data."""
        pass
    
    @abstractmethod
    async def delete_token(self) -> None:
        """Delete stored token."""
        pass
    
    @abstractmethod
    async def has_token(self) -> bool:
        """Check if a token exists."""
        pass


class FileTokenStorage(TokenStorage):
    """
    File-based token storage.
    
    Stores tokens in a JSON file on disk.
    """
    
    def __init__(self, file_path: str):
        """
        Initialize file-based token storage.
        
        Args:
            file_path: Path to the token file
        """
        self.file_path = Path(file_path)
        logger.debug(f"Initialized file token storage at: {self.file_path}")
    
    async def save_token(self, token_data: TokenData) -> None:
        """
        Save token data to file.
        
        Args:
            token_data: Token data to save
        """
        try:
            # Ensure directory exists
            self.file_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Convert to dict with datetime serialization
            data = token_data.model_dump(mode="json")
            
            with open(self.file_path, "w") as f:
                json.dump(data, f, indent=2, default=str)
            
            logger.info(f"Token saved to {self.file_path}")
            
        except Exception as e:
            logger.error(f"Failed to save token: {e}")
            raise
    
    async def load_token(self) -> Optional[TokenData]:
        """
        Load token data from file.
        
        Returns:
            TokenData if found, None otherwise
        """
        if not self.file_path.exists():
            logger.debug(f"Token file not found: {self.file_path}")
            return None
        
        try:
            with open(self.file_path, "r") as f:
                data = json.load(f)
            
            # Parse datetime fields
            if data.get("expires_at"):
                data["expires_at"] = datetime.fromisoformat(data["expires_at"])
            if data.get("created_at"):
                data["created_at"] = datetime.fromisoformat(data["created_at"])
            
            token_data = TokenData(**data)
            logger.debug("Token loaded from file")
            return token_data
            
        except (json.JSONDecodeError, ValueError) as e:
            logger.warning(f"Failed to parse token file: {e}")
            return None
        except Exception as e:
            logger.error(f"Failed to load token: {e}")
            return None
    
    async def delete_token(self) -> None:
        """Delete the token file."""
        if self.file_path.exists():
            self.file_path.unlink()
            logger.info(f"Token deleted from {self.file_path}")
        else:
            logger.debug("No token file to delete")
    
    async def has_token(self) -> bool:
        """Check if a token file exists."""
        return self.file_path.exists()


class MemoryTokenStorage(TokenStorage):
    """
    In-memory token storage.
    
    Stores tokens in memory. Useful for testing or temporary sessions.
    """
    
    def __init__(self):
        """Initialize in-memory token storage."""
        self._token_data: Optional[TokenData] = None
        logger.debug("Initialized in-memory token storage")
    
    async def save_token(self, token_data: TokenData) -> None:
        """Save token data in memory."""
        self._token_data = token_data
        logger.debug("Token saved in memory")
    
    async def load_token(self) -> Optional[TokenData]:
        """Load token data from memory."""
        return self._token_data
    
    async def delete_token(self) -> None:
        """Delete token from memory."""
        self._token_data = None
        logger.debug("Token deleted from memory")
    
    async def has_token(self) -> bool:
        """Check if a token exists in memory."""
        return self._token_data is not None


class TokenManager:
    """
    Token manager for handling token lifecycle.
    
    Provides methods to get, refresh, and validate tokens.
    """
    
    def __init__(self, storage: TokenStorage):
        """
        Initialize token manager.
        
        Args:
            storage: Token storage backend
        """
        self.storage = storage
        self._cached_token: Optional[TokenData] = None
    
    async def get_token(self, force_reload: bool = False) -> TokenData:
        """
        Get the current valid token.
        
        Args:
            force_reload: Force reload from storage
            
        Returns:
            Valid token data
            
        Raises:
            FyersTokenNotFoundError: If no valid token is found
        """
        if not force_reload and self._cached_token:
            if not self._cached_token.is_expired():
                return self._cached_token
        
        token = await self.storage.load_token()
        
        if not token:
            raise FyersTokenNotFoundError("No token found in storage")
        
        if token.is_expired():
            raise FyersTokenNotFoundError("Token has expired")
        
        self._cached_token = token
        return token
    
    async def set_token(self, token_data: TokenData) -> None:
        """
        Set and store a new token.
        
        Args:
            token_data: Token data to store
        """
        await self.storage.save_token(token_data)
        self._cached_token = token_data
    
    async def clear_token(self) -> None:
        """Clear the stored token."""
        await self.storage.delete_token()
        self._cached_token = None
    
    async def has_valid_token(self) -> bool:
        """Check if a valid (non-expired) token exists."""
        try:
            token = await self.get_token()
            return not token.is_expired()
        except FyersTokenNotFoundError:
            return False
    
    def get_auth_header(self) -> Optional[str]:
        """Get the authorization header value if token is cached."""
        if self._cached_token and not self._cached_token.is_expired():
            return self._cached_token.get_auth_header()
        return None