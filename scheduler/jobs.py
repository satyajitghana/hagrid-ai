"""
Job implementations for the trading scheduler.

Each job wraps a workflow's run function and handles logging/errors.
"""

from datetime import datetime
from typing import Dict, Any, Optional

from rich.console import Console

console = Console()


def run_intraday_job() -> Dict[str, Any]:
    """
    Run the intraday analysis workflow.

    Schedule: 9:00 AM Monday-Friday
    Purpose: Analyze NIFTY 100 stocks and generate 10-15 picks
    """
    console.print(f"\n[bold blue]{'='*50}[/bold blue]")
    console.print(f"[bold blue]INTRADAY ANALYSIS - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}[/bold blue]")
    console.print(f"[bold blue]{'='*50}[/bold blue]\n")

    try:
        from workflows.intraday_cycle import run_intraday_analysis

        result = run_intraday_analysis()

        console.print(f"[green]✓ Analysis complete[/green]")
        console.print(f"  Date: {result.get('date')}")
        console.print(f"  Regime: {result.get('regime')}")
        console.print(f"  Picks: {len(result.get('picks', [])) if isinstance(result.get('picks'), list) else 'Generated'}")

        return result

    except Exception as e:
        console.print(f"[red]✗ Intraday analysis failed: {e}[/red]")
        raise


def run_executor_job() -> Dict[str, Any]:
    """
    Run the order execution workflow.

    Schedule: 9:15 AM Monday-Friday
    Purpose: Execute orders based on intraday analysis picks
    """
    console.print(f"\n[bold green]{'='*50}[/bold green]")
    console.print(f"[bold green]ORDER EXECUTION - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}[/bold green]")
    console.print(f"[bold green]{'='*50}[/bold green]\n")

    try:
        from workflows.executor import run_executor

        result = run_executor()

        console.print(f"[green]✓ Execution complete[/green]")
        console.print(f"  Date: {result.get('date')}")
        console.print(f"  Executed: {len(result.get('executed', []))}")

        return result

    except Exception as e:
        console.print(f"[red]✗ Order execution failed: {e}[/red]")
        raise


def run_monitoring_job() -> Dict[str, Any]:
    """
    Run the position monitoring workflow.

    Schedule: Every 20 minutes from 9:30 AM to 3:20 PM
    Purpose: Monitor open positions, adjust stops, close losers
    """
    console.print(f"\n[bold yellow]{'='*50}[/bold yellow]")
    console.print(f"[bold yellow]POSITION MONITORING - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}[/bold yellow]")
    console.print(f"[bold yellow]{'='*50}[/bold yellow]\n")

    try:
        from workflows.monitoring import run_monitoring

        result = run_monitoring()

        console.print(f"[green]✓ Monitoring complete[/green]")
        console.print(f"  Date: {result.get('date')}")
        console.print(f"  Open trades: {len(result.get('open_trades', []))}")
        console.print(f"  Adjustments: {len(result.get('adjustments', []))}")

        return result

    except Exception as e:
        console.print(f"[red]✗ Position monitoring failed: {e}[/red]")
        raise


def run_news_job() -> Dict[str, Any]:
    """
    Run the news summarization workflow.

    Schedule: Hourly from 9 AM to 4 PM
    Purpose: Aggregate and summarize market news
    """
    console.print(f"\n[bold cyan]{'='*50}[/bold cyan]")
    console.print(f"[bold cyan]NEWS SUMMARY - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}[/bold cyan]")
    console.print(f"[bold cyan]{'='*50}[/bold cyan]\n")

    try:
        from workflows.news_workflow import run_news_summary

        result = run_news_summary()

        console.print(f"[green]✓ News summary complete[/green]")
        console.print(f"  Date: {result.get('date')}")
        console.print(f"  Sentiment: {result.get('sentiment')}")
        console.print(f"  Key events: {len(result.get('key_events', []))}")
        console.print(f"  Affected symbols: {len(result.get('affected_symbols', []))}")

        return result

    except Exception as e:
        console.print(f"[red]✗ News summary failed: {e}[/red]")
        raise


def run_post_trade_job() -> Dict[str, Any]:
    """
    Run the post-trade analysis workflow.

    Schedule: 4:00 PM Monday-Friday
    Purpose: Analyze day's performance, generate report
    """
    console.print(f"\n[bold magenta]{'='*50}[/bold magenta]")
    console.print(f"[bold magenta]POST-TRADE ANALYSIS - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}[/bold magenta]")
    console.print(f"[bold magenta]{'='*50}[/bold magenta]\n")

    try:
        from workflows.post_trade import run_post_trade_analysis

        result = run_post_trade_analysis()

        metrics = result.get("metrics", {})
        console.print(f"[green]✓ Post-trade analysis complete[/green]")
        console.print(f"  Date: {result.get('date')}")
        console.print(f"  Total trades: {metrics.get('total_trades', 0)}")
        console.print(f"  Win rate: {metrics.get('win_rate', 0):.1f}%")
        console.print(f"  Total P&L: ₹{metrics.get('total_pnl', 0):.2f}")
        console.print(f"  P&L %: {metrics.get('pnl_pct', 0):.2f}%")

        return result

    except Exception as e:
        console.print(f"[red]✗ Post-trade analysis failed: {e}[/red]")
        raise


def check_market_hours() -> bool:
    """
    Check if current time is within Indian market hours.

    Market hours: 9:15 AM to 3:30 PM IST, Monday-Friday
    """
    from datetime import time
    import pytz

    ist = pytz.timezone("Asia/Kolkata")
    now = datetime.now(ist)

    # Check if weekday (Monday=0, Friday=4)
    if now.weekday() > 4:
        return False

    # Check market hours
    market_open = time(9, 15)
    market_close = time(15, 30)

    return market_open <= now.time() <= market_close


def is_trading_day() -> bool:
    """
    Check if today is a trading day.

    Note: This doesn't account for market holidays.
    For production, integrate with NSE holiday calendar.
    """
    import pytz

    ist = pytz.timezone("Asia/Kolkata")
    now = datetime.now(ist)

    # Monday=0 to Friday=4
    return now.weekday() <= 4
