"""In-memory metrics collector with counters, gauges, and histograms."""

from __future__ import annotations

import functools
import time
from typing import Any, Callable, Dict, List, Optional


class MetricsCollector:
    """Collects metrics in memory: counters, gauges, and histograms.

    Histogram values are bounded by max_values per metric. When exceeded,
    the oldest values are discarded.
    """

    def __init__(self, max_values: int = 10000) -> None:
        self._counters: Dict[str, Dict[str, Any]] = {}
        self._gauges: Dict[str, Dict[str, Any]] = {}
        self._histograms: Dict[str, Dict[str, Any]] = {}
        self._max_values = max_values

    def counter(
        self, name: str, value: int = 1, tags: Optional[Dict[str, str]] = None
    ) -> None:
        """Increment a counter metric."""
        key = self._make_key(name, tags)
        if key not in self._counters:
            self._counters[key] = {"name": name, "value": 0, "tags": tags}
        self._counters[key]["value"] += value

    def gauge(
        self, name: str, value: float, tags: Optional[Dict[str, str]] = None
    ) -> None:
        """Set a gauge metric to a specific value."""
        key = self._make_key(name, tags)
        self._gauges[key] = {"name": name, "value": value, "tags": tags}

    def histogram(
        self, name: str, value: float, tags: Optional[Dict[str, str]] = None
    ) -> None:
        """Record a value in a histogram metric.

        When max_values is exceeded, the oldest values are discarded.
        """
        key = self._make_key(name, tags)
        if key not in self._histograms:
            self._histograms[key] = {"name": name, "values": [], "tags": tags}
        values = self._histograms[key]["values"]
        values.append(value)
        if len(values) > self._max_values:
            self._histograms[key]["values"] = values[-self._max_values:]

    def get_metrics(self) -> Dict[str, Any]:
        """Return all collected metrics."""
        return {
            "counters": dict(self._counters),
            "gauges": dict(self._gauges),
            "histograms": dict(self._histograms),
        }

    def reset(self) -> None:
        """Clear all collected metrics."""
        self._counters.clear()
        self._gauges.clear()
        self._histograms.clear()

    def _make_key(self, name: str, tags: Optional[Dict[str, str]]) -> str:
        """Create a unique key from name and tags."""
        if tags:
            tag_str = ",".join(f"{k}={v}" for k, v in sorted(tags.items()))
            return f"{name}|{tag_str}"
        return name


def timed(metric_name: str, collector: MetricsCollector) -> Callable:
    """Decorator that records function execution time as a histogram metric."""

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            start = time.time()
            try:
                return func(*args, **kwargs)
            finally:
                duration = time.time() - start
                collector.histogram(metric_name, duration)

        @functools.wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            start = time.time()
            try:
                return await func(*args, **kwargs)
            finally:
                duration = time.time() - start
                collector.histogram(metric_name, duration)

        import asyncio

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    return decorator
