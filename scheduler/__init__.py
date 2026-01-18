"""
Hagrid Trading Scheduler Package

This package provides scheduled execution of trading workflows:
- Intraday Analysis: 9:00 AM (Mon-Fri)
- Order Execution: 9:15 AM (Mon-Fri)
- Position Monitoring: Every 20 min during market hours
- News Summary: Hourly during market hours
- Post-Trade Analysis: 4:00 PM (Mon-Fri)

Usage:
    python -m scheduler          # Start scheduler
    python -m scheduler --once   # Run all jobs once (testing)
"""

from scheduler.scheduler import TradingScheduler
from scheduler.jobs import (
    run_intraday_job,
    run_executor_job,
    run_monitoring_job,
    run_news_job,
    run_post_trade_job,
)

__all__ = [
    "TradingScheduler",
    "run_intraday_job",
    "run_executor_job",
    "run_monitoring_job",
    "run_news_job",
    "run_post_trade_job",
]
