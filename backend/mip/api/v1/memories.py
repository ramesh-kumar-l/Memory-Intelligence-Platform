"""Memory CRUD + lifecycle endpoints (Phase 1 canonical operations).

Routes are async; engine calls run in the thread pool so SQLite access never
blocks the event loop. Idempotency-Key semantics: a repeated key returns the
original stored result; the same key with a different payload is MEM-4003.
"""

from __future__ import annotations

import asyncio
import hashlib
import json
from collections.abc import Callable
from typing import Any

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from mip.api.responses import envelope, json_response
from mip.api.v1.pagination import decode_token, encode_token
from mip.api.v1.schemas import CreateMemoryRequest, UpdateMemoryRequest
from mip.core import errors
from mip.core.states import MemoryState
from mip.engines.memory_manager.engine import MemoryManager
from mip.storage.interfaces import IdempotencyStoreABC

router = APIRouter()


async def _run[T](fn: Callable[[], T]) -> T:
    return await asyncio.to_thread(fn)


def _manager(request: Request) -> MemoryManager:
    manager: MemoryManager = request.app.state.memory_manager
    return manager


def _idempotency(request: Request) -> IdempotencyStoreABC:
    store: IdempotencyStoreABC = request.app.state.idempotency
    return store


def _ids(request: Request) -> tuple[str, str]:
    return request.state.request_id, request.state.trace_id


def _body_hash(*parts: str) -> str:
    digest = hashlib.sha256()
    for part in parts:
        digest.update(part.encode())
    return digest.hexdigest()


async def _idempotent_replay(
    request: Request, endpoint: str, request_hash: str
) -> tuple[str | None, JSONResponse | None]:
    """Return (key, cached response). Key is None when the header is absent."""
    key = request.headers.get("Idempotency-Key")
    if key is None:
        return None, None
    store = _idempotency(request)
    cached = await _run(lambda: store.lookup(key, endpoint))
    if cached is None:
        return key, None
    if cached.request_hash != request_hash:
        raise errors.idempotency_key_reuse(key)
    body: dict[str, Any] = json.loads(cached.response_json)
    return key, JSONResponse(body, status_code=cached.status_code)


async def _idempotent_store(
    request: Request,
    key: str | None,
    endpoint: str,
    request_hash: str,
    status_code: int,
    body: dict[str, Any],
) -> None:
    if key is None:
        return
    store = _idempotency(request)
    clock = request.app.state.clock
    await _run(
        lambda: store.store(key, endpoint, request_hash, status_code, json.dumps(body), clock.now())
    )


@router.post("/memories", status_code=201)
async def create_memory(request: Request, payload: CreateMemoryRequest) -> JSONResponse:
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
    return json_response(request, memory.to_public_dict())


@router.get("/memories/{memory_id}/versions")
async def list_versions(request: Request, memory_id: str) -> JSONResponse:
    manager = _manager(request)
    versions = await _run(lambda: manager.list_versions(memory_id))
    data = {"memory_id": memory_id, "versions": [v.model_dump(mode="json") for v in versions]}
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
    result = await _run(
        lambda: manager.delete_memory(memory_id, actor=request_id, trace_id=trace_id)
    )
    return json_response(request, result)


@router.post("/memories/{memory_id}/archive")
async def archive_memory(request: Request, memory_id: str) -> JSONResponse:
    request_id, trace_id = _ids(request)
    manager = _manager(request)
    memory = await _run(
        lambda: manager.archive_memory(memory_id, actor=request_id, trace_id=trace_id)
    )
    return json_response(request, memory.to_public_dict())


@router.post("/memories/{memory_id}/restore")
async def restore_memory(request: Request, memory_id: str) -> JSONResponse:
    request_id, trace_id = _ids(request)
    manager = _manager(request)
    memory = await _run(
        lambda: manager.restore_memory(memory_id, actor=request_id, trace_id=trace_id)
    )
    return json_response(request, memory.to_public_dict())
