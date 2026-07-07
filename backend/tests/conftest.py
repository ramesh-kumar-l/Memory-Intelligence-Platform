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
from mip.engines.memory_manager.engine import MemoryManager
from mip.engines.memory_manager.locks import LockRegistry
from mip.engines.validation.engine import ValidationEngine
from mip.storage.sqlite.database import Database
from mip.storage.sqlite.event_store import SqliteEventStore
from mip.storage.sqlite.idempotency_store import SqliteIdempotencyStore
from mip.storage.sqlite.memory_repository import SqliteMemoryRepository


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


@pytest.fixture
def db(tmp_path: Path) -> Iterator[Database]:
    database = Database(tmp_path / "test.db")
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
def manager(
    db: Database,
    event_store: SqliteEventStore,
    repo: SqliteMemoryRepository,
    locks: LockRegistry,
    validation: ValidationEngine,
    clock: TickingClock,
) -> MemoryManager:
    return MemoryManager(
        event_store=event_store,
        repository=repo,
        transactions=db,
        locks=locks,
        validation=validation,
        clock=clock,
        lock_timeout=0.2,  # keep INV-CONCUR-004 tests fast
    )


@pytest.fixture
def app(tmp_path: Path) -> FastAPI:
    return create_app(MIPSettings(db_path=tmp_path / "api.db"))


@pytest.fixture
def client(app: FastAPI) -> Iterator[TestClient]:
    with TestClient(app) as test_client:
        yield test_client
