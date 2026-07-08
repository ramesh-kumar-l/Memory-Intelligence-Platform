"""Idempotency-Key replay/store helpers shared by Create/Update/Learn routes
(05-api-design.md: "Idempotency-Key required semantics for Create/Update/Learn
retries"). A repeated key returns the original stored result; the same key
with a different payload is MEM-4003.
"""

from __future__ import annotations

import asyncio
import hashlib
import json
from collections.abc import Callable
from typing import Any

from fastapi import Request
from fastapi.responses import JSONResponse

from mip.core import errors
from mip.storage.interfaces import IdempotencyStoreABC


async def run[T](fn: Callable[[], T]) -> T:
    return await asyncio.to_thread(fn)


def idempotency_store(request: Request) -> IdempotencyStoreABC:
    store: IdempotencyStoreABC = request.app.state.idempotency
    return store


def body_hash(*parts: str) -> str:
    digest = hashlib.sha256()
    for part in parts:
        digest.update(part.encode())
    return digest.hexdigest()


async def idempotent_replay(
    request: Request, endpoint: str, request_hash: str
) -> tuple[str | None, JSONResponse | None]:
    """Return (key, cached response). Key is None when the header is absent."""
    key = request.headers.get("Idempotency-Key")
    if key is None:
        return None, None
    store = idempotency_store(request)
    cached = await run(lambda: store.lookup(key, endpoint))
    if cached is None:
        return key, None
    if cached.request_hash != request_hash:
        raise errors.idempotency_key_reuse(key)
    body: dict[str, Any] = json.loads(cached.response_json)
    return key, JSONResponse(body, status_code=cached.status_code)


async def idempotent_store(
    request: Request,
    key: str | None,
    endpoint: str,
    request_hash: str,
    status_code: int,
    body: dict[str, Any],
) -> None:
    if key is None:
        return
    store = idempotency_store(request)
    clock = request.app.state.clock
    await run(
        lambda: store.store(key, endpoint, request_hash, status_code, json.dumps(body), clock.now())
    )
