#!/usr/bin/env python3
"""
Fyers Login Script

Smart authentication flow:
1. Load saved token from file
2. Call get_profile() to validate token
3. If valid -> Success (use existing token)
4. If expired -> Try refresh_access_token(refresh_token, PIN)
5. If refresh fails -> Full OAuth login via callback server
6. Store new token to file

Usage:
    python scripts/login_fyers.py              # Auto (tries token -> refresh -> full)
    python scripts/login_fyers.py --refresh    # Force refresh (prompts for PIN interactively)
    python scripts/login_fyers.py --force      # Force full login
    python scripts/login_fyers.py --status     # Check current auth status only
"""

# Load environment variables first
from dotenv import load_dotenv
load_dotenv()

import asyncio
import sys
from pathlib import Path

import typer
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from broker.fyers import FyersClient, FyersConfig
from broker.fyers.core.exceptions import FyersAuthenticationError
from core.config import get_settings

# Initialize Typer app and Rich console
app = typer.Typer(
    name="fyers-login",
    help="Fyers Authentication CLI for Hagrid AI Trading System",
    add_completion=False,
)
console = Console()


def print_banner():
    """Print script banner."""
    console.print(Panel.fit(
        "[bold blue]Hagrid AI[/bold blue] - [cyan]Fyers Authentication[/cyan]",
        border_style="blue"
    ))


def print_success(client: FyersClient):
    """Print successful authentication status."""
    if client.user_profile:
        table = Table(title="Authentication Successful", border_style="green")
        table.add_column("Field", style="cyan")
        table.add_column("Value", style="green")
        table.add_row("Name", client.user_profile.name or "N/A")
        table.add_row("Fyers ID", client.user_profile.fy_id or "N/A")
        table.add_row("Email", client.user_profile.email_id or "N/A")
        console.print(table)
    else:
        console.print("[green]✓[/green] Token is valid")


def print_failure(message: str = "Not authenticated"):
    """Print authentication failure."""
    console.print(f"[red]✗[/red] {message}")


async def check_status(client: FyersClient) -> bool:
    """Check if current token is valid without modifying anything."""
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        progress.add_task(description="Checking authentication status...", total=None)

        try:
            if await client.load_saved_token():
                return True
            else:
                return False
        except Exception as e:
            console.print(f"[red]Error:[/red] {e}")
            return False


async def try_validate_existing_token(client: FyersClient) -> bool:
    """Try to load and validate existing token."""
    console.print("\n[dim]Step 1/3:[/dim] Checking for existing valid token...")

    try:
        if await client.load_saved_token():
            console.print("  [green]✓[/green] Found valid token!")
            return True
        else:
            console.print("  [yellow]![/yellow] No valid token found or token expired")
            return False
    except Exception as e:
        console.print(f"  [red]✗[/red] Error: {e}")
        return False


async def try_refresh_token(client: FyersClient, pin: str = None) -> bool:
    """Try to refresh expired token using PIN."""
    console.print("\n[dim]Step 2/3:[/dim] Attempting token refresh...")

    if pin is None:
        console.print("  [cyan]Token refresh requires your Fyers PIN[/cyan]")
        pin = typer.prompt("  Enter PIN", hide_input=True)

        if not pin:
            console.print("  [yellow]![/yellow] No PIN provided, skipping refresh")
            return False

    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            progress.add_task(description="Refreshing token...", total=None)
            await client.authenticate(refresh_pin=pin, auto_browser=False)

        console.print("  [green]✓[/green] Token refreshed successfully!")
        return True
    except FyersAuthenticationError as e:
        console.print(f"  [red]✗[/red] Refresh failed: {e}")
        return False
    except Exception as e:
        console.print(f"  [red]✗[/red] Error during refresh: {e}")
        return False


async def do_full_login(client: FyersClient) -> bool:
    """Perform full OAuth login via browser."""
    console.print("\n[dim]Step 3/3:[/dim] Starting full OAuth login...")
    console.print("  [cyan]Browser will open for Fyers login[/cyan]")
    console.print("  [dim]Please complete the login in your browser[/dim]")

    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            progress.add_task(description="Waiting for authentication...", total=None)
            await client.authenticate_with_callback_server(timeout=300)

        console.print("  [green]✓[/green] Full login completed successfully!")
        return True
    except FyersAuthenticationError as e:
        console.print(f"  [red]✗[/red] Login failed: {e}")
        return False
    except Exception as e:
        console.print(f"  [red]✗[/red] Error during login: {e}")
        return False


async def auto_login(client: FyersClient) -> bool:
    """
    Smart auto-login flow:
    1. Try existing token
    2. Try refresh with PIN prompt
    3. Full OAuth login
    """
    # Step 1: Try existing token
    if await try_validate_existing_token(client):
        return True

    # Step 2: Try refresh (will prompt for PIN)
    if await try_refresh_token(client):
        return True

    # Step 3: Full login
    return await do_full_login(client)


def get_client() -> FyersClient:
    """Create and return a FyersClient instance."""
    settings = get_settings()

    if not settings.FYERS_CLIENT_ID or not settings.FYERS_SECRET_KEY:
        console.print("[red]Error:[/red] FYERS_CLIENT_ID and FYERS_SECRET_KEY must be set")
        console.print("[dim]Add them to your .env file:[/dim]")
        console.print("  FYERS_CLIENT_ID=your_client_id")
        console.print("  FYERS_SECRET_KEY=your_secret_key")
        raise typer.Exit(1)

    config = FyersConfig(
        client_id=settings.FYERS_CLIENT_ID,
        secret_key=settings.FYERS_SECRET_KEY,
        token_file_path=settings.FYERS_TOKEN_FILE,
    )

    # Show config info
    table = Table(show_header=False, box=None)
    table.add_column("Key", style="dim")
    table.add_column("Value", style="cyan")
    table.add_row("Client ID", settings.FYERS_CLIENT_ID)
    table.add_row("Token File", settings.FYERS_TOKEN_FILE)
    console.print(table)

    return FyersClient(config)


@app.command()
def login(
    refresh: bool = typer.Option(False, "--refresh", "-r", help="Force token refresh (prompts for PIN)"),
    force: bool = typer.Option(False, "--force", "-f", help="Force full OAuth login via browser"),
    status: bool = typer.Option(False, "--status", "-s", help="Check current authentication status only"),
):
    """
    Authenticate with Fyers API.

    By default, uses smart auto-login that tries:
    1. Existing saved token
    2. Token refresh with PIN
    3. Full OAuth login via browser
    """
    print_banner()
    console.print()

    try:
        client = get_client()
    except typer.Exit:
        raise

    async def run():
        if status:
            success = await check_status(client)
        elif refresh:
            console.print("[bold]Force Refresh Mode[/bold]")
            success = await try_refresh_token(client)
        elif force:
            console.print("[bold]Force Login Mode[/bold]")
            success = await do_full_login(client)
        else:
            success = await auto_login(client)

        return success

    success = asyncio.run(run())

    console.print()

    if success:
        print_success(client)
        console.print()
        console.print(Panel.fit(
            "[bold green]Ready to trade![/bold green]",
            border_style="green"
        ))
        raise typer.Exit(0)
    else:
        print_failure()
        console.print()
        console.print(Panel.fit(
            "[bold red]Authentication failed[/bold red]",
            border_style="red"
        ))
        raise typer.Exit(1)


@app.command()
def logout():
    """Clear saved authentication token."""
    print_banner()
    console.print()

    settings = get_settings()
    token_file = Path(settings.FYERS_TOKEN_FILE)

    if token_file.exists():
        if typer.confirm(f"Delete token file {token_file}?"):
            token_file.unlink()
            console.print("[green]✓[/green] Token file deleted")
        else:
            console.print("[yellow]![/yellow] Logout cancelled")
    else:
        console.print("[yellow]![/yellow] No token file found")


@app.command()
def status():
    """Check current authentication status."""
    print_banner()
    console.print()

    settings = get_settings()
    token_file = Path(settings.FYERS_TOKEN_FILE)

    table = Table(title="Fyers Authentication Status", border_style="blue")
    table.add_column("Check", style="cyan")
    table.add_column("Status", style="green")

    # Show token file path
    table.add_row("Token Path", f"[dim]{token_file}[/dim]")

    # Check token file
    if token_file.exists():
        table.add_row("Token File", "[green]✓ Exists[/green]")

        # Try to read and validate
        try:
            import json
            with open(token_file) as f:
                token_data = json.load(f)

            if token_data.get("access_token"):
                table.add_row("Access Token", "[green]✓ Present[/green]")
            else:
                table.add_row("Access Token", "[red]✗ Missing[/red]")

            if token_data.get("refresh_token"):
                table.add_row("Refresh Token", "[green]✓ Present[/green]")
            else:
                table.add_row("Refresh Token", "[yellow]⚠ Missing[/yellow]")

        except Exception as e:
            table.add_row("Token Parse", f"[red]✗ Error: {e}[/red]")
    else:
        table.add_row("Token File", "[red]✗ Not found[/red]")
        table.add_row("Status", "[yellow]Run 'python -m scripts fyers login'[/yellow]")

    console.print(table)

    # Try to validate with API if token exists
    if token_file.exists():
        console.print("\n[dim]Validating token with Fyers API...[/dim]")
        try:
            client = get_client()
            success = asyncio.run(check_status(client))
            if success:
                print_success(client)
            else:
                console.print("[yellow]⚠ Token may be expired - run 'python -m scripts fyers login'[/yellow]")
        except Exception as e:
            console.print(f"[red]✗ Validation error: {e}[/red]")


if __name__ == "__main__":
    app()
