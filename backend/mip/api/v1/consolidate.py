"""Consolidate (Phase 4 task 2, FR-API-001): merge duplicate memories via
relationships; history is preserved by construction (ADR-0006).
"""

from __future__ import annotations

import asyncio
from collections.abc import Callable

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from mip.api.responses import json_response
from mip.api.v1.intelligence_schemas import ConsolidateRequest
from mip.engines.knowledge.consolidate import ConsolidateEngine

router = APIRouter()


async def _run[T](fn: Callable[[], T]) -> T:
    return await asyncio.to_thread(fn)


@router.post("/consolidate")
async def consolidate_memories(request: Request, payload: ConsolidateRequest) -> JSONResponse:
    engine: ConsolidateEngine = request.app.state.consolidate_engine
    request_id, trace_id = request.state.request_id, request.state.trace_id
    memory = await _run(
        lambda: engine.consolidate(
            primary_memory_id=payload.primary_memory_id,
            duplicate_memory_ids=payload.duplicate_memory_ids,
            actor=request_id,
            request_id=request_id,
            trace_id=trace_id,
        )
    )
    return json_response(request, memory.to_public_dict())
