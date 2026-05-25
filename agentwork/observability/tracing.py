"""Distributed tracing with context propagation via contextvars."""

from __future__ import annotations

import uuid
from contextvars import ContextVar
from typing import Optional

_current_trace: ContextVar[Optional["TraceContext"]] = ContextVar(
    "_current_trace", default=None
)


class TraceContext:
    """Represents a trace span with automatic ID generation.

    Can be used as a context manager to set/restore the active trace context.
    """

    def __init__(
        self,
        trace_id: Optional[str] = None,
        span_id: Optional[str] = None,
        parent_span_id: Optional[str] = None,
    ) -> None:
        self.trace_id = trace_id or str(uuid.uuid4())
        self.span_id = span_id or str(uuid.uuid4())
        self.parent_span_id = parent_span_id
        self._token = None

    def __enter__(self) -> "TraceContext":
        self._token = _current_trace.set(self)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        if self._token is not None:
            _current_trace.reset(self._token)
            self._token = None


def current_trace() -> Optional[TraceContext]:
    """Return the currently active TraceContext, or None if no context is set."""
    return _current_trace.get()
