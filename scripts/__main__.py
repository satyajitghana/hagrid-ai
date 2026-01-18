"""
Hagrid CLI - Unified Entry Point

Usage:
    python -m scripts fyers login       # Login to Fyers broker
    python -m scripts fyers logout      # Clear Fyers tokens
    python -m scripts run intraday      # Run intraday analysis workflow
    python -m scripts run multi-sector  # Run multi-sector analysis workflow (10 sectors parallel)
    python -m scripts run executor      # Run order execution workflow
    python -m scripts run monitoring    # Run position monitoring workflow
    python -m scripts run news          # Run news summarization workflow
    python -m scripts run post-trade    # Run post-trade analysis workflow
    python -m scripts run all           # Run all workflows in sequence
    python -m scripts status            # Show system status
"""

# Load environment variables first
from dotenv import load_dotenv
load_dotenv()

import asyncio
import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from typing import Optional
from datetime import datetime

app = typer.Typer(
    name="hagrid",
    help="Hagrid Trading System CLI",
    add_completion=False,
    no_args_is_help=True,
)
console = Console()


# ==============================================================================
# FYERS COMMANDS
# ==============================================================================

fyers_app = typer.Typer(
    name="fyers",
    help="Fyers broker authentication commands",
    no_args_is_help=True,
)
app.add_typer(fyers_app, name="fyers")


@fyers_app.command("login")
def fyers_login(
    force: bool = typer.Option(False, "--force", "-f", help="Force full OAuth login"),
    refresh: bool = typer.Option(False, "--refresh", "-r", help="Force token refresh"),
):
    """Login to Fyers broker."""
    from scripts.fyers import login
    login(force=force, refresh=refresh)


@fyers_app.command("logout")
def fyers_logout():
    """Clear Fyers authentication tokens."""
    from scripts.fyers import logout
    logout()


@fyers_app.command("status")
def fyers_status():
    """Check Fyers authentication status."""
    from scripts.fyers import status
    status()


# ==============================================================================
# WORKFLOW RUN COMMANDS
# ==============================================================================

run_app = typer.Typer(
    name="run",
    help="Run trading workflows",
    no_args_is_help=True,
)
app.add_typer(run_app, name="run")


@run_app.command("intraday")
def run_intraday():
    """
    Run the intraday analysis workflow.

    This workflow:
    1. Checks market regime
    2. Runs 4 department teams in parallel (11 analysts + 4 managers)
    3. CIO synthesizes all department reports
    4. Risk manager validates final picks
    """
    console.print(Panel(
        "[bold blue]Running Intraday Analysis Workflow[/bold blue]\n\n"
        "This will analyze NIFTY 100 stocks using:\n"
        "• Technical Analysis Department (3 analysts)\n"
        "• Fundamentals Department (3 analysts)\n"
        "• Market Intelligence Department (3 analysts)\n"
        "• Derivatives Department (1 analyst)\n"
        "• CIO final decision\n"
        "• Risk validation",
        title="Hagrid Trading LLC",
        border_style="blue"
    ))

    try:
        from workflows.intraday_cycle import run_intraday_analysis

        with console.status("[bold green]Running analysis..."):
            result = asyncio.run(run_intraday_analysis())

        console.print("\n[bold green]✓ Analysis Complete[/bold green]")
        console.print(f"  Date: {result.get('date')}")
        console.print(f"  Regime: {result.get('regime')}")

        picks = result.get('picks', [])
        if picks:
            console.print(f"  Picks: {len(picks) if isinstance(picks, list) else 'Generated'}")

        # Show result summary
        if result.get('result'):
            console.print("\n[bold]Result:[/bold]")
            console.print(result['result'][:2000] + "..." if len(str(result.get('result', ''))) > 2000 else result.get('result', ''))

    except Exception as e:
        console.print(f"[red]✗ Error: {e}[/red]")
        raise typer.Exit(1)


@run_app.command("multi-sector")
def run_multi_sector():
    """
    Run the multi-sector analysis workflow.

    This workflow:
    1. Checks market regime
    2. Scans OI spurts for unusual activity
    3. Fetches sector constituents dynamically from NSE
    4. Runs 10 sector teams in PARALLEL
    5. Cross-sector aggregator selects final 15 stocks
    6. Risk manager validates picks

    Sectors: Banking, IT, Financial Services, Pharma, Auto,
             FMCG, Metals, Energy, Realty, Infrastructure
    """
    console.print(Panel(
        "[bold green]Running Multi-Sector Analysis Workflow[/bold green]\n\n"
        "This will analyze stocks across 10 sectors in parallel:\n"
        "• Banking (NIFTY BANK) - Max 3 picks\n"
        "• IT (NIFTY IT) - Max 2 picks\n"
        "• Financial Services - Max 2 picks\n"
        "• Pharma (NIFTY PHARMA) - Max 2 picks\n"
        "• Auto (NIFTY AUTO) - Max 2 picks\n"
        "• FMCG - Max 2 picks\n"
        "• Metals (NIFTY METAL) - Max 2 picks\n"
        "• Energy (NIFTY ENERGY) - Max 2 picks\n"
        "• Realty - Max 2 picks\n"
        "• Infrastructure - Max 2 picks\n\n"
        "[bold]Features:[/bold]\n"
        "• Dynamic stock fetching via NSE India API\n"
        "• OI Spurts integration for smart money signals\n"
        "• Final 15 stocks with max 3 per sector",
        title="Hagrid Multi-Sector Analysis",
        border_style="green"
    ))

    try:
        from workflows.intraday_cycle_multi_sectors import run_multi_sector_analysis

        with console.status("[bold green]Running parallel sector analysis..."):
            result = asyncio.run(run_multi_sector_analysis())

        console.print("\n[bold green]✓ Multi-Sector Analysis Complete[/bold green]")
        console.print(f"  Date: {result.get('date')}")
        console.print(f"  Session: {result.get('session_id')}")
        console.print(f"  Regime: {result.get('regime')}")

        oi_spurts = result.get('oi_spurts', {})
        if oi_spurts:
            bullish = len(oi_spurts.get('bullish', []))
            bearish = len(oi_spurts.get('bearish', []))
            console.print(f"  OI Spurts: {bullish} bullish, {bearish} bearish signals")

        final_picks = result.get('final_picks', [])
        if final_picks:
            console.print(f"  Final Picks: {len(final_picks) if isinstance(final_picks, list) else 'Generated'}")

        if result.get('output_file'):
            console.print(f"  Output: {result['output_file']}")

        # Show result summary
        if result.get('result'):
            result_text = str(result.get('result', ''))
            console.print("\n[bold]Result:[/bold]")
            console.print(result_text[:3000] + "..." if len(result_text) > 3000 else result_text)

    except Exception as e:
        console.print(f"[red]✗ Error: {e}[/red]")
        raise typer.Exit(1)


@run_app.command("executor")
def run_executor():
    """
    Run the order execution workflow.

    Loads picks from intraday analysis and executes orders.
    """
    console.print("[bold green]Running Order Execution Workflow[/bold green]\n")

    try:
        from workflows.executor import run_executor as run_executor_workflow

        with console.status("[bold green]Executing orders..."):
            result = asyncio.run(run_executor_workflow())

        console.print("[green]✓ Execution Complete[/green]")
        console.print(f"  Date: {result.get('date')}")
        console.print(f"  Executed: {len(result.get('executed', []))}")

        if result.get('result'):
            console.print(f"\n[bold]Result:[/bold]\n{result['result'][:1000]}")

    except Exception as e:
        console.print(f"[red]✗ Error: {e}[/red]")
        raise typer.Exit(1)


@run_app.command("monitoring")
def run_monitoring():
    """
    Run the position monitoring workflow.

    Monitors open positions and adjusts stops/exits.
    """
    console.print("[bold yellow]Running Position Monitoring Workflow[/bold yellow]\n")

    try:
        from workflows.monitoring import run_monitoring as run_monitoring_workflow

        with console.status("[bold yellow]Monitoring positions..."):
            result = asyncio.run(run_monitoring_workflow())

        console.print("[green]✓ Monitoring Complete[/green]")
        console.print(f"  Date: {result.get('date')}")
        console.print(f"  Open Trades: {len(result.get('open_trades', []))}")
        console.print(f"  Adjustments: {len(result.get('adjustments', []))}")

        if result.get('result'):
            console.print(f"\n[bold]Result:[/bold]\n{result['result'][:1000]}")

    except Exception as e:
        console.print(f"[red]✗ Error: {e}[/red]")
        raise typer.Exit(1)


@run_app.command("news")
def run_news():
    """
    Run the news summarization workflow.

    Aggregates and summarizes market news.
    """
    console.print("[bold cyan]Running News Summarization Workflow[/bold cyan]\n")

    try:
        from workflows.news_workflow import run_news_summary

        with console.status("[bold cyan]Fetching news..."):
            result = asyncio.run(run_news_summary())

        console.print("[green]✓ News Summary Complete[/green]")
        console.print(f"  Date: {result.get('date')}")
        console.print(f"  Sentiment: {result.get('sentiment')}")
        console.print(f"  Key Events: {len(result.get('key_events', []))}")
        console.print(f"  Affected Symbols: {len(result.get('affected_symbols', []))}")

        if result.get('result'):
            console.print(f"\n[bold]Summary:[/bold]\n{result['result'][:1000]}")

    except Exception as e:
        console.print(f"[red]✗ Error: {e}[/red]")
        raise typer.Exit(1)


@run_app.command("post-trade")
def run_post_trade():
    """
    Run the post-trade analysis workflow.

    Analyzes day's trading performance.
    """
    console.print("[bold magenta]Running Post-Trade Analysis Workflow[/bold magenta]\n")

    try:
        from workflows.post_trade import run_post_trade_analysis

        with console.status("[bold magenta]Analyzing performance..."):
            result = asyncio.run(run_post_trade_analysis())

        console.print("[green]✓ Post-Trade Analysis Complete[/green]")
        console.print(f"  Date: {result.get('date')}")

        metrics = result.get('metrics', {})
        if metrics:
            console.print(f"  Total Trades: {metrics.get('total_trades', 0)}")
            console.print(f"  Win Rate: {metrics.get('win_rate', 0):.1f}%")
            console.print(f"  Total P&L: ₹{metrics.get('total_pnl', 0):.2f}")

        if result.get('report'):
            console.print(f"\n[bold]Report:[/bold]\n{result['report'][:1500]}")

    except Exception as e:
        console.print(f"[red]✗ Error: {e}[/red]")
        raise typer.Exit(1)


@run_app.command("all")
def run_all(
    skip_execution: bool = typer.Option(False, "--skip-execution", "-s", help="Skip order execution"),
):
    """
    Run all workflows in sequence.

    Order: News → Intraday → Executor → Monitoring → Post-Trade
    """
    console.print(Panel(
        "[bold]Running Full Trading Cycle[/bold]\n\n"
        "1. News Summarization\n"
        "2. Intraday Analysis\n"
        "3. Order Execution\n"
        "4. Position Monitoring\n"
        "5. Post-Trade Analysis",
        title="Hagrid Full Cycle",
        border_style="green"
    ))

    workflows = [
        ("News Summary", run_news),
        ("Intraday Analysis", run_intraday),
    ]

    if not skip_execution:
        workflows.append(("Order Execution", run_executor))

    workflows.extend([
        ("Position Monitoring", run_monitoring),
        ("Post-Trade Analysis", run_post_trade),
    ])

    for name, func in workflows:
        console.print(f"\n[bold]{'='*50}[/bold]")
        console.print(f"[bold]{name}[/bold]")
        console.print(f"[bold]{'='*50}[/bold]\n")
        try:
            func()
        except Exception as e:
            console.print(f"[red]✗ {name} failed: {e}[/red]")
            if not typer.confirm("Continue with next workflow?"):
                raise typer.Exit(1)

    console.print("\n[bold green]✓ Full cycle complete![/bold green]")


# ==============================================================================
# STATUS COMMAND
# ==============================================================================

@app.command("status")
def status():
    """Show system status and configuration."""
    from pathlib import Path
    from core.config import get_settings

    settings = get_settings()

    table = Table(title="Hagrid Trading System Status")
    table.add_column("Setting", style="cyan")
    table.add_column("Value", style="green")

    table.add_row("App Name", settings.APP_NAME)
    table.add_row("Version", settings.VERSION)
    table.add_row("Debug Mode", str(settings.DEBUG))
    table.add_row("Data Directory", str(settings.DATA_DIR))
    table.add_row("Base Capital", f"₹{settings.BASE_CAPITAL:,.0f}")
    table.add_row("Target Daily Return", f"{settings.TARGET_DAILY_RETURN_PERCENT}%")
    table.add_row("Max Risk Per Trade", f"{settings.MAX_RISK_PER_TRADE_PERCENT}%")
    table.add_row("Max Stocks Per Day", str(settings.MAX_STOCKS_PER_DAY))
    table.add_row("Scheduler Enabled", str(settings.SCHEDULER_ENABLED))
    table.add_row("Market Open", settings.MARKET_OPEN_TIME)
    table.add_row("Market Close", settings.MARKET_CLOSE_TIME)

    console.print(table)

    # Check data files
    console.print("\n[bold]Data Files:[/bold]")
    files_to_check = [
        ("Fyers Token", settings.FYERS_TOKEN_FILE),
        ("Workflow DB", settings.WORKFLOW_DB_FILE),
        ("Agent DB", settings.AGENT_DB_FILE),
        ("Trade DB", settings.TRADE_DB_FILE),
    ]
    for name, file_path in files_to_check:
        if Path(file_path).exists():
            console.print(f"  [green]✓ {name}[/green]: {file_path}")
        else:
            console.print(f"  [dim]○ {name}[/dim]: {file_path}")

    # Check Fyers auth status
    console.print("\n[bold]Broker Status:[/bold]")
    try:
        token_file = Path(settings.FYERS_TOKEN_FILE)
        if token_file.exists():
            console.print("  [green]✓ Fyers token file exists[/green]")
        else:
            console.print("  [yellow]⚠ No Fyers token file - run 'python -m scripts fyers login'[/yellow]")
    except Exception:
        console.print("  [red]✗ Could not check Fyers status[/red]")


# ==============================================================================
# MAIN
# ==============================================================================

if __name__ == "__main__":
    app()
