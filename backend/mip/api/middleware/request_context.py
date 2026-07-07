"""Request context: request_id / trace_id propagation, timing, and
MIP-API-Version negotiation (unknown versions get a structured error).
"""

from __future__ import annotations

import time
from uuid import uuid4

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.types import ASGIApp

from mip.api.responses import error_response
from mip.core import errors


class RequestContextMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp, supported_versions: tuple[str, ...]) -> None:
        super().__init__(app)
        self._supported = supported_versions

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        request.state.start = time.perf_counter()
        request.state.request_id = request.headers.get("X-Request-Id") or uuid4().hex
        request.state.trace_id = request.headers.get("X-Trace-Id") or uuid4().hex

        requested_version = request.headers.get("MIP-API-Version")
        if requested_version is not None and requested_version not in self._supported:
            return error_response(
                request, errors.unsupported_api_version(requested_version, self._supported)
            )

        response = await call_next(request)
        response.headers["X-Request-Id"] = request.state.request_id
        return response
