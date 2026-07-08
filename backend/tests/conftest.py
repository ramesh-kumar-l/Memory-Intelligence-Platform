"""Shared fixtures. Determinism rules: injected ticking clock, tmp database per
test, no network, no sleeps (20-testing-strategy.md).
"""

from __future__ import annotations

from collections.abc import Iterator
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from mip.api.app import create_app
from mip.config import MIPSettings
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
from mip.providers.embeddings import EmbeddingProviderABC
from mip.providers.local_embedding import LocalHashingEmbeddingProvider
from mip.storage.sqlite.database import Database
from mip.storage.sqlite.event_store import SqliteEventStore
from mip.storage.sqlite.graph_index import SqliteGraphIndex
from mip.storage.sqlite.idempotency_store import SqliteIdempotencyStore
from mip.storage.sqlite.memory_repository import SqliteMemoryRepository
from mip.storage.sqlite.search_index import Fts5SearchIndex
from mip.storage.sqlite.vector_index import SqliteVecVectorIndex


class TickingClock:
    """Deterministic clock: every call advances exactly one second."""

    def __init__(self, start: datetime | None = None) -> None:
        self._now = start or datetime(2026, 1, 1, tzinfo=UTC)

    def now(self) -> datetime:
        self._now += timedelta(seconds=1)
        return self._now


@pytest.fixture
def clock() -> TickingClock:
    return TickingClock()


#: Kept small across fixtures for fast tests; must match the `embeddings` fixture.
TEST_EMBEDDING_DIMENSIONS = 32


@pytest.fixture
def db(tmp_path: Path) -> Iterator[Database]:
    database = Database(tmp_path / "test.db", embedding_dimensions=TEST_EMBEDDING_DIMENSIONS)
    yield database
    database.close()


@pytest.fixture
def event_store(db: Database) -> SqliteEventStore:
    return SqliteEventStore(db)


@pytest.fixture
def repo(db: Database) -> SqliteMemoryRepository:
    return SqliteMemoryRepository(db)


@pytest.fixture
def idempotency(db: Database) -> SqliteIdempotencyStore:
    return SqliteIdempotencyStore(db)


@pytest.fixture
def locks() -> LockRegistry:
    return LockRegistry()


@pytest.fixture
def validation(clock: TickingClock) -> ValidationEngine:
    return ValidationEngine(schema_version="1.0", encoding_version="1.0", clock=clock)


@pytest.fixture
def embeddings() -> EmbeddingProviderABC:
    return LocalHashingEmbeddingProvider(dimensions=TEST_EMBEDDING_DIMENSIONS)


@pytest.fixture
def search_index(db: Database) -> Fts5SearchIndex:
    return Fts5SearchIndex(db)


@pytest.fixture
def vector_index(db: Database) -> SqliteVecVectorIndex:
    return SqliteVecVectorIndex(db)


@pytest.fixture
def graph_index(db: Database) -> SqliteGraphIndex:
    return SqliteGraphIndex(db)


@pytest.fixture
def semantic() -> SemanticEngine:
    return SemanticEngine()


@pytest.fixture
def trust() -> TrustEngine:
    return TrustEngine(freshness_half_life_days=30.0)


@pytest.fixture
def graph(graph_index: SqliteGraphIndex, repo: SqliteMemoryRepository) -> GraphEngine:
    return GraphEngine(graph_index=graph_index, repository=repo)


@pytest.fixture
def retrieval(
    search_index: Fts5SearchIndex,
    vector_index: SqliteVecVectorIndex,
    embeddings: EmbeddingProviderABC,
    repo: SqliteMemoryRepository,
    graph: GraphEngine,
) -> RetrievalEngine:
    return RetrievalEngine(
        search_index=search_index,
        vector_index=vector_index,
        embeddings=embeddings,
        repository=repo,
        graph=graph,
        hybrid_keyword_weight=0.5,
    )


@pytest.fixture
def context_engine(retrieval: RetrievalEngine, repo: SqliteMemoryRepository) -> ContextEngine:
    return ContextEngine(retrieval=retrieval, repository=repo)


@pytest.fixture
def manager(
    db: Database,
    event_store: SqliteEventStore,
    repo: SqliteMemoryRepository,
    locks: LockRegistry,
    validation: ValidationEngine,
    semantic: SemanticEngine,
    trust: TrustEngine,
    retrieval: RetrievalEngine,
    clock: TickingClock,
) -> MemoryManager:
    return MemoryManager(
        event_store=event_store,
        repository=repo,
        transactions=db,
        locks=locks,
        validation=validation,
        semantic=semantic,
        trust=trust,
        indexer=retrieval,
        clock=clock,
        lock_timeout=0.2,  # keep INV-CONCUR-004 tests fast
    )


@pytest.fixture
def consolidate_engine(
    manager: MemoryManager,
    event_store: SqliteEventStore,
    repo: SqliteMemoryRepository,
    db: Database,
    clock: TickingClock,
) -> ConsolidateEngine:
    return ConsolidateEngine(
        manager=manager, event_store=event_store, repository=repo, transactions=db, clock=clock
    )


@pytest.fixture
def learn_engine(manager: MemoryManager, trust: TrustEngine) -> LearnEngine:
    return LearnEngine(manager=manager, trust=trust)


@pytest.fixture
def export_engine(manager: MemoryManager, clock: TickingClock) -> ExportEngine:
    return ExportEngine(manager=manager, clock=clock, schema_version="1.0")


@pytest.fixture
def import_engine(
    event_store: SqliteEventStore, repo: SqliteMemoryRepository, db: Database, clock: TickingClock
) -> ImportEngine:
    return ImportEngine(event_store=event_store, repository=repo, transactions=db, clock=clock)


@pytest.fixture
def app(tmp_path: Path) -> FastAPI:
    return create_app(MIPSettings(db_path=tmp_path / "api.db"))


@pytest.fixture
def client(app: FastAPI) -> Iterator[TestClient]:
    with TestClient(app) as test_client:
        yield test_client
