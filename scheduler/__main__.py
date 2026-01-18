"""
Entry point for running the scheduler as a module.

Usage:
    python -m scheduler              # Start scheduler daemon
    python -m scheduler --once       # Run all jobs once (testing)
    python -m scheduler --job news   # Run specific job once
"""

import asyncio
import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from typing import Optional

from scheduler.scheduler import TradingScheduler
from scheduler.jobs import (
    run_intraday_job,
    run_executor_job,
    run_monitoring_job,
    run_news_job,
    run_post_trade_job,
)

app = typer.Typer(
    name="hagrid-scheduler",
    help="Hagrid Trading Workflow Scheduler",
    add_completion=False,
)
console = Console()


@app.command()
def start(
    once: bool = typer.Option(False, "--once", "-o", help="Run all jobs once and exit"),
    job: Optional[str] = typer.Option(None, "--job", "-j", help="Run specific job once (intraday/executor/monitoring/news/post_trade)"),
):
    """Start the trading scheduler."""

    if job:
        # Run specific job once
        console.print(f"\n[bold cyan]Running job: {job}[/bold cyan]\n")
        run_single_job(job)
        return

    if once:
        # Run all jobs once for testing
        console.print(Panel(
            "[bold yellow]Running all jobs once for testing...[/bold yellow]",
            title="Test Mode"
        ))
        run_all_jobs_once()
        return

    # Start scheduler daemon
    console.print(Panel(
        "[bold green]Starting Hagrid Trading Scheduler[/bold green]\n\n"
        "The scheduler will run the following jobs:\n"
        "• Intraday Analysis: 9:00 AM (Mon-Fri)\n"
        "• Order Execution: 9:15 AM (Mon-Fri)\n"
        "• Position Monitoring: Every 20 min (9:30 AM - 3:20 PM)\n"
        "• News Summary: Hourly (9 AM - 4 PM)\n"
        "• Post-Trade Analysis: 4:00 PM (Mon-Fri)\n\n"
        "[dim]Press Ctrl+C to stop[/dim]",
        title="Hagrid Scheduler",
        border_style="green"
    ))

    scheduler = TradingScheduler()

    try:
        asyncio.run(scheduler.start())
    except KeyboardInterrupt:
        console.print("\n[yellow]Scheduler stopped by user[/yellow]")


@app.command()
def status():
    """Show scheduler status and upcoming jobs."""
    scheduler = TradingScheduler()
    jobs = scheduler.get_scheduled_jobs()

    table = Table(title="Scheduled Jobs")
    table.add_column("Job ID", style="cyan")
    table.add_column("Next Run", style="green")
    table.add_column("Schedule", style="yellow")

    for job in jobs:
        table.add_row(
            job["id"],
            job["next_run"],
            job["schedule"]
        )

    console.print(table)


def run_single_job(job_name: str):
    """Run a single job by name."""
    jobs = {
        "intraday": run_intraday_job,
        "executor": run_executor_job,
        "monitoring": run_monitoring_job,
        "news": run_news_job,
        "post_trade": run_post_trade_job,
    }

    if job_name not in jobs:
        console.print(f"[red]Unknown job: {job_name}[/red]")
        console.print(f"Available jobs: {', '.join(jobs.keys())}")
        return

    try:
        result = jobs[job_name]()
        console.print(f"[green]Job completed successfully[/green]")
        console.print(result)
    except Exception as e:
        console.print(f"[red]Job failed: {e}[/red]")


def run_all_jobs_once():
    """Run all jobs once for testing."""
    jobs = [
        ("News Summary", run_news_job),
        ("Intraday Analysis", run_intraday_job),
        ("Order Execution", run_executor_job),
        ("Position Monitoring", run_monitoring_job),
        ("Post-Trade Analysis", run_post_trade_job),
    ]

    for name, job_func in jobs:
        console.print(f"\n[bold cyan]Running: {name}[/bold cyan]")
        try:
            result = job_func()
            console.print(f"[green]✓ {name} completed[/green]")
            if result:
                console.print(f"  Result: {result.get('result', 'N/A')[:100]}...")
        except Exception as e:
            console.print(f"[red]✗ {name} failed: {e}[/red]")


if __name__ == "__main__":
    app()
