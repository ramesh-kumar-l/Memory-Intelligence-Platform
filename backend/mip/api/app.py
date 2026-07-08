"""Application factory: wires adapters → engines → routes (dependency rule:
engines receive interfaces, concrete SQLite adapters are chosen only here).
"""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware

import mip
from mip.api.middleware.auth import require_principal
from mip.api.middleware.rate_limit import RateLimitMiddleware
from mip.api.middleware.request_context import RequestContextMiddleware
from mip.api.responses import error_response
from mip.api.v1 import admin, consolidate, context, explain, learn, memories, portability, search
from mip.config import MIPSettings
from mip.core import errors
from mip.core.clock import SystemClock
from mip.engines.context.engine import ContextEngine
from mip.engines.knowledge.consolidate import ConsolidateEngine
from mip.engines.knowledge.graph import GraphEngine
from mip.engines.learning.engine import LearnEngine
from mip.engines.memory_manager.engine import MemoryManager
from mip.engines.memory_manager.locks import LockRegistry
from mip.engines.portability.export_engine import ExportEngine
from mip.engines.portability.import_engine import ImportEngine
from mip.engines.retrieval.engine import RetrievalEngine
from mip.engines.semantic.engine import SemanticEngine
from mip.engines.trust.scoring import TrustEngine
from mip.engines.validation.engine import ValidationEngine
from mip.providers.local_embedding import LocalHashingEmbeddingProvider
from mip.storage.sqlite.database import Database
from mip.storage.sqlite.event_store import SqliteEventStore
from mip.storage.sqlite.graph_index import SqliteGraphIndex
from mip.storage.sqlite.idempotency_store import SqliteIdempotencyStore
from mip.storage.sqlite.memory_repository import SqliteMemoryRepository
from mip.storage.sqlite.search_index import Fts5SearchIndex
from mip.storage.sqlite.vector_index import SqliteVecVectorIndex

logger = logging.getLogger(__name__)


def create_app(settings: MIPSettings | None = None) -> FastAPI:
    active_settings = settings or MIPSettings()
    database = Database(
        active_settings.db_path, embedding_dimensions=active_settings.embedding_dimensions
    )
    clock = SystemClock()
    event_store = SqliteEventStore(database)
    repository = SqliteMemoryRepository(database)
    validation = ValidationEngine(
        schema_version=active_settings.schema_version,
        encoding_version=active_settings.encoding_version,
        clock=clock,
    )
    embeddings = LocalHashingEmbeddingProvider(dimensions=active_settings.embedding_dimensions)
    graph = GraphEngine(graph_index=SqliteGraphIndex(database), repository=repository)
    retrieval = RetrievalEngine(
        search_index=Fts5SearchIndex(database),
        vector_index=SqliteVecVectorIndex(database),
        embeddings=embeddings,
        repository=repository,
        graph=graph,
        hybrid_keyword_weight=active_settings.hybrid_keyword_weight,
    )
    trust = TrustEngine(freshness_half_life_days=active_settings.trust_freshness_half_life_days)
    manager = MemoryManager(
        event_store=event_store,
        repository=repository,
        transactions=database,
        locks=LockRegistry(),
        validation=validation,
        semantic=SemanticEngine(),
        trust=trust,
        indexer=retrieval,
        clock=clock,
        lock_timeout=active_settings.lock_timeout_seconds,
    )
    context_engine = ContextEngine(retrieval=retrieval, repository=repository)
    consolidate_engine = ConsolidateEngine(
        manager=manager,
        event_store=event_store,
        repository=repository,
        transactions=database,
        clock=clock,
    )
    learn_engine = LearnEngine(manager=manager, trust=trust)
    export_engine = ExportEngine(
        manager=manager, clock=clock, schema_version=active_settings.schema_version
    )
    import_engine = ImportEngine(
        event_store=event_store, repository=repository, transactions=database, clock=clock
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
    app.state.retrieval_engine = retrieval
    app.state.context_engine = context_engine
    app.state.trust_engine = trust
    app.state.graph_engine = graph
    app.state.consolidate_engine = consolidate_engine
    app.state.learn_engine = learn_engine
    app.state.export_engine = export_engine
    app.state.import_engine = import_engine

    app.add_middleware(
        RateLimitMiddleware,
        enabled=active_settings.rate_limit_enabled,
        requests_per_minute=active_settings.rate_limit_requests_per_minute,
    )
    app.add_middleware(RequestContextMiddleware, supported_versions=active_settings.api_versions)
    if active_settings.cors_allowed_origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=list(active_settings.cors_allowed_origins),
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

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

    auth_dep = [Depends(require_principal)]
    # /v1/health and /v1/version (in admin.router) stay public; rebuild-projections
    # is gated individually since it shares a router with them (ADR-0007).
    app.include_router(memories.router, prefix="/v1", tags=["memories"], dependencies=auth_dep)
    app.include_router(admin.router, prefix="/v1", tags=["admin"])
    app.include_router(search.router, prefix="/v1", tags=["retrieval"], dependencies=auth_dep)
    app.include_router(explain.router, prefix="/v1", tags=["retrieval"], dependencies=auth_dep)
    app.include_router(context.router, prefix="/v1", tags=["retrieval"], dependencies=auth_dep)
    app.include_router(
        consolidate.router, prefix="/v1", tags=["intelligence"], dependencies=auth_dep
    )
    app.include_router(learn.router, prefix="/v1", tags=["intelligence"], dependencies=auth_dep)
    app.include_router(
        portability.router, prefix="/v1", tags=["intelligence"], dependencies=auth_dep
    )
    return app
