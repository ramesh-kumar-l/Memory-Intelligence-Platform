"""In-memory sliding-window rate limiting (ADR-0007).

Single-process, keyed by API key (falling back to client IP when
unauthenticated). Matches MIP's single-writer SQLite deployment model — a
distributed store (e.g. Redis) is only needed if MIP is ever run as multiple
worker processes/instances sharing one limit, which is out of scope here.
Disabled by default.
"""

from __future__ import annotations

import threading
import time
from collections import defaultdict, deque

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response
from starlette.types import ASGIApp

from mip.api.responses import error_response
from mip.core import errors

_WINDOW_SECONDS = 60.0


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp, *, enabled: bool, requests_per_minute: int) -> None:
        super().__init__(app)
        self._enabled = enabled
        self._limit = requests_per_minute
        self._windows: dict[str, deque[float]] = defaultdict(deque)
        self._lock = threading.Lock()

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if not self._enabled:
            return await call_next(request)
        identity = _client_identity(request)
        now = time.monotonic()
        with self._lock:
            window = self._windows[identity]
            cutoff = now - _WINDOW_SECONDS
            while window and window[0] < cutoff:
                window.popleft()
            if len(window) >= self._limit:
                retry_after = max(1, round(_WINDOW_SECONDS - (now - window[0])))
                response = error_response(request, errors.rate_limit_exceeded())
                response.headers["Retry-After"] = str(retry_after)
                return response
            window.append(now)
        return await call_next(request)


def _client_identity(request: Request) -> str:
    api_key = request.headers.get("X-API-Key")
    if api_key:
        return api_key
    authorization = request.headers.get("Authorization")
    if authorization:
        return authorization
    return request.client.host if request.client else "unknown"
