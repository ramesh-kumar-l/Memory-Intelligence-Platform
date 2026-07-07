"""Response envelope and error envelope builders (05-api-design.md).

Every success body carries request_id, schema_version, processing_time_ms;
every failure is the structured MEM-* error envelope. Clients key on `code`.
"""

from __future__ import annotations

import time
from typing import Any

from fastapi import Request
from fastapi.responses import JSONResponse

from mip.core.errors import MIPError


def envelope(request: Request, data: Any) -> dict[str, Any]:
    started: float = getattr(request.state, "start", time.perf_counter())
    elapsed_ms = (time.perf_counter() - started) * 1000
    settings = request.app.state.settings
    return {
        "data": data,
        "request_id": _request_id(request),
        "schema_version": settings.schema_version,
        "processing_time_ms": round(elapsed_ms, 3),
    }


def json_response(request: Request, data: Any, status_code: int = 200) -> JSONResponse:
    return JSONResponse(envelope(request, data), status_code=status_code)


def error_response(request: Request, exc: MIPError) -> JSONResponse:
    body = {"error": exc.to_error_dict(), "request_id": _request_id(request)}
    return JSONResponse(body, status_code=exc.http_status)


def _request_id(request: Request) -> str:
    return str(getattr(request.state, "request_id", "unknown"))
