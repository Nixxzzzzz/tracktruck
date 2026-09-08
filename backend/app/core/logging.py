"""
Structured Application Logging.
Formats application and request logs into structured JSON for production observability
or human-readable format for local development.
"""

import json
import logging
import sys
from datetime import UTC, datetime
from typing import Any


class JSONFormatter(logging.Formatter):
    """Formats log records as single-line JSON objects."""

    SENSITIVE_KEYS = {
        "password",
        "password_hash",
        "token",
        "access_token",
        "refresh_token",
        "jwt_secret",
        "secret",
        "authorization",
    }

    def format(self, record: logging.LogRecord) -> str:
        log_entry: dict[str, Any] = {
            "timestamp": datetime.now(UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Include structured extra fields if present
        if hasattr(record, "request_id"):
            log_entry["request_id"] = record.request_id
        if hasattr(record, "user_id"):
            log_entry["user_id"] = record.user_id
        if hasattr(record, "route"):
            log_entry["route"] = record.route
        if hasattr(record, "method"):
            log_entry["method"] = record.method
        if hasattr(record, "status_code"):
            log_entry["status_code"] = record.status_code
        if hasattr(record, "duration_ms"):
            log_entry["duration_ms"] = record.duration_ms

        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)

        # Sanitize any accidental sensitive fields in extras
        for key in list(log_entry.keys()):
            if any(sensitive in key.lower() for sensitive in self.SENSITIVE_KEYS):
                log_entry[key] = "[REDACTED]"

        return json.dumps(log_entry)


def setup_logging(level: str = "INFO", json_format: bool = True) -> logging.Logger:
    """Configures root logger with JSON or standard formatter."""
    root_logger = logging.getLogger("aurelis")
    root_logger.setLevel(getattr(logging, level.upper(), logging.INFO))

    # Remove existing handlers to avoid duplicates
    root_logger.handlers.clear()

    handler = logging.StreamHandler(sys.stdout)
    if json_format:
        handler.setFormatter(JSONFormatter())
    else:
        handler.setFormatter(
            logging.Formatter(
                fmt="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
        )

    root_logger.addHandler(handler)
    return root_logger


logger = logging.getLogger("aurelis")
