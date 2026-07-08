"""Operational endpoints: health, version negotiation info, projection rebuild."""

from __future__ import annotations

import asyncio

from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse

import mip
from mip.api.middleware.auth import require_principal
from mip.api.responses import json_response
from mip.engines.memory_manager.engine import MemoryManager
from mip.storage.interfaces import TransactionManagerABC

router = APIRouter()


@router.get("/health")
async def health(request: Request) -> JSONResponse:
    transactions: TransactionManagerABC = request.app.state.transactions
    storage_ok = await asyncio.to_thread(transactions.ping)
    data = {"status": "ok" if storage_ok else "degraded", "storage": storage_ok}
    return json_response(request, data, status_code=200 if storage_ok else 503)


@router.get("/version")
async def version(request: Request) -> JSONResponse:
    settings = request.app.state.settings
    data = {
        "service_version": mip.__version__,
        "api_versions": list(settings.api_versions),
        "schema_version": settings.schema_version,
    }
    return json_response(request, data)


@router.post("/admin/rebuild-projections", dependencies=[Depends(require_principal)])
async def rebuild_projections(request: Request) -> JSONResponse:
    """Rebuild all projections from the event log; `identical: true` proves
    replay reproduces the exact pre-rebuild state (INV-CONS-004).
    """
    manager: MemoryManager = request.app.state.memory_manager
    report = await asyncio.to_thread(manager.rebuild_projections)
    return json_response(request, report)
