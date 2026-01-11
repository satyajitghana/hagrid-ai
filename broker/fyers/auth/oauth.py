"""
OAuth authentication flow for the Fyers SDK.

Implements the User Apps authentication flow:
1. Generate authorization URL
2. User logs in and gets redirected with auth_code
3. Validate auth_code to get access_token
4. Refresh token when needed
"""

import asyncio
import secrets
import webbrowser
from datetime import datetime, timedelta
from typing import Optional, Callable
from urllib.parse import urlencode, urlparse, parse_qs
from http.server import BaseHTTPRequestHandler, HTTPServer
import threading
import socket

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


class CallbackHTTPHandler(BaseHTTPRequestHandler):
    """HTTP handler for OAuth callback."""
    
    # Class variable to store the redirect URL
    redirect_url: Optional[str] = None
    callback_received: Optional[Callable[[], None]] = None
    
    def do_GET(self):
        """Handle GET request from OAuth redirect."""
        # Store the full URL
        full_url = f"http://{self.headers.get('Host')}{self.path}"
        CallbackHTTPHandler.redirect_url = full_url
        
        # Send response
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        
        # Check if auth_code exists in the URL
        parsed = urlparse(full_url)
        params = parse_qs(parsed.query)
        
        if "auth_code" in params or "code" in params:
            response = """
            <!DOCTYPE html>
            <html>
            <head>
                <title>Authentication Successful - Fyers</title>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <style>
                    * {
                        margin: 0;
                        padding: 0;
                        box-sizing: border-box;
                    }
                    body {
                        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
                        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        min-height: 100vh;
                        padding: 20px;
                    }
                    .container {
                        background: white;
                        border-radius: 20px;
                        box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
                        padding: 60px 40px;
                        text-align: center;
                        max-width: 500px;
                        width: 100%;
                        animation: slideIn 0.5s ease-out;
                    }
                    @keyframes slideIn {
                        from {
                            opacity: 0;
                            transform: translateY(-30px);
                        }
                        to {
                            opacity: 1;
                            transform: translateY(0);
                        }
                    }
                    .checkmark {
                        width: 80px;
                        height: 80px;
                        border-radius: 50%;
                        background: #10b981;
                        margin: 0 auto 30px;
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        animation: scaleIn 0.5s ease-out 0.2s both;
                    }
                    @keyframes scaleIn {
                        from {
                            transform: scale(0);
                        }
                        to {
                            transform: scale(1);
                        }
                    }
                    .checkmark svg {
                        width: 50px;
                        height: 50px;
                        stroke: white;
                        stroke-width: 3;
                        fill: none;
                        animation: draw 0.5s ease-out 0.4s both;
                    }
                    @keyframes draw {
                        from {
                            stroke-dasharray: 100;
                            stroke-dashoffset: 100;
                        }
                        to {
                            stroke-dasharray: 100;
                            stroke-dashoffset: 0;
                        }
                    }
                    h1 {
                        color: #1f2937;
                        font-size: 32px;
                        font-weight: 700;
                        margin-bottom: 15px;
                    }
                    p {
                        color: #6b7280;
                        font-size: 18px;
                        line-height: 1.6;
                        margin-bottom: 30px;
                    }
                    .info {
                        background: #f3f4f6;
                        border-radius: 10px;
                        padding: 20px;
                        margin-top: 30px;
                    }
                    .info p {
                        font-size: 14px;
                        color: #6b7280;
                        margin: 0;
                    }
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="checkmark">
                        <svg viewBox="0 0 52 52">
                            <polyline points="14 27 22 35 38 19"/>
                        </svg>
                    </div>
                    <h1>Authentication Successful!</h1>
                    <p>You have been successfully authenticated with Fyers.</p>
                    <p>You can now close this window and return to your application.</p>
                    <div class="info">
                        <p>🔒 Your credentials have been securely processed</p>
                    </div>
                </div>
            </body>
            </html>
            """
        else:
            error = params.get("error", ["Unknown error"])[0]
            error_desc = params.get("error_description", [""])[0]
            response = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>Authentication Failed - Fyers</title>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <style>
                    * {{
                        margin: 0;
                        padding: 0;
                        box-sizing: border-box;
                    }}
                    body {{
                        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
                        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        min-height: 100vh;
                        padding: 20px;
                    }}
                    .container {{
                        background: white;
                        border-radius: 20px;
                        box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
                        padding: 60px 40px;
                        text-align: center;
                        max-width: 500px;
                        width: 100%;
                        animation: slideIn 0.5s ease-out;
                    }}
                    @keyframes slideIn {{
                        from {{
                            opacity: 0;
                            transform: translateY(-30px);
                        }}
                        to {{
                            opacity: 1;
                            transform: translateY(0);
                        }}
                    }}
                    .error-icon {{
                        width: 80px;
                        height: 80px;
                        border-radius: 50%;
                        background: #ef4444;
                        margin: 0 auto 30px;
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        animation: scaleIn 0.5s ease-out 0.2s both;
                    }}
                    @keyframes scaleIn {{
                        from {{
                            transform: scale(0);
                        }}
                        to {{
                            transform: scale(1);
                        }}
                    }}
                    .error-icon svg {{
                        width: 50px;
                        height: 50px;
                        stroke: white;
                        stroke-width: 3;
                        fill: none;
                    }}
                    h1 {{
                        color: #1f2937;
                        font-size: 32px;
                        font-weight: 700;
                        margin-bottom: 15px;
                    }}
                    p {{
                        color: #6b7280;
                        font-size: 18px;
                        line-height: 1.6;
                        margin-bottom: 20px;
                    }}
                    .error-details {{
                        background: #fee2e2;
                        border-left: 4px solid #ef4444;
                        border-radius: 8px;
                        padding: 20px;
                        margin-top: 30px;
                        text-align: left;
                    }}
                    .error-details p {{
                        font-size: 14px;
                        color: #991b1b;
                        margin: 5px 0;
                    }}
                    .error-details strong {{
                        color: #7f1d1d;
                    }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="error-icon">
                        <svg viewBox="0 0 52 52">
                            <line x1="16" y1="16" x2="36" y2="36"/>
                            <line x1="36" y1="16" x2="16" y2="36"/>
                        </svg>
                    </div>
                    <h1>Authentication Failed</h1>
                    <p>We encountered an error during the authentication process.</p>
                    <div class="error-details">
                        <p><strong>Error:</strong> {error}</p>
                        <p><strong>Details:</strong> {error_desc}</p>
                    </div>
                    <p style="margin-top: 30px; font-size: 14px;">Please close this window and try again.</p>
                </div>
            </body>
            </html>
            """
        
        self.wfile.write(response.encode())
        
        # Signal that callback was received
        if CallbackHTTPHandler.callback_received:
            CallbackHTTPHandler.callback_received()
    
    def log_message(self, format, *args):
        """Suppress default logging."""
        pass


def extract_port_from_url(url: str) -> int:
    """
    Extract port number from a URL.
    
    Args:
        url: URL string (e.g., "http://127.0.0.1:9000/")
        
    Returns:
        Port number
        
    Raises:
        ValueError: If port cannot be extracted
    """
    parsed = urlparse(url)
    
    if parsed.port is not None:
        return parsed.port
    
    # Default ports
    if parsed.scheme == "http":
        return 80
    elif parsed.scheme == "https":
        return 443
    
    raise ValueError(f"Cannot extract port from URL: {url}")


def check_port_available(host: str, port: int) -> None:
    """
    Check if a port is available for binding.
    
    Args:
        host: Host address
        port: Port number
        
    Raises:
        RuntimeError: If port is already in use
    """
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.bind((host, port))
        sock.close()
    except OSError as e:
        raise RuntimeError(
            f"Port {port} is already in use on {host}. "
            f"Please ensure no other application is using this port, "
            f"or update your redirect_uri in Fyers dashboard to use a different port."
        ) from e


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
    
    async def authenticate_with_callback_server(
        self,
        port: Optional[int] = None,
        host: Optional[str] = None,
        timeout: int = 300,
    ) -> TokenData:
        """
        Authenticate using a local HTTP callback server.
        
        This method starts a local HTTP server, opens the browser for login,
        and automatically captures the OAuth redirect. No manual copy-paste needed!
        
        IMPORTANT: Your redirect_uri must be registered in Fyers dashboard beforehand.
        The server will use the exact host/port from your configured redirect_uri.
        
        Args:
            port: Port number for callback server. If None, extracts from redirect_uri
            host: Host address for callback server. If None, extracts from redirect_uri
            timeout: Timeout in seconds to wait for callback (default: 300)
            
        Returns:
            TokenData with access_token
            
        Raises:
            FyersAuthenticationError: If authentication fails or times out
            RuntimeError: If the specified port is already in use
            ValueError: If port/host cannot be extracted from redirect_uri
            
        Example:
            ```python
            # Configure with localhost redirect (must match Fyers dashboard)
            config = FyersConfig(
                client_id="YOUR_CLIENT_ID",
                secret_key="YOUR_SECRET",
                redirect_uri="http://127.0.0.1:9000/"
            )
            oauth = FyersOAuth(config)
            
            # Authenticate automatically - uses port/host from redirect_uri
            token_data = await oauth.authenticate_with_callback_server()
            ```
        """
        # Extract port and host from redirect_uri if not provided
        parsed_redirect = urlparse(self.config.redirect_uri)
        
        if port is None:
            port = extract_port_from_url(self.config.redirect_uri)
            logger.info(f"Using port {port} from redirect_uri")
        
        if host is None:
            host = parsed_redirect.hostname or "127.0.0.1"
            logger.info(f"Using host {host} from redirect_uri")
        
        # Verify the port is available before starting
        check_port_available(host, port)
        
        # Verify redirect_uri matches the server we're starting
        expected_redirect = f"{parsed_redirect.scheme}://{host}:{port}{parsed_redirect.path}"
        if self.config.redirect_uri != expected_redirect:
            logger.warning(
                f"redirect_uri mismatch! Config has '{self.config.redirect_uri}' "
                f"but server will run at '{expected_redirect}'"
            )
        
        # Reset callback handler state
        CallbackHTTPHandler.redirect_url = None
        callback_event = threading.Event()
        CallbackHTTPHandler.callback_received = callback_event.set
        
        # Create and start HTTP server in background thread
        server = HTTPServer((host, port), CallbackHTTPHandler)
        server_thread = threading.Thread(target=server.serve_forever, daemon=True)
        server_thread.start()
        
        logger.info(f"Started callback server on {host}:{port}")
        
        try:
            # Generate and open auth URL
            auth_url = self.open_auth_url()
            
            print("\n" + "=" * 60)
            print("FYERS AUTHENTICATION")
            print("=" * 60)
            print(f"\nAuthorization URL has been opened in your browser.")
            print(f"\nIf it didn't open automatically, visit:\n{auth_url}")
            print(f"\nWaiting for OAuth callback on {host}:{port}...")
            print("(This window will automatically continue once you authorize)")
            
            # Wait for callback with timeout
            if not callback_event.wait(timeout=timeout):
                raise FyersAuthenticationError(
                    f"Authentication timed out after {timeout} seconds. "
                    "Please try again."
                )
            
            # Get the redirect URL captured by the server
            redirect_url = CallbackHTTPHandler.redirect_url
            
            if not redirect_url:
                raise FyersAuthenticationError("No redirect URL captured")
            
            logger.info("Received OAuth callback")
            
            # Complete authentication
            token_data = await self.authenticate_with_redirect(redirect_url)
            
            print("\n✓ Authentication successful!")
            logger.info("Access token obtained and saved")
            
            return token_data
            
        finally:
            # Shutdown the server
            server.shutdown()
            server.server_close()
            logger.info("Callback server stopped")


# Convenience functions for interactive OAuth flow
async def interactive_login(
    config: FyersConfig,
    token_storage: Optional[TokenStorage] = None,
    use_callback_server: bool = True,
    callback_port: Optional[int] = None,
) -> TokenData:
    """
    Perform interactive OAuth login.
    
    By default, uses automatic callback server to capture OAuth redirect.
    Can fall back to manual URL input if use_callback_server=False.
    
    Args:
        config: Fyers configuration
        token_storage: Optional token storage
        use_callback_server: If True, automatically capture redirect (default: True)
        callback_port: Port for callback server (auto-selected if None)
        
    Returns:
        TokenData with access_token
        
    Example:
        ```python
        # Automatic (default) - no manual copy-paste needed
        token = await interactive_login(config)
        
        # Manual - requires copy-paste
        token = await interactive_login(config, use_callback_server=False)
        ```
    """
    oauth = FyersOAuth(config, token_storage)
    
    # Try automatic callback server first
    if use_callback_server:
        try:
            return await oauth.authenticate_with_callback_server(port=callback_port)
        except Exception as e:
            logger.warning(f"Callback server failed: {e}. Falling back to manual input.")
            print(f"\n⚠ Automatic authentication failed: {e}")
            print("Falling back to manual URL input...\n")
    
    # Fall back to manual input
    auth_url = oauth.open_auth_url()
    
    print("\n" + "=" * 60)
    print("FYERS AUTHENTICATION (Manual)")
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
    logger.info("Access token obtained and saved")
    
    return token_data