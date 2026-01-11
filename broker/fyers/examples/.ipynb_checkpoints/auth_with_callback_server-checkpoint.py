"""
Example: Automatic OAuth Authentication with Callback Server

This example demonstrates the easiest way to authenticate with Fyers API
using the automatic callback server - no manual copy-paste needed!

IMPORTANT: You must register your redirect_uri in Fyers dashboard first!

Usage:
    # From project root directory
    python -m broker.fyers.examples.auth_with_callback_server
    
    # Or run directly if in virtual environment with package installed
    python broker/fyers/examples/auth_with_callback_server.py
"""

import asyncio
import sys
from pathlib import Path

# Add project root to Python path for direct execution
if __name__ == "__main__":
    project_root = Path(__file__).parent.parent.parent.parent
    sys.path.insert(0, str(project_root))

from broker.fyers import FyersClient, FyersConfig


async def main():
    """Demonstrate automatic authentication with callback server."""
    
    # Step 1: Register redirect URI in Fyers dashboard
    # Go to: https://myapi.fyers.in/dashboard
    # Add redirect URI: http://127.0.0.1:9000/
    
    # Step 2: Configure client with the SAME redirect URI
    config = FyersConfig(
        client_id="TX4LY7JMLL-100",  # Replace with your app ID
        secret_key="5L72OBKPUM",  # Replace with your secret
        redirect_uri="http://fyers.localhost:9001/",  # MUST match Fyers dashboard
        token_file_path="fyers_token.json",  # Optional: persist tokens
    )
    
    client = FyersClient(config)
    
    # Step 3: Authenticate automatically!
    # - Browser opens automatically
    # - You login on Fyers website
    # - Callback is captured automatically at port 9000
    # - No copy-paste required!
    print("\n🚀 Starting automatic authentication...")
    print("Your browser will open shortly for login.\n")
    
    try:
        # The callback server will use port 9000 from redirect_uri
        token_data = await client.authenticate_with_callback_server(
            timeout=300,  # Optional: timeout in seconds (default 300)
        )
        
        print(f"\n✅ Authentication successful!")
        print(f"Access Token: {token_data.access_token[:30]}...")
        
        # Step 4: Now you can make API calls
        print("\n📊 Fetching market data...")
        quotes = await client.get_quotes(["NSE:SBIN-EQ", "NSE:INFY-EQ"])
        print(f"Quotes: {quotes}")
        
    except RuntimeError as e:
        print(f"\n❌ Port error: {e}")
        print("Solution: Ensure no other application is using port 9000")
        raise
    except Exception as e:
        print(f"\n❌ Authentication failed: {e}")
        raise


async def main_with_custom_port():
    """Example using a different port (e.g., 8080)."""
    
    # Step 1: Register http://127.0.0.1:8080/ in Fyers dashboard
    
    # Step 2: Configure with same port
    config = FyersConfig(
        client_id="YOUR_CLIENT_ID",
        secret_key="YOUR_SECRET_KEY",
        redirect_uri="http://127.0.0.1:8080/",  # Different port
    )
    
    client = FyersClient(config)
    
    # The callback server will use port 8080 from redirect_uri
    print("\n🔍 Using port 8080 from redirect_uri...")
    token_data = await client.authenticate_with_callback_server()
    
    print(f"\n✅ Authenticated successfully!")
    return token_data


async def main_with_fallback():
    """Example with fallback to manual authentication if callback fails."""
    
    from broker.fyers.auth.oauth import interactive_login
    
    config = FyersConfig(
        client_id="YOUR_CLIENT_ID",
        secret_key="YOUR_SECRET_KEY",
        redirect_uri="http://127.0.0.1:9000/",
    )
    
    # interactive_login tries automatic first, falls back to manual if needed
    try:
        token_data = await interactive_login(
            config=config,
            use_callback_server=True,  # Try automatic first (default)
        )
        print(f"\n✅ Authenticated: {token_data.access_token[:30]}...")
    except Exception as e:
        print(f"\n❌ Failed: {e}")


async def main_with_manual_only():
    """Example forcing manual authentication (old method)."""
    
    from broker.fyers.auth.oauth import interactive_login
    
    config = FyersConfig(
        client_id="YOUR_CLIENT_ID",
        secret_key="YOUR_SECRET_KEY",
        redirect_uri="https://trade.fyers.in/api-login/redirect-uri/index.html",
    )
    
    # Force manual authentication (no callback server)
    token_data = await interactive_login(
        config=config,
        use_callback_server=False,  # Use manual copy-paste method
    )
    
    print(f"\n✅ Authenticated manually!")
    return token_data


if __name__ == "__main__":
    print("=" * 70)
    print("Fyers Automatic OAuth Authentication Example")
    print("=" * 70)
    print("\nIMPORTANT: Register http://127.0.0.1:9000/ in Fyers dashboard first!")
    print("Visit: https://myapi.fyers.in/dashboard\n")
    
    # Run the main example
    asyncio.run(main())
    
    # Uncomment to try other examples:
    # asyncio.run(main_with_custom_port())
    # asyncio.run(main_with_fallback())
    # asyncio.run(main_with_manual_only())