"""Explain (Phase 2 task 4, FR-API-007): evidence, confidence, freshness,
provenance, and — when a query is given — the ranking explanation.
"""

from __future__ import annotations

import asyncio
from collections.abc import Callable
from typing import Any

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from mip.api.responses import json_response
from mip.api.v1.retrieval_schemas import ExplainRequest
from mip.engines.memory_manager.engine import MemoryManager
from mip.engines.retrieval.engine import RetrievalEngine
from mip.engines.retrieval.explain import build_explanation
from mip.engines.trust.scoring import TrustEngine

router = APIRouter()


async def _run[T](fn: Callable[[], T]) -> T:
    return await asyncio.to_thread(fn)


@router.post("/explain")
async def explain_memory(request: Request, payload: ExplainRequest) -> JSONResponse:
    manager: MemoryManager = request.app.state.memory_manager
    trust: TrustEngine = request.app.state.trust_engine
    retrieval: RetrievalEngine = request.app.state.retrieval_engine

    def _build() -> dict[str, Any]:
        memory = manager.get_memory(payload.memory_id)
        now = request.app.state.clock.now()
        return build_explanation(
            memory,
            trust=trust,
            retrieval=retrieval,
            query=payload.query,
            mode=payload.mode,
            now=now,
        )

    explanation = await _run(_build)
    return json_response(request, explanation)
