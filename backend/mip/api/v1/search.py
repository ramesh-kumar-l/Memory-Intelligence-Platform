"""Search (Phase 2 task 1-3): keyword/semantic/hybrid modes, continuation-token
pagination. Every item carries its own score breakdown — search results are
explainable by construction (FR-API-007), independent of the /v1/explain endpoint.
"""

from __future__ import annotations

import asyncio
from collections.abc import Callable

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from mip.api.middleware.auth import resolve_scoped_namespace
from mip.api.responses import json_response
from mip.api.v1.pagination import encode_search_token
from mip.api.v1.retrieval_common import resolve_cursor
from mip.api.v1.retrieval_schemas import SearchRequest
from mip.core import errors
from mip.engines.retrieval.engine import RetrievalEngine

router = APIRouter()


async def _run[T](fn: Callable[[], T]) -> T:
    return await asyncio.to_thread(fn)


@router.post("/search")
async def search_memories(request: Request, payload: SearchRequest) -> JSONResponse:
    settings = request.app.state.settings
    retrieval: RetrievalEngine = request.app.state.retrieval_engine
    query, mode, namespace, offset = resolve_cursor(
        query=payload.query,
        mode=payload.mode,
        namespace=payload.namespace,
        continuation_token=payload.continuation_token,
    )
    limit = min(payload.limit or settings.search_default_limit, settings.search_max_limit)
    if limit < 1:
        raise errors.invalid_request([{"field": "limit", "message": "must be >= 1"}])
    namespace = resolve_scoped_namespace(request, namespace)
    results, has_more = await _run(
        lambda: retrieval.search(query, mode=mode, namespace=namespace, limit=limit, offset=offset)
    )
    next_token = (
        encode_search_token(query=query, mode=mode, namespace=namespace, offset=offset + limit)
        if has_more
        else None
    )
    items = [
        {
            "memory_id": result.memory_id,
            "score": result.score,
            "explanation": {
                "mode": mode,
                "keyword_score": result.keyword_score,
                "semantic_score": result.semantic_score,
            },
        }
        for result in results
    ]
    data = {
        "query": query,
        "mode": mode,
        "items": items,
        "complete": not has_more,
        "continuation_token": next_token,
    }
    return json_response(request, data)
