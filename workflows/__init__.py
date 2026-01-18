"""
Workflows package for Hagrid AI Trading System.

Provides shared database instances, tracing, and logging setup.
"""

from agno.db.sqlite import SqliteDb
from core.config import get_settings
from core.logging_setup import setup_logging

settings = get_settings()

# Set up centralized logging first
logger = setup_logging(
    log_level=settings.LOG_LEVEL,
    log_to_file=settings.LOG_TO_FILE,
    log_file=settings.LOG_FILE,
    agno_debug=settings.AGNO_DEBUG,
    agno_debug_level=settings.AGNO_DEBUG_LEVEL,
)

# Shared database for all workflows
# Auto-stores: session_id, runs, step results, session_state, timestamps
workflow_db = SqliteDb(
    db_file=settings.WORKFLOW_DB_FILE,
    session_table="workflow_sessions"
)

# Shared database for agents (optional - for agent-level history)
# Use when agents need their own conversation history across runs
agent_db = SqliteDb(
    db_file=settings.AGENT_DB_FILE,
    session_table="agent_sessions"
)

# Tracing database (separate for performance)
tracing_db = SqliteDb(
    db_file=settings.TRACING_DB_FILE,
    session_table="tracing_sessions"
)

# Enable tracing if configured
if settings.TRACING_ENABLED:
    try:
        from agno.tracing import setup_tracing

        setup_tracing(
            db=tracing_db,
            batch_processing=True,
            max_queue_size=settings.TRACING_QUEUE_SIZE,
            max_export_batch_size=settings.TRACING_BATCH_SIZE,
        )
        logger.info("Agno tracing enabled")
    except ImportError:
        logger.warning(
            "Tracing dependencies not installed. "
            "Run: uv add opentelemetry-api opentelemetry-sdk openinference-instrumentation-agno"
        )
    except Exception as e:
        logger.error(f"Failed to setup tracing: {e}")

# Export workflow instances after they're defined
# These will be populated by the workflow modules
__all__ = [
    "workflow_db",
    "agent_db",
    "tracing_db",
    "logger",
]
