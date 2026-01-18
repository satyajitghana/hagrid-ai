"""
Trading Scheduler using APScheduler

This module configures and runs the scheduled trading workflows
during Indian market hours (9 AM - 4 PM, Monday-Friday).
"""

import asyncio
from datetime import datetime
from typing import List, Dict, Any

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.events import EVENT_JOB_ERROR, EVENT_JOB_EXECUTED

from rich.console import Console

from core.config import get_settings
from scheduler.jobs import (
    run_intraday_job,
    run_executor_job,
    run_monitoring_job,
    run_news_job,
    run_post_trade_job,
)

settings = get_settings()
console = Console()


class TradingScheduler:
    """
    Manages scheduled execution of trading workflows.

    Schedule:
    - 9:00 AM: Intraday Analysis (generate picks)
    - 9:15 AM: Order Execution (place orders)
    - 9:30 AM - 3:20 PM: Position Monitoring (every 20 min)
    - 9 AM - 4 PM: News Summary (hourly)
    - 4:00 PM: Post-Trade Analysis
    """

    def __init__(self):
        self.scheduler = AsyncIOScheduler(
            timezone="Asia/Kolkata",
            job_defaults={
                "coalesce": True,  # Combine missed runs into one
                "max_instances": 1,  # Only one instance per job
                "misfire_grace_time": 300,  # 5 min grace for missed jobs
            }
        )
        self._configure_jobs()
        self._configure_listeners()

    def _configure_jobs(self):
        """Configure all scheduled jobs."""

        if not settings.SCHEDULER_ENABLED:
            console.print("[yellow]Scheduler is disabled in config[/yellow]")
            return

        # Intraday Analysis - 9:00 AM Monday-Friday
        self.scheduler.add_job(
            run_intraday_job,
            CronTrigger(hour=9, minute=0, day_of_week="mon-fri"),
            id="intraday_analysis",
            name="Intraday Analysis",
            replace_existing=True,
        )

        # Order Execution - 9:15 AM Monday-Friday
        self.scheduler.add_job(
            run_executor_job,
            CronTrigger(hour=9, minute=15, day_of_week="mon-fri"),
            id="order_execution",
            name="Order Execution",
            replace_existing=True,
        )

        # Position Monitoring - Every 20 minutes from 9:30 AM to 3:20 PM
        self.scheduler.add_job(
            run_monitoring_job,
            CronTrigger(
                minute="10,30,50",  # At 10, 30, 50 past the hour
                hour="9-15",  # 9 AM to 3 PM
                day_of_week="mon-fri"
            ),
            id="position_monitoring",
            name="Position Monitoring",
            replace_existing=True,
        )

        # News Summary - Hourly from 9 AM to 4 PM
        self.scheduler.add_job(
            run_news_job,
            CronTrigger(
                minute=0,  # At the top of each hour
                hour="9-16",  # 9 AM to 4 PM
                day_of_week="mon-fri"
            ),
            id="news_summary",
            name="News Summary",
            replace_existing=True,
        )

        # Post-Trade Analysis - 4:00 PM Monday-Friday
        self.scheduler.add_job(
            run_post_trade_job,
            CronTrigger(hour=16, minute=0, day_of_week="mon-fri"),
            id="post_trade_analysis",
            name="Post-Trade Analysis",
            replace_existing=True,
        )

        console.print("[green]✓ All jobs configured[/green]")

    def _configure_listeners(self):
        """Configure event listeners for job execution."""

        def job_executed(event):
            """Handle successful job execution."""
            job_id = event.job_id
            console.print(f"[green]✓ Job completed: {job_id}[/green]")

        def job_error(event):
            """Handle job execution errors."""
            job_id = event.job_id
            exception = event.exception
            console.print(f"[red]✗ Job failed: {job_id} - {exception}[/red]")

        self.scheduler.add_listener(job_executed, EVENT_JOB_EXECUTED)
        self.scheduler.add_listener(job_error, EVENT_JOB_ERROR)

    async def start(self):
        """Start the scheduler and run forever."""
        self.scheduler.start()
        console.print(f"[green]Scheduler started at {datetime.now()}[/green]")

        # Print next run times
        self._print_next_runs()

        # Keep running until interrupted
        try:
            while True:
                await asyncio.sleep(60)  # Check every minute
        except (KeyboardInterrupt, SystemExit):
            console.print("[yellow]Shutting down scheduler...[/yellow]")
            self.scheduler.shutdown(wait=True)

    def _print_next_runs(self):
        """Print upcoming job run times."""
        console.print("\n[bold]Upcoming job runs:[/bold]")
        for job in self.scheduler.get_jobs():
            next_run = job.next_run_time
            if next_run:
                console.print(f"  • {job.name}: {next_run.strftime('%Y-%m-%d %H:%M:%S')}")

    def get_scheduled_jobs(self) -> List[Dict[str, Any]]:
        """Get list of scheduled jobs with their next run times."""
        jobs = []
        for job in self.scheduler.get_jobs():
            jobs.append({
                "id": job.id,
                "name": job.name,
                "next_run": job.next_run_time.strftime("%Y-%m-%d %H:%M:%S") if job.next_run_time else "Not scheduled",
                "schedule": str(job.trigger),
            })
        return jobs

    def pause_job(self, job_id: str):
        """Pause a specific job."""
        self.scheduler.pause_job(job_id)
        console.print(f"[yellow]Paused job: {job_id}[/yellow]")

    def resume_job(self, job_id: str):
        """Resume a paused job."""
        self.scheduler.resume_job(job_id)
        console.print(f"[green]Resumed job: {job_id}[/green]")

    def run_job_now(self, job_id: str):
        """Trigger immediate execution of a job."""
        job = self.scheduler.get_job(job_id)
        if job:
            job.func()
            console.print(f"[green]Triggered job: {job_id}[/green]")
        else:
            console.print(f"[red]Job not found: {job_id}[/red]")
