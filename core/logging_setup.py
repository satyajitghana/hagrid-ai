"""Centralized logging configuration for Hagrid AI."""

import os
import logging
from pathlib import Path
from typing import Optional


def setup_logging(
    log_level: str = "INFO",
    log_to_file: bool = True,
    log_file: Optional[str] = None,
    agno_debug: bool = True,
    agno_debug_level: int = 1,
) -> logging.Logger:
    """
    Configure centralized logging for Hagrid AI.

    - Sets up console handler with source identification
    - Sets up file handler (optional)
    - Configures Agno framework logging
    - Sets AGNO_DEBUG environment variable

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
        log_to_file: Whether to write logs to file
        log_file: Path to log file
        agno_debug: Whether to enable Agno debug mode
        agno_debug_level: Agno debug level (1=normal, 2=verbose)

    Returns:
        Configured logger instance
    """
    # Create main logger
    logger = logging.getLogger("hagrid")
    logger.setLevel(getattr(logging, log_level.upper()))
    logger.propagate = False

    # Clear existing handlers to avoid duplicates
    logger.handlers.clear()

    # Formatter with source file identification
    formatter = logging.Formatter(
        "%(asctime)s | %(name)s | %(levelname)s | %(filename)s:%(lineno)d | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File handler (optional)
    if log_to_file and log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        file_handler = logging.FileHandler(log_path, encoding="utf-8")
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    # Configure Agno logging to use our logger
    try:
        from agno.utils.log import configure_agno_logging

        configure_agno_logging(
            custom_default_logger=logger,
            custom_agent_logger=logger,
            custom_team_logger=logger,
            custom_workflow_logger=logger,
        )
    except ImportError:
        logger.warning("agno.utils.log not available, skipping Agno logging configuration")

    # Set AGNO_DEBUG environment variable
    if agno_debug:
        os.environ["AGNO_DEBUG"] = "true"
        if agno_debug_level >= 2:
            os.environ["AGNO_DEBUG_LEVEL"] = "2"

    return logger


def get_logger(name: str = "hagrid") -> logging.Logger:
    """
    Get a child logger with the given name.

    Args:
        name: Logger name (will be prefixed with 'hagrid.')

    Returns:
        Logger instance
    """
    if name == "hagrid":
        return logging.getLogger("hagrid")
    return logging.getLogger(f"hagrid.{name}")
