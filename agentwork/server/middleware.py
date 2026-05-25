"""Middleware for API key auth, rate limiting, and request logging."""

from __future__ import annotations

import logging
import time
from collections import defaultdict
from typing import Any, Callable, Dict, Optional

logger = logging.getLogger(__name__)

try:
    from fastapi import FastAPI, Request, HTTPException
    from fastapi.responses import JSONResponse
    from starlette.middleware.base import BaseHTTPMiddleware

    HAS_FASTAPI = True
except ImportError:
    HAS_FASTAPI = False


def add_api_key_auth(app: Any, api_keys: list[str]) -> None:
    """Add API key authentication middleware.

    Checks for X-API-Key header on all requests (except /health).
    """
    if not HAS_FASTAPI:
        return

    @app.middleware("http")
    async def api_key_middleware(request: Request, call_next: Callable) -> Any:
        if request.url.path.endswith("/health"):
            return await call_next(request)

        api_key = request.headers.get("X-API-Key")
        if api_key not in api_keys:
            return JSONResponse(
                status_code=401,
                content={"detail": "Invalid or missing API key"},
            )
        return await call_next(request)


def add_rate_limiter(
    app: Any, max_requests: int = 100, window_seconds: float = 60.0
) -> None:
    """Add rate limiting middleware.

    Limits requests per client IP within a time window.
    """
    if not HAS_FASTAPI:
        return

    request_counts: Dict[str, list[float]] = defaultdict(list)

    @app.middleware("http")
    async def rate_limit_middleware(request: Request, call_next: Callable) -> Any:
        client_ip = request.client.host if request.client else "unknown"
        now = time.time()
        window_start = now - window_seconds

        # Clean old entries
        request_counts[client_ip] = [
            t for t in request_counts[client_ip] if t > window_start
        ]

        if len(request_counts[client_ip]) >= max_requests:
            return JSONResponse(
                status_code=429,
                content={"detail": "Rate limit exceeded"},
            )

        request_counts[client_ip].append(now)
        return await call_next(request)


def add_request_logger(app: Any) -> None:
    """Add request logging middleware.

    Logs method, path, status code, and duration for each request.
    """
    if not HAS_FASTAPI:
        return

    @app.middleware("http")
    async def logging_middleware(request: Request, call_next: Callable) -> Any:
        start_time = time.time()
        response = await call_next(request)
        duration_ms = (time.time() - start_time) * 1000
        logger.info(
            "%s %s -> %d (%.1fms)",
            request.method,
            request.url.path,
            response.status_code,
            duration_ms,
        )
        return response
