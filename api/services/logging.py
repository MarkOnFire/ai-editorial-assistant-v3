"""
Editorial Assistant v3.0 - Structured JSON Logging

Provides JSON-formatted logging for consistent API log output.
"""

import logging
import json
import os
from datetime import datetime, timezone
from typing import Any, Dict, Optional


class JSONFormatter(logging.Formatter):
    """Custom formatter that outputs logs in JSON format."""

    def format(self, record: logging.LogRecord) -> str:
        """
        Format a log record as JSON.

        Args:
            record: The log record to format

        Returns:
            JSON string with timestamp, level, logger, message, and extra fields
        """
        log_data: Dict[str, Any] = {
            "timestamp": datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "extra": {}
        }

        # Include any extra context passed via logger.info("msg", extra={...})
        standard_attrs = {
            'name', 'msg', 'args', 'created', 'filename', 'funcName', 'levelname',
            'levelno', 'lineno', 'module', 'msecs', 'message', 'pathname', 'process',
            'processName', 'relativeCreated', 'thread', 'threadName', 'exc_info',
            'exc_text', 'stack_info', 'getMessage', 'asctime', 'taskName'
        }

        for key, value in record.__dict__.items():
            if key not in standard_attrs:
                log_data["extra"][key] = value

        # Include exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_data)


# Track whether logging has been set up
_logging_configured = False


def setup_logging(level: Optional[str] = None) -> None:
    """
    Configure Python logging for JSON output.

    Args:
        level: Log level as string (DEBUG, INFO, WARNING, ERROR).
               If not specified, reads from LOG_LEVEL environment variable.
               Defaults to INFO if neither is provided.
    """
    global _logging_configured

    if level is None:
        level = os.getenv("LOG_LEVEL", "INFO")

    level_upper = level.upper()

    numeric_level = getattr(logging, level_upper, None)
    if not isinstance(numeric_level, int):
        raise ValueError(f"Invalid log level: {level}")

    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)

    # Remove existing handlers to avoid duplicates
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    console_handler = logging.StreamHandler()
    console_handler.setLevel(numeric_level)
    console_handler.setFormatter(JSONFormatter())

    root_logger.addHandler(console_handler)

    _logging_configured = True


def get_logger(name: str) -> logging.Logger:
    """
    Get a configured logger instance.

    Ensures logging is set up on first call.

    Args:
        name: Name for the logger (typically __name__)

    Returns:
        Configured logger instance
    """
    global _logging_configured

    if not _logging_configured:
        setup_logging()

    return logging.getLogger(name)
