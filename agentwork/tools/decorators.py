"""Decorator to turn functions into Tool instances."""

from __future__ import annotations

from typing import Any, Callable, Optional, Tuple, Type

from agentwork.resilience.retry import RetryPolicy
from agentwork.tools.base import Tool


def tool(
    name: Optional[str] = None,
    description: str = "",
    retry_attempts: int = 0,
    retry_backoff: float = 1.0,
    retry_on: Optional[Tuple[Type[Exception], ...]] = None,
    fallback: Optional[Callable[..., Any]] = None,
    tags: Optional[list[str]] = None,
    timeout_seconds: Optional[float] = None,
) -> Callable[..., Any]:
    """Decorator to turn a function into a Tool with metadata and retry config.

    Usage:
        @tool(name="greet", description="Greets a person", retry_attempts=3)
        def greet(name: str) -> str:
            return f"Hello, {name}!"

    The decorated function becomes a Tool instance that can be passed to an Agent.
    """

    def decorator(func: Callable[..., Any]) -> Tool:
        tool_name = name or func.__name__
        tool_description = description or (func.__doc__ or "").strip()

        retry_policy: Optional[RetryPolicy] = None
        if retry_attempts > 0:
            retry_policy = RetryPolicy(
                max_attempts=retry_attempts,
                backoff_base=retry_backoff,
                retry_on=retry_on or (Exception,),
            )

        t = Tool(
            name=tool_name,
            description=tool_description,
            function=func,
            retry_policy=retry_policy,
            fallback=fallback,
            tags=tags or [],
            timeout_seconds=timeout_seconds,
        )
        # Preserve the original function reference for introspection
        t.__wrapped__ = func  # type: ignore[attr-defined]
        return t

    return decorator
