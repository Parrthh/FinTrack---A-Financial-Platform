"""Minimal in-memory sliding-window rate limiter for auth endpoints.

Per-process only, which is fine for a single free-tier instance. If the API
ever scales past one instance, move this to Redis (already in the stack for
Phase 2 caching/queues).
"""

import time
from collections import defaultdict, deque

from fastapi import HTTPException, Request, status

from app.config import get_settings
from app.logging_config import app_log

settings = get_settings()

_attempts: dict[str, deque[float]] = defaultdict(deque)


def _client_ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def enforce_auth_rate_limit(request: Request) -> None:
    """FastAPI dependency: raise 429 when an IP exceeds the auth attempt budget."""
    ip = _client_ip(request)
    now = time.monotonic()
    window = settings.auth_rate_limit_window_seconds
    bucket = _attempts[ip]
    while bucket and now - bucket[0] > window:
        bucket.popleft()
    if len(bucket) >= settings.auth_rate_limit_attempts:
        app_log.warning("rate_limit_hit", ip=ip, path=request.url.path)
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many attempts. Please try again shortly.",
        )
    bucket.append(now)
