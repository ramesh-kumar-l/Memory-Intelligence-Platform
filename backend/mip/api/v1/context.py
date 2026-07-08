"""BuildContext (Phase 2 task 5): assembles a task-specific Context Package."""

from __future__ import annotations

import asyncio
from collections.abc import Callable
from typing import Any

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from mip.api.responses import json_response
from mip.api.v1.pagination import encode_search_token
from mip.api.v1.retrieval_common import resolve_cursor
from mip.api.v1.retrieval_schemas import ContextRequest
from mip.core import errors
from mip.engines.context.engine import ContextEngine

router = APIRouter()


async def _run[T](fn: Callable[[], T]) -> T:
    return await asyncio.to_thread(fn)


@router.post("/context")
async def build_context(request: Request, payload: ContextRequest) -> JSONResponse:
    settings = request.app.state.settings
    context_engine: ContextEngine = request.app.state.context_engine
    query, mode, namespace, offset = resolve_cursor(
        query=payload.query,
        mode=payload.mode,
        namespace=payload.namespace,
        continuation_token=payload.continuation_token,
    )
    limit = min(payload.limit or settings.context_default_limit, settings.context_max_limit)
    if limit < 1:
        raise errors.invalid_request([{"field": "limit", "message": "must be >= 1"}])
    package: dict[str, Any] = await _run(
        lambda: context_engine.build_context(
            query, namespace=namespace, mode=mode, limit=limit, offset=offset
        )
    )
    has_more = not package["complete"]
    next_token = (
        encode_search_token(query=query, mode=mode, namespace=namespace, offset=offset + limit)
        if has_more
        else None
    )
    package["continuation_token"] = next_token
    return json_response(request, package)
