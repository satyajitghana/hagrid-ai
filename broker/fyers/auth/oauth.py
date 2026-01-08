"""
OAuth authentication flow for the Fyers SDK.

Implements the User Apps authentication flow:
1. Generate authorization URL
2. User logs in and gets redirected with auth_code
3. Validate auth_code to get access_token
4. Refresh token when needed
"""

import secrets
import webbrowser
from datetime import datetime, timedelta
from typing import Optional
from urllib.parse import urlencode, urlparse, parse_qs

import httpx

from broker.fyers.core.exceptions import (
    FyersAuthenticationError,
    FyersAPIError,
)
from broker.fyers.core.logger import get_logger
from broker.fyers.models.config import FyersConfig
from broker.fyers.models.auth import (
    TokenData,
    TokenResponse,
    ValidateAuthCodeRequest,
    RefreshTokenRequest,
)
from broker.fyers.auth.token_storage import TokenStorage, TokenManager

logger = get_logger("fyers.oauth")


class FyersOAuth:
    """
    OAuth authentication handler for Fyers API.
    
    Implements the complete OAuth2 flow for User Apps:
    - Generate authorization URL
    - Validate authorization code
    - Generate access token
    - Refresh access token
    """
    
    # API endpoints
    AUTH_URL = "https://api-t1.fyers.in/api/v3/generate-authcode"
    VALIDATE_AUTHCODE_URL = "https://api-t1.fyers.in/api/v3/validate-authcode"
    REFRESH_TOKEN_URL = "https://api-t1.fyers.in/api/v3/validate-refresh-token"
    
    def __init__(
        self,
        config: FyersConfig,
        token_storage: Optional[TokenStorage] = None,
    ):
        """
        Initialize the OAuth handler.
        
        Args:
            config: Fyers configuration
            token_storage: Optional token storage backend
        """
        self.config = config
        self.token_storage = token_storage
        self.token_manager = TokenManager(token_storage) if token_storage else None
        
        # State tracking for OAuth flow
        self._pending_state: Optional[str] = None
        
        logger.info(f"OAuth handler initialized for client: {config.client_id}")
    
    def generate_auth_url(self, state: Optional[str] = None) -> str:
        """
        Generate the authorization URL for the OAuth flow.
        
        Step 1 of the OAuth flow. User should be redirected to this URL
        to log in and authorize the application.
        
        Args:
            state: Optional state parameter for CSRF protection.
                   If not provided, a random state will be generated.
        
        Returns:
            Authorization URL string
        """
        if state is None:
            state = secrets.token_urlsafe(32)
        
        self._pending_state = state
        
        params = {
            "client_id": self.config.client_id,
            "redirect_uri": self.config.redirect_uri,
            "response_type": "code",
            "state": state,
        }
        
        auth_url = f"{self.AUTH_URL}?{urlencode(params)}"
        
        logger.info(f"Generated auth URL with state: {state[:8]}...")
        logger.debug(f"Full auth URL: {auth_url}")
        
        return auth_url
    
    def open_auth_url(self, state: Optional[str] = None) -> str:
        """
        Generate and open the authorization URL in the default browser.
        
        Args:
            state: Optional state parameter
            
        Returns:
            The authorization URL that was opened
        """
        auth_url = self.generate_auth_url(state)
        
        logger.info("Opening authorization URL in browser...")
        webbrowser.open(auth_url)
        
        return auth_url
    
    def parse_redirect_url(self, redirect_url: str) -> tuple[str, str]:
        """
        Parse the redirect URL to extract auth_code and state.
        
        Args:
            redirect_url: The full redirect URL from the OAuth callback
            
        Returns:
            Tuple of (auth_code, state)
            
        Raises:
            FyersAuthenticationError: If parsing fails or auth_code is missing
        """
        try:
            parsed = urlparse(redirect_url)
            params = parse_qs(parsed.query)
            
            # Get auth_code
            auth_code = params.get("auth_code", params.get("code", [None]))[0]
            if not auth_code:
                # Check if there's an error
                error = params.get("error", [None])[0]
                error_desc = params.get("error_description", ["Unknown error"])[0]
                if error:
                    raise FyersAuthenticationError(
                        f"OAuth error: {error} - {error_desc}"
                    )
                raise FyersAuthenticationError("No auth_code found in redirect URL")
            
            # Get state
            state = params.get("state", [None])[0]
            
            logger.debug(f"Parsed auth_code: {auth_code[:20]}..., state: {state}")
            
            return auth_code, state
            
        except FyersAuthenticationError:
            raise
        except Exception as e:
            logger.error(f"Failed to parse redirect URL: {e}")
            raise FyersAuthenticationError(f"Failed to parse redirect URL: {e}")
    
    def verify_state(self, state: str) -> bool:
        """
        Verify the state parameter matches the pending state.
        
        Args:
            state: State from the redirect URL
            
        Returns:
            True if state matches, False otherwise
        """
        if self._pending_state is None:
            logger.warning("No pending state to verify against")
            return True  # No state tracking, assume valid
        
        is_valid = state == self._pending_state
        
        if not is_valid:
            logger.warning(f"State mismatch: expected {self._pending_state[:8]}..., got {state[:8]}...")
        
        return is_valid
    
    async def validate_auth_code(self, auth_code: str) -> TokenData:
        """
        Validate the authorization code and get access token.
        
        Step 2 of the OAuth flow. Exchanges the auth_code for an access_token.
        
        Args:
            auth_code: The authorization code from Step 1
            
        Returns:
            TokenData with access_token and refresh_token
            
        Raises:
            FyersAuthenticationError: If validation fails
        """
        logger.info("Validating authorization code...")
        
        # Prepare request
        request_data = ValidateAuthCodeRequest(
            grant_type="authorization_code",
            appIdHash=self.config.get_app_id_hash(),
            code=auth_code,
        )
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.VALIDATE_AUTHCODE_URL,
                    json=request_data.model_dump(),
                    headers={"Content-Type": "application/json"},
                    timeout=30.0,
                )
                
                response_data = response.json()
                logger.debug(f"Validate auth code response: {response_data}")
                
                # Parse response
                token_response = TokenResponse(**response_data)
                
                if not token_response.is_success():
                    raise FyersAuthenticationError(
                        f"Failed to validate auth code: {token_response.message}",
                        code=token_response.code,
                    )
                
                # Create TokenData
                token_data = TokenData(
                    access_token=token_response.access_token,
                    refresh_token=token_response.refresh_token,
                    created_at=datetime.utcnow(),
                    # Fyers tokens typically expire at end of trading day
                    # or after ~24 hours
                    expires_at=datetime.utcnow() + timedelta(hours=24),
                )
                
                # Store token if storage is configured
                if self.token_manager:
                    await self.token_manager.set_token(token_data)
                
                logger.info("Successfully obtained access token")
                
                # Clear pending state
                self._pending_state = None
                
                return token_data
                
        except httpx.RequestError as e:
            logger.error(f"Network error during auth code validation: {e}")
            raise FyersAuthenticationError(f"Network error: {e}")
        except Exception as e:
            if isinstance(e, FyersAuthenticationError):
                raise
            logger.error(f"Error validating auth code: {e}")
            raise FyersAuthenticationError(f"Failed to validate auth code: {e}")
    
    async def refresh_access_token(
        self,
        refresh_token: str,
        pin: str,
    ) -> TokenData:
        """
        Refresh the access token using the refresh token.
        
        Args:
            refresh_token: The refresh token from previous authentication
            pin: User's PIN
            
        Returns:
            New TokenData with fresh access_token
            
        Raises:
            FyersAuthenticationError: If refresh fails
        """
        logger.info("Refreshing access token...")
        
        request_data = RefreshTokenRequest(
            grant_type="refresh_token",
            appIdHash=self.config.get_app_id_hash(),
            refresh_token=refresh_token,
            pin=pin,
        )
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.REFRESH_TOKEN_URL,
                    json=request_data.model_dump(),
                    headers={"Content-Type": "application/json"},
                    timeout=30.0,
                )
                
                response_data = response.json()
                logger.debug(f"Refresh token response: {response_data}")
                
                # Parse response
                token_response = TokenResponse(**response_data)
                
                if not token_response.is_success():
                    raise FyersAuthenticationError(
                        f"Failed to refresh token: {token_response.message}",
                        code=token_response.code,
                    )
                
                # Create new TokenData
                token_data = TokenData(
                    access_token=token_response.access_token,
                    refresh_token=refresh_token,  # Keep original refresh token
                    created_at=datetime.utcnow(),
                    expires_at=datetime.utcnow() + timedelta(hours=24),
                )
                
                # Store token if storage is configured
                if self.token_manager:
                    await self.token_manager.set_token(token_data)
                
                logger.info("Successfully refreshed access token")
                return token_data
                
        except httpx.RequestError as e:
            logger.error(f"Network error during token refresh: {e}")
            raise FyersAuthenticationError(f"Network error: {e}")
        except Exception as e:
            if isinstance(e, FyersAuthenticationError):
                raise
            logger.error(f"Error refreshing token: {e}")
            raise FyersAuthenticationError(f"Failed to refresh token: {e}")
    
    async def authenticate_with_redirect(
        self,
        redirect_url: str,
        verify_state: bool = True,
    ) -> TokenData:
        """
        Complete authentication using the redirect URL from OAuth callback.
        
        Convenience method that parses the redirect URL and validates the auth code.
        
        Args:
            redirect_url: The full redirect URL from OAuth callback
            verify_state: Whether to verify the state parameter
            
        Returns:
            TokenData with access_token
            
        Raises:
            FyersAuthenticationError: If authentication fails
        """
        # Parse redirect URL
        auth_code, state = self.parse_redirect_url(redirect_url)
        
        # Verify state if requested
        if verify_state and state:
            if not self.verify_state(state):
                raise FyersAuthenticationError(
                    "State verification failed. Possible CSRF attack."
                )
        
        # Validate auth code
        return await self.validate_auth_code(auth_code)
    
    async def get_token(self) -> Optional[TokenData]:
        """
        Get the current stored token.
        
        Returns:
            TokenData if available, None otherwise
        """
        if not self.token_manager:
            logger.warning("No token storage configured")
            return None
        
        try:
            return await self.token_manager.get_token()
        except Exception:
            return None
    
    async def is_authenticated(self) -> bool:
        """
        Check if there's a valid authentication token.
        
        Returns:
            True if authenticated with valid token
        """
        if not self.token_manager:
            return False
        
        return await self.token_manager.has_valid_token()
    
    async def logout(self) -> None:
        """Clear stored authentication tokens."""
        if self.token_manager:
            await self.token_manager.clear_token()
            logger.info("Logged out and cleared tokens")


# Convenience functions for interactive OAuth flow
async def interactive_login(
    config: FyersConfig,
    token_storage: Optional[TokenStorage] = None,
) -> TokenData:
    """
    Perform interactive OAuth login.
    
    Opens browser for login and prompts for the redirect URL.
    
    Args:
        config: Fyers configuration
        token_storage: Optional token storage
        
    Returns:
        TokenData with access_token
    """
    oauth = FyersOAuth(config, token_storage)
    
    # Generate and open auth URL
    auth_url = oauth.open_auth_url()
    
    print("\n" + "=" * 60)
    print("FYERS AUTHENTICATION")
    print("=" * 60)
    print(f"\nAuthorization URL has been opened in your browser.")
    print(f"\nIf it didn't open automatically, visit:\n{auth_url}")
    print("\nAfter logging in, you will be redirected to a URL.")
    print("Please copy and paste the FULL redirect URL below.\n")
    
    # Get redirect URL from user
    redirect_url = input("Paste the redirect URL here: ").strip()
    
    # Complete authentication
    token_data = await oauth.authenticate_with_redirect(redirect_url)
    
    print("\n✓ Authentication successful!")
    print(f"Access token: {token_data.access_token[:30]}...")
    
    return token_data