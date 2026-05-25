"""Instrumentation decorator for automatic span and metric creation."""

from __future__ import annotations

import asyncio
import functools
import time
from typing import Any, Callable, Optional

from agentwork.observability.metrics import MetricsCollector
from agentwork.observability.tracing import TraceContext, current_trace


def instrument(
    name: Optional[str] = None,
    collector: Optional[MetricsCollector] = None,
) -> Callable:
    """Decorator that instruments a function with tracing and optional metrics.

    Creates a TraceContext span, records duration as a histogram metric
    (if a collector is provided), and handles exceptions gracefully.

    Works with both sync and async functions.
    """

    def decorator(func: Callable) -> Callable:
        span_name = name or func.__name__

        @functools.wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            parent = current_trace()
            ctx = TraceContext(
                trace_id=parent.trace_id if parent else None,
                parent_span_id=parent.span_id if parent else None,
            )
            with ctx:
                start = time.time()
                try:
                    result = func(*args, **kwargs)
                    return result
                except Exception:
                    raise
                finally:
                    duration = time.time() - start
                    if collector is not None:
                        collector.histogram(f"{span_name}.duration", duration)

        @functools.wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            parent = current_trace()
            ctx = TraceContext(
                trace_id=parent.trace_id if parent else None,
                parent_span_id=parent.span_id if parent else None,
            )
            with ctx:
                start = time.time()
                try:
                    result = await func(*args, **kwargs)
                    return result
                except Exception:
                    raise
                finally:
                    duration = time.time() - start
                    if collector is not None:
                        collector.histogram(f"{span_name}.duration", duration)

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    return decorator
