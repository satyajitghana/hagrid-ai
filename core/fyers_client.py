"""
Shared Fyers client initialization for all agents.

This module provides a singleton FyersClient instance that is shared
across all agents to avoid creating multiple client instances.

The client automatically loads saved tokens on initialization.
"""

import asyncio
import logging
from typing import Optional
from broker.fyers import FyersClient, FyersConfig, FyersToolkit
from core.config import get_settings

logger = logging.getLogger(__name__)

_client: Optional[FyersClient] = None
_initialized: bool = False


def get_fyers_client() -> FyersClient:
    """
    Get the shared FyersClient instance.

    Creates a new client on first call, reuses existing client on subsequent calls.
    The client is configured from environment/settings and automatically
    loads saved tokens if available.

    Returns:
        FyersClient: Configured client with token loaded if available
    """
    global _client, _initialized

    if _client is None:
        settings = get_settings()
        config = FyersConfig(
            client_id=settings.FYERS_CLIENT_ID,
            secret_key=settings.FYERS_SECRET_KEY,
            token_file_path=settings.FYERS_TOKEN_FILE,
        )
        _client = FyersClient(config)
        logger.debug(f"FyersClient created with token file: {settings.FYERS_TOKEN_FILE}")

    # Try to load saved token if not already initialized
    if not _initialized and _client is not None:
        _initialized = True
        try:
            # Load saved token synchronously
            # This validates the token by calling profile API
            loaded = asyncio.run(_client.load_saved_token())
            if loaded:
                logger.info(f"Fyers token loaded successfully for {_client.user_name}")
            else:
                logger.warning("No valid Fyers token found. Run: python -m scripts fyers login")
        except RuntimeError as e:
            # Already in an async context - this shouldn't happen during import
            logger.warning(f"Cannot load token synchronously (async context): {e}")
        except Exception as e:
            # Token load failed (expired, invalid, or doesn't exist)
            logger.warning(f"Failed to load Fyers token: {e}")

    return _client


async def ensure_authenticated() -> FyersClient:
    """
    Get the shared client and ensure it's authenticated.

    This loads the saved token if not already loaded. If no valid token
    exists, raises an error (user needs to run login script).

    Returns:
        FyersClient: Authenticated client

    Raises:
        FyersAuthenticationError: If no valid token exists
    """
    client = get_fyers_client()
    if not client.is_authenticated:
        # Try to load saved token
        loaded = await client.load_saved_token()
        if not loaded:
            from broker.fyers.core.exceptions import FyersAuthenticationError
            raise FyersAuthenticationError(
                "No valid Fyers token found. Please run:\n"
                "  python -m scripts fyers login"
            )
    return client


def reset_client() -> None:
    """
    Reset the shared client (for testing or re-authentication).
    """
    global _client, _initialized
    _client = None
    _initialized = False
