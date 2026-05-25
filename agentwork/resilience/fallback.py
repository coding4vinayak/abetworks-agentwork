"""Fallback chain - tries multiple strategies until one succeeds."""

from __future__ import annotations

import logging
from typing import Any, Callable, List, Optional

from agentwork.core.exceptions import AgentError

logger = logging.getLogger(__name__)


class FallbackChain:
    """Tries an ordered list of callables until one succeeds.

    If all callables fail, returns a structured error result rather than crashing.
    """

    def __init__(
        self,
        strategies: Optional[List[Callable[..., Any]]] = None,
        default: Optional[Any] = None,
    ) -> None:
        self.strategies: List[Callable[..., Any]] = strategies or []
        self.default = default

    def add(self, func: Callable[..., Any]) -> "FallbackChain":
        """Add a strategy to the fallback chain."""
        self.strategies.append(func)
        return self

    def execute(self, *args: Any, **kwargs: Any) -> Any:
        """Execute the fallback chain.

        Tries each strategy in order. Returns the result of the first
        successful one. If all fail, returns the default value or raises.
        """
        errors: List[Exception] = []

        for i, strategy in enumerate(self.strategies):
            try:
                result = strategy(*args, **kwargs)
                logger.debug(
                    "Fallback strategy %d (%s) succeeded",
                    i,
                    strategy.__name__ if hasattr(strategy, "__name__") else str(strategy),
                )
                return result
            except Exception as e:
                logger.warning(
                    "Fallback strategy %d (%s) failed: %s",
                    i,
                    strategy.__name__ if hasattr(strategy, "__name__") else str(strategy),
                    str(e),
                )
                errors.append(e)

        if self.default is not None:
            return self.default

        raise AgentError(
            f"All {len(self.strategies)} fallback strategies failed",
            details=[str(e) for e in errors],
        )

    async def execute_async(self, *args: Any, **kwargs: Any) -> Any:
        """Execute the fallback chain with async strategies."""
        errors: List[Exception] = []

        for i, strategy in enumerate(self.strategies):
            try:
                import asyncio

                if asyncio.iscoroutinefunction(strategy):
                    result = await strategy(*args, **kwargs)
                else:
                    result = strategy(*args, **kwargs)
                logger.debug("Async fallback strategy %d succeeded", i)
                return result
            except Exception as e:
                logger.warning(
                    "Async fallback strategy %d failed: %s", i, str(e)
                )
                errors.append(e)

        if self.default is not None:
            return self.default

        raise AgentError(
            f"All {len(self.strategies)} fallback strategies failed",
            details=[str(e) for e in errors],
        )
