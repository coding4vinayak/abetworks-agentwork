"""Token bucket rate limiter with per-client tracking."""

from __future__ import annotations

import time
from typing import Any, Callable, Dict, Optional, Tuple

try:
    from fastapi import FastAPI, Request
    from fastapi.responses import JSONResponse

    HAS_FASTAPI = True
except ImportError:
    HAS_FASTAPI = False


class RateLimiter:
    """Token bucket rate limiter with per-client tracking.

    Each client gets a bucket that fills at `rate` tokens per second,
    up to a maximum of `capacity` tokens. Each request consumes one token.
    """

    def __init__(self, rate: float = 10.0, capacity: int = 10) -> None:
        self._rate = rate
        self._capacity = capacity
        self._buckets: Dict[str, Tuple[float, float]] = {}

    def allow(self, client_id: str) -> bool:
        """Check if a request from client_id is allowed.

        Refills the bucket based on elapsed time, then tries to consume one token.
        Returns True if the request is allowed.
        """
        now = time.time()
        tokens, last_refill = self._buckets.get(
            client_id, (float(self._capacity), now)
        )

        # Refill tokens based on elapsed time
        elapsed = now - last_refill
        tokens = min(self._capacity, tokens + elapsed * self._rate)

        if tokens >= 1.0:
            self._buckets[client_id] = (tokens - 1.0, now)
            return True
        else:
            self._buckets[client_id] = (tokens, last_refill)
            return False

    def get_retry_after(self, client_id: str) -> float:
        """Return seconds until the next token is available for client_id."""
        now = time.time()
        tokens, last_refill = self._buckets.get(
            client_id, (float(self._capacity), now)
        )

        # Refill tokens based on elapsed time
        elapsed = now - last_refill
        tokens = min(self._capacity, tokens + elapsed * self._rate)

        if tokens >= 1.0:
            return 0.0

        # Time until tokens reach 1.0
        needed = 1.0 - tokens
        return needed / self._rate

    def reset(self, client_id: Optional[str] = None) -> None:
        """Reset one or all client buckets."""
        if client_id is not None:
            self._buckets.pop(client_id, None)
        else:
            self._buckets.clear()


def add_rate_limit_middleware(
    app: Any,
    limiter: RateLimiter,
    key_func: Optional[Callable] = None,
) -> None:
    """Add rate limiting middleware to a FastAPI app.

    Returns 429 with Retry-After header when rate exceeded.
    key_func extracts client identity from request (default: X-API-Key header or client IP).
    """
    if not HAS_FASTAPI:
        return

    def default_key_func(request: Request) -> str:
        api_key = request.headers.get("X-API-Key")
        if api_key:
            return api_key
        return request.client.host if request.client else "unknown"

    actual_key_func = key_func or default_key_func

    @app.middleware("http")
    async def rate_limit_middleware(request: Request, call_next: Callable) -> Any:
        client_id = actual_key_func(request)
        if not limiter.allow(client_id):
            retry_after = limiter.get_retry_after(client_id)
            return JSONResponse(
                status_code=429,
                content={"detail": "Rate limit exceeded"},
                headers={"Retry-After": str(retry_after)},
            )
        return await call_next(request)
