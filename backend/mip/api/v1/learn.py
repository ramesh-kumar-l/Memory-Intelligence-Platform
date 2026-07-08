"""Learn (Phase 4 task 3, FR-API-001): update derived semantic knowledge and,
optionally, mature the trust evidence chain. Supports Idempotency-Key like
Create/Update (05-api-design.md).
"""

from __future__ import annotations

import asyncio
from collections.abc import Callable

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from mip.api.middleware.auth import ensure_namespace_allowed
from mip.api.responses import envelope
from mip.api.v1.idempotency import body_hash, idempotent_replay, idempotent_store
from mip.api.v1.intelligence_schemas import LearnRequest
from mip.engines.learning.engine import LearnEngine
from mip.engines.memory_manager.engine import MemoryManager

router = APIRouter()


async def _run[T](fn: Callable[[], T]) -> T:
    return await asyncio.to_thread(fn)


@router.post("/learn")
async def learn_memory(request: Request, payload: LearnRequest) -> JSONResponse:
    request_id, trace_id = request.state.request_id, request.state.trace_id
    endpoint = "POST /v1/learn"
    request_hash = body_hash(payload.model_dump_json())
    key, cached = await idempotent_replay(request, endpoint, request_hash)
    if cached is not None:
        return cached
    manager: MemoryManager = request.app.state.memory_manager
    namespace = await _run(lambda: manager.peek_namespace(payload.memory_id))
    if namespace is not None:
        ensure_namespace_allowed(request, namespace)
    engine: LearnEngine = request.app.state.learn_engine
    memory = await _run(
        lambda: engine.learn(
            payload.memory_id,
            derived=payload.derived,
            new_evidence=payload.new_evidence,
            verifier=payload.verifier,
            reason=payload.reason,
            actor=payload.actor,
            request_id=request_id,
            trace_id=trace_id,
        )
    )
    body = envelope(request, memory.to_public_dict())
    await idempotent_store(request, key, endpoint, request_hash, 200, body)
    return JSONResponse(body, status_code=200)
