"""SQLite connection, schema, and transaction management (WAL mode).

A single connection guarded by an RLock serializes all access — correct and
sufficient for the local-first Phase 1 deployment (SQLite is single-writer
anyway); reads observe consistent snapshots (INV-CONCUR-002).
"""

from __future__ import annotations

import sqlite3
import threading
from collections.abc import Iterator
from contextlib import AbstractContextManager, contextmanager
from pathlib import Path

import sqlite_vec

from mip.core import errors
from mip.storage.interfaces import TransactionManagerABC

_SCHEMA = """
CREATE TABLE IF NOT EXISTS events (
    sequence INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id TEXT NOT NULL UNIQUE,
    memory_id TEXT NOT NULL,
    event_type TEXT NOT NULL,
    payload TEXT NOT NULL,
    actor TEXT NOT NULL,
    trace_id TEXT NOT NULL,
    created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_events_memory ON events(memory_id, sequence);

CREATE TABLE IF NOT EXISTS memories (
    memory_id TEXT PRIMARY KEY,
    namespace TEXT NOT NULL,
    owner_id TEXT NOT NULL,
    object_type TEXT NOT NULL,
    title TEXT NOT NULL,
    state TEXT NOT NULL,
    current_version INTEGER NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT,
    archived_at TEXT,
    deleted_at TEXT
);
CREATE INDEX IF NOT EXISTS idx_memories_namespace_state ON memories(namespace, state);

CREATE TABLE IF NOT EXISTS memory_versions (
    memory_id TEXT NOT NULL,
    version INTEGER NOT NULL,
    previous_version INTEGER,
    object_json TEXT NOT NULL,
    created_at TEXT NOT NULL,
    PRIMARY KEY (memory_id, version)
);

CREATE TABLE IF NOT EXISTS idempotency_keys (
    idempotency_key TEXT NOT NULL,
    endpoint TEXT NOT NULL,
    request_hash TEXT NOT NULL,
    status_code INTEGER NOT NULL,
    response_json TEXT NOT NULL,
    created_at TEXT NOT NULL,
    PRIMARY KEY (idempotency_key, endpoint)
);

CREATE VIRTUAL TABLE IF NOT EXISTS memory_fts USING fts5(
    memory_id UNINDEXED,
    namespace UNINDEXED,
    title,
    summary,
    description,
    keywords
);

CREATE TABLE IF NOT EXISTS vector_rowids (
    memory_id TEXT PRIMARY KEY,
    rowid INTEGER NOT NULL UNIQUE
);
"""

_VECTOR_TABLE_DDL = (
    "CREATE VIRTUAL TABLE IF NOT EXISTS memory_vectors USING vec0(embedding float[{dim}])"
)


class Database(TransactionManagerABC):
    """Owns the sqlite3 connection; adapters execute through it."""

    def __init__(self, path: Path | str, *, embedding_dimensions: int = 256) -> None:
        location = str(path)
        if location != ":memory:":
            Path(location).parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(location, check_same_thread=False)
        self._conn.isolation_level = None  # explicit BEGIN/COMMIT below
        self._lock = threading.RLock()
        self._depth = 0
        with self._lock:
            self._conn.execute("PRAGMA journal_mode=WAL")
            self._conn.enable_load_extension(True)
            sqlite_vec.load(self._conn)
            self._conn.enable_load_extension(False)
            self._conn.executescript(_SCHEMA)
            self._conn.execute(_VECTOR_TABLE_DDL.format(dim=embedding_dimensions))

    def execute(self, sql: str, params: tuple[object, ...] = ()) -> sqlite3.Cursor:
        with self._lock:
            try:
                return self._conn.execute(sql, params)
            except sqlite3.IntegrityError:
                raise  # adapters translate integrity violations contextually
            except sqlite3.Error as exc:
                raise errors.storage_failure(type(exc).__name__) from exc

    @contextmanager
    def _transaction_scope(self) -> Iterator[None]:
        with self._lock:
            if self._depth:
                # Nested scope joins the outer transaction (atomicity preserved).
                self._depth += 1
                try:
                    yield
                finally:
                    self._depth -= 1
                return
            self._depth = 1
            try:
                self._conn.execute("BEGIN IMMEDIATE")
                try:
                    yield
                except sqlite3.Error as exc:
                    self._conn.execute("ROLLBACK")
                    raise errors.storage_failure(type(exc).__name__) from exc
                except BaseException:
                    self._conn.execute("ROLLBACK")
                    raise
                else:
                    self._conn.execute("COMMIT")
            finally:
                self._depth = 0

    def transaction(self) -> AbstractContextManager[None]:
        return self._transaction_scope()

    def ping(self) -> bool:
        try:
            with self._lock:
                self._conn.execute("SELECT 1")
        except sqlite3.Error:
            return False
        return True

    def close(self) -> None:
        with self._lock:
            self._conn.close()
