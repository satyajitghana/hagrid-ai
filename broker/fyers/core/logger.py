"""
Logging configuration for the Fyers SDK.
"""

import logging
import sys
from typing import Optional


def get_logger(
    name: str = "fyers",
    level: int = logging.INFO,
    format_string: Optional[str] = None,
) -> logging.Logger:
    """
    Get or create a logger instance for the Fyers SDK.
    
    Args:
        name: Logger name (will be prefixed with 'fyers.')
        level: Logging level (default: INFO)
        format_string: Custom format string for log messages
        
    Returns:
        Configured logger instance
    """
    # Ensure the name is prefixed with 'fyers.'
    if not name.startswith("fyers"):
        name = f"fyers.{name}"
    
    logger = logging.getLogger(name)
    
    # Only configure if no handlers exist
    if not logger.handlers:
        logger.setLevel(level)
        
        # Create console handler
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(level)
        
        # Create formatter
        if format_string is None:
            format_string = (
                "%(asctime)s | %(name)s | %(levelname)s | %(message)s"
            )
        formatter = logging.Formatter(format_string, datefmt="%Y-%m-%d %H:%M:%S")
        handler.setFormatter(formatter)
        
        logger.addHandler(handler)
        
        # Prevent propagation to root logger
        logger.propagate = False
    
    return logger


def configure_logging(
    level: int = logging.INFO,
    format_string: Optional[str] = None,
    log_file: Optional[str] = None,
) -> None:
    """
    Configure logging for all Fyers SDK loggers.
    
    Args:
        level: Logging level
        format_string: Custom format string
        log_file: Optional file path to write logs to
    """
    root_logger = logging.getLogger("fyers")
    root_logger.setLevel(level)
    
    # Clear existing handlers
    root_logger.handlers.clear()
    
    # Create formatter
    if format_string is None:
        format_string = (
            "%(asctime)s | %(name)s | %(levelname)s | %(message)s"
        )
    formatter = logging.Formatter(format_string, datefmt="%Y-%m-%d %H:%M:%S")
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # File handler (optional)
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
    
    root_logger.propagate = False


# Create default SDK logger
sdk_logger = get_logger("fyers.sdk")