"""Memory CRUD + lifecycle endpoints (Phase 1 canonical operations).

Routes are async; engine calls run in the thread pool so SQLite access never
blocks the event loop. Idempotency-Key semantics: a repeated key returns the
original stored result; the same key with a different payload is MEM-4003.
"""

from __future__ import annotations

import asyncio
from collections.abc import Callable

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from mip.api.middleware.auth import ensure_namespace_allowed, resolve_scoped_namespace
from mip.api.responses import envelope, json_response
from mip.api.v1.idempotency import body_hash as _body_hash
from mip.api.v1.idempotency import idempotent_replay as _idempotent_replay
from mip.api.v1.idempotency import idempotent_store as _idempotent_store
from mip.api.v1.pagination import decode_token, encode_token
from mip.api.v1.schemas import CreateMemoryRequest, UpdateMemoryRequest
from mip.core import errors
from mip.core.states import MemoryState
from mip.engines.knowledge.graph import GraphEngine
from mip.engines.memory_manager.engine import MemoryManager

router = APIRouter()


async def _run[T](fn: Callable[[], T]) -> T:
    return await asyncio.to_thread(fn)


def _manager(request: Request) -> MemoryManager:
    manager: MemoryManager = request.app.state.memory_manager
    return manager


def _ids(request: Request) -> tuple[str, str]:
    return request.state.request_id, request.state.trace_id


@router.post("/memories", status_code=201)
async def create_memory(request: Request, payload: CreateMemoryRequest) -> JSONResponse:
    ensure_namespace_allowed(request, payload.namespace)
    request_id, trace_id = _ids(request)
    endpoint = "POST /v1/memories"
    request_hash = _body_hash(payload.model_dump_json())
    key, cached = await _idempotent_replay(request, endpoint, request_hash)
    if cached is not None:
        return cached
    manager = _manager(request)
    spec = payload.to_spec()
    memory = await _run(
        lambda: manager.create_memory(spec, request_id=request_id, trace_id=trace_id)
    )
    body = envelope(request, memory.to_public_dict())
    await _idempotent_store(request, key, endpoint, request_hash, 201, body)
    return JSONResponse(body, status_code=201)


@router.get("/memories")
async def list_memories(
    request: Request,
    namespace: str | None = None,
    state: str | None = None,
    limit: int | None = None,
    continuation_token: str | None = None,
) -> JSONResponse:
    settings = request.app.state.settings
    state_filter: MemoryState | None = None
    if state is not None:
        try:
            state_filter = MemoryState(state)
        except ValueError as exc:
            raise errors.invalid_request(
                [{"field": "state", "message": f"unknown state {state!r}"}]
            ) from exc
    page_size = min(limit or settings.list_default_limit, settings.list_max_limit)
    if page_size < 1:
        raise errors.invalid_request([{"field": "limit", "message": "must be >= 1"}])
    namespace = resolve_scoped_namespace(request, namespace)
    after = decode_token(continuation_token) if continuation_token else None
    manager = _manager(request)
    records, has_more = await _run(
        lambda: manager.list_memories(
            namespace=namespace, state=state_filter, limit=page_size, after_memory_id=after
        )
    )
    next_token = encode_token(records[-1].memory_id) if has_more and records else None
    data = {
        "items": [record.model_dump(mode="json") for record in records],
        "complete": not has_more,
        "continuation_token": next_token,
    }
    return json_response(request, data)


@router.get("/memories/{memory_id}")
async def get_memory(request: Request, memory_id: str, version: int | None = None) -> JSONResponse:
    if version is not None and version < 1:
        raise errors.invalid_request([{"field": "version", "message": "must be >= 1"}])
    manager = _manager(request)
    memory = await _run(lambda: manager.get_memory(memory_id, version))
    ensure_namespace_allowed(request, memory.identity.namespace)
    return json_response(request, memory.to_public_dict())


@router.get("/memories/{memory_id}/versions")
async def list_versions(request: Request, memory_id: str) -> JSONResponse:
    manager = _manager(request)
    namespace = await _run(lambda: manager.peek_namespace(memory_id))
    if namespace is not None:
        ensure_namespace_allowed(request, namespace)
    versions = await _run(lambda: manager.list_versions(memory_id))
    data = {"memory_id": memory_id, "versions": [v.model_dump(mode="json") for v in versions]}
    return json_response(request, data)


@router.get("/memories/{memory_id}/relationships")
async def list_relationships(request: Request, memory_id: str) -> JSONResponse:
    """Graph edges touching one memory (Phase 4 task 1, ADR-0006) — a read-only
    convenience view over the regenerable relationship-graph projection.
    """
    manager = _manager(request)
    graph: GraphEngine = request.app.state.graph_engine
    memory = await _run(lambda: manager.get_memory(memory_id))  # 404/410 semantics
    ensure_namespace_allowed(request, memory.identity.namespace)
    edges = await _run(lambda: graph.relationships_for(memory_id))
    data = {
        "memory_id": memory_id,
        "relationships": [edge.model_dump(mode="json") for edge in edges],
    }
    return json_response(request, data)


@router.patch("/memories/{memory_id}")
async def update_memory(
    request: Request, memory_id: str, payload: UpdateMemoryRequest
) -> JSONResponse:
    request_id, trace_id = _ids(request)
    if_match = request.headers.get("If-Match")
    if if_match is None:
        raise errors.missing_precondition("If-Match")
    try:
        expected_version = int(if_match.strip().strip('"'))
    except ValueError as exc:
        raise errors.invalid_request(
            [{"field": "If-Match", "message": "must be an integer version"}]
        ) from exc
    endpoint = f"PATCH /v1/memories/{memory_id}"
    request_hash = _body_hash(str(expected_version), payload.model_dump_json())
    key, cached = await _idempotent_replay(request, endpoint, request_hash)
    if cached is not None:
        return cached
    manager = _manager(request)
    namespace = await _run(lambda: manager.peek_namespace(memory_id))
    if namespace is not None:
        ensure_namespace_allowed(request, namespace)
    spec = payload.to_spec()
    memory = await _run(
        lambda: manager.update_memory(
            memory_id,
            spec,
            expected_version=expected_version,
            request_id=request_id,
            trace_id=trace_id,
        )
    )
    body = envelope(request, memory.to_public_dict())
    await _idempotent_store(request, key, endpoint, request_hash, 200, body)
    return JSONResponse(body, status_code=200)


@router.delete("/memories/{memory_id}")
async def delete_memory(request: Request, memory_id: str) -> JSONResponse:
    request_id, trace_id = _ids(request)
    manager = _manager(request)
    namespace = await _run(lambda: manager.peek_namespace(memory_id))
    if namespace is not None:
        ensure_namespace_allowed(request, namespace)
    result = await _run(
        lambda: manager.delete_memory(memory_id, actor=request_id, trace_id=trace_id)
    )
    return json_response(request, result)


@router.post("/memories/{memory_id}/archive")
async def archive_memory(request: Request, memory_id: str) -> JSONResponse:
    request_id, trace_id = _ids(request)
    manager = _manager(request)
    namespace = await _run(lambda: manager.peek_namespace(memory_id))
    if namespace is not None:
        ensure_namespace_allowed(request, namespace)
    memory = await _run(
        lambda: manager.archive_memory(memory_id, actor=request_id, trace_id=trace_id)
    )
    return json_response(request, memory.to_public_dict())


@router.post("/memories/{memory_id}/restore")
async def restore_memory(request: Request, memory_id: str) -> JSONResponse:
    request_id, trace_id = _ids(request)
    manager = _manager(request)
    namespace = await _run(lambda: manager.peek_namespace(memory_id))
    if namespace is not None:
        ensure_namespace_allowed(request, namespace)
    memory = await _run(
        lambda: manager.restore_memory(memory_id, actor=request_id, trace_id=trace_id)
    )
    return json_response(request, memory.to_public_dict())
