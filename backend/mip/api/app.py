"""Application factory: wires adapters → engines → routes (dependency rule:
engines receive interfaces, concrete SQLite adapters are chosen only here).
"""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Response
from fastapi.exceptions import RequestValidationError

import mip
from mip.api.middleware.request_context import RequestContextMiddleware
from mip.api.responses import error_response
from mip.api.v1 import admin, memories
from mip.config import MIPSettings
from mip.core import errors
from mip.core.clock import SystemClock
from mip.engines.memory_manager.engine import MemoryManager
from mip.engines.memory_manager.locks import LockRegistry
from mip.engines.validation.engine import ValidationEngine
from mip.storage.sqlite.database import Database
from mip.storage.sqlite.event_store import SqliteEventStore
from mip.storage.sqlite.idempotency_store import SqliteIdempotencyStore
from mip.storage.sqlite.memory_repository import SqliteMemoryRepository

logger = logging.getLogger(__name__)


def create_app(settings: MIPSettings | None = None) -> FastAPI:
    active_settings = settings or MIPSettings()
    database = Database(active_settings.db_path)
    clock = SystemClock()
    validation = ValidationEngine(
        schema_version=active_settings.schema_version,
        encoding_version=active_settings.encoding_version,
        clock=clock,
    )
    manager = MemoryManager(
        event_store=SqliteEventStore(database),
        repository=SqliteMemoryRepository(database),
        transactions=database,
        locks=LockRegistry(),
        validation=validation,
        clock=clock,
        lock_timeout=active_settings.lock_timeout_seconds,
    )

    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncIterator[None]:
        yield
        database.close()

    app = FastAPI(title="Memory Intelligence Platform", version=mip.__version__, lifespan=lifespan)
    app.state.settings = active_settings
    app.state.memory_manager = manager
    app.state.idempotency = SqliteIdempotencyStore(database)
    app.state.transactions = database
    app.state.clock = clock

    app.add_middleware(RequestContextMiddleware, supported_versions=active_settings.api_versions)

    async def handle_mip_error(request: Request, exc: Exception) -> Response:
        if not isinstance(exc, errors.MIPError):  # pragma: no cover - handler is type-bound
            raise exc
        return error_response(request, exc)

    async def handle_request_validation(request: Request, exc: Exception) -> Response:
        if not isinstance(exc, RequestValidationError):  # pragma: no cover
            raise exc
        violations = [
            {
                "field": ".".join(str(part) for part in error.get("loc", ())),
                "message": str(error.get("msg", "invalid")),
            }
            for error in exc.errors()
        ]
        return error_response(request, errors.invalid_request(violations))

    async def handle_unexpected(request: Request, exc: Exception) -> Response:
        # Never log payloads — identifiers and outcome only (privacy by default).
        logger.exception(
            "unhandled error", extra={"request_id": getattr(request.state, "request_id", None)}
        )
        return error_response(request, errors.internal_failure())

    app.add_exception_handler(errors.MIPError, handle_mip_error)
    app.add_exception_handler(RequestValidationError, handle_request_validation)
    app.add_exception_handler(Exception, handle_unexpected)

    app.include_router(memories.router, prefix="/v1", tags=["memories"])
    app.include_router(admin.router, prefix="/v1", tags=["admin"])
    return app
