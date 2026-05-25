"""Structured JSON logger with trace context integration."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Any

from agentwork.observability.tracing import current_trace


class _JSONFormatter(logging.Formatter):
    """Formats log records as JSON strings."""

    def format(self, record: logging.LogRecord) -> str:
        trace = current_trace()
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "logger": record.name,
            "trace_id": trace.trace_id if trace else None,
            "span_id": trace.span_id if trace else None,
        }
        # Include extra fields
        extra = getattr(record, "_extra", {})
        if extra:
            entry.update(extra)
        return json.dumps(entry)


class StructuredLogger:
    """JSON-formatted structured logger with trace context."""

    def __init__(self, name: str) -> None:
        self._logger = logging.getLogger(name)
        if not self._logger.handlers:
            handler = logging.StreamHandler()
            handler.setFormatter(_JSONFormatter())
            self._logger.addHandler(handler)
            self._logger.setLevel(logging.DEBUG)

    @classmethod
    def get_logger(cls, name: str) -> "StructuredLogger":
        """Get or create a StructuredLogger instance."""
        return cls(name)

    def info(self, message: str, **kwargs: Any) -> None:
        """Log at INFO level with optional extra fields."""
        self._log(logging.INFO, message, kwargs)

    def warning(self, message: str, **kwargs: Any) -> None:
        """Log at WARNING level with optional extra fields."""
        self._log(logging.WARNING, message, kwargs)

    def error(self, message: str, **kwargs: Any) -> None:
        """Log at ERROR level with optional extra fields."""
        self._log(logging.ERROR, message, kwargs)

    def debug(self, message: str, **kwargs: Any) -> None:
        """Log at DEBUG level with optional extra fields."""
        self._log(logging.DEBUG, message, kwargs)

    def _log(self, level: int, message: str, extra: dict) -> None:
        """Internal logging method."""
        record = self._logger.makeRecord(
            name=self._logger.name,
            level=level,
            fn="",
            lno=0,
            msg=message,
            args=(),
            exc_info=None,
        )
        record._extra = extra  # type: ignore[attr-defined]
        self._logger.handle(record)
