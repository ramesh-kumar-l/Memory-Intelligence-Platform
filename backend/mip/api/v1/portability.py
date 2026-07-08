"""Export/Import (Phase 4 task 4, FR-API-001): backup, migration, and the
validation pipeline required before any imported memory is materialized
(ADR-0006).
"""

from __future__ import annotations

import asyncio
from collections.abc import Callable
from typing import Any

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from mip.api.responses import json_response
from mip.api.v1.intelligence_schemas import ExportRequest, ImportRequest
from mip.engines.portability.export_engine import ExportEngine
from mip.engines.portability.import_engine import ImportEngine

router = APIRouter()


async def _run[T](fn: Callable[[], T]) -> T:
    return await asyncio.to_thread(fn)


@router.post("/export")
async def export_memories(request: Request, payload: ExportRequest) -> JSONResponse:
    engine: ExportEngine = request.app.state.export_engine
    bundle = await _run(lambda: engine.export(namespace=payload.namespace))
    return json_response(request, bundle)


@router.post("/import")
async def import_memories(request: Request, payload: ImportRequest) -> JSONResponse:
    engine: ImportEngine = request.app.state.import_engine
    request_id, trace_id = request.state.request_id, request.state.trace_id
    bundle: dict[str, Any] = {"memories": payload.memories}
    report = await _run(lambda: engine.import_bundle(bundle, actor=request_id, trace_id=trace_id))
    return json_response(request, report)
