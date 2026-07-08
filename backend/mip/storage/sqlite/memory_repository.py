"""SQLite projection repository: current records + immutable version snapshots."""

from __future__ import annotations

import sqlite3
from datetime import datetime
from typing import Any

from mip.core import errors
from mip.core.model import MemoryObject
from mip.core.states import MemoryState
from mip.storage.interfaces import MemoryRecord, MemoryRepositoryABC, VersionInfo
from mip.storage.sqlite.database import Database

_RECORD_COLUMNS = (
    "memory_id, namespace, owner_id, object_type, title, state, current_version, "
    "created_at, updated_at, archived_at, deleted_at, consolidation_count"
)


class SqliteMemoryRepository(MemoryRepositoryABC):
    def __init__(self, db: Database) -> None:
        self._db = db

    def create(self, memory: MemoryObject) -> None:
        lifecycle = memory.lifecycle
        try:
            self._db.execute(
                f"INSERT INTO memories ({_RECORD_COLUMNS}) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, NULL, NULL, NULL, 0)",
                (
                    memory.memory_id,
                    memory.identity.namespace,
                    memory.identity.owner_id,
                    memory.header.object_type.value,
                    memory.content.title,
                    lifecycle.state.value,
                    lifecycle.version,
                    lifecycle.created_at.isoformat(),
                ),
            )
        except sqlite3.IntegrityError as exc:
            raise errors.duplicate_memory_id(memory.memory_id) from exc
        self._insert_version(memory, previous_version=None, created_at=lifecycle.created_at)

    def get_record(self, memory_id: str) -> MemoryRecord | None:
        row = self._db.execute(
            f"SELECT {_RECORD_COLUMNS} FROM memories WHERE memory_id = ?", (memory_id,)
        ).fetchone()
        return _to_record(row) if row else None

    def get_object(self, memory_id: str, version: int | None = None) -> MemoryObject | None:
        record = self.get_record(memory_id)
        if record is None:
            return None
        wanted = record.current_version if version is None else version
        row = self._db.execute(
            "SELECT object_json FROM memory_versions WHERE memory_id = ? AND version = ?",
            (memory_id, wanted),
        ).fetchone()
        if row is None:
            return None
        memory = MemoryObject.from_storage_json(row[0])
        if version is not None and version != record.current_version:
            return memory  # historical snapshot, immutable as stored (INV-VER-002)
        return memory.with_lifecycle(
            state=record.state,
            updated_at=record.updated_at,
            archived_at=record.archived_at,
            deleted_at=record.deleted_at,
            consolidation_count=record.consolidation_count,
        )

    def publish_version(
        self, memory: MemoryObject, previous_version: int, published_at: datetime
    ) -> None:
        self._insert_version(memory, previous_version=previous_version, created_at=published_at)
        self._db.execute(
            "UPDATE memories SET current_version = ?, state = ?, updated_at = ?, title = ? "
            "WHERE memory_id = ?",
            (
                memory.version,
                MemoryState.ACTIVE.value,
                published_at.isoformat(),
                memory.content.title,
                memory.memory_id,
            ),
        )

    def set_state(self, memory_id: str, state: MemoryState, changed_at: datetime) -> None:
        timestamp = changed_at.isoformat()
        if state is MemoryState.ARCHIVED:
            self._db.execute(
                "UPDATE memories SET state = ?, archived_at = ? WHERE memory_id = ?",
                (state.value, timestamp, memory_id),
            )
        elif state is MemoryState.DELETED:
            self._db.execute(
                "UPDATE memories SET state = ?, deleted_at = ? WHERE memory_id = ?",
                (state.value, timestamp, memory_id),
            )
        elif state is MemoryState.ACTIVE:
            # Entering Active always clears any archive marker (restore path).
            self._db.execute(
                "UPDATE memories SET state = ?, archived_at = NULL WHERE memory_id = ?",
                (state.value, memory_id),
            )
        else:
            self._db.execute(
                "UPDATE memories SET state = ? WHERE memory_id = ?", (state.value, memory_id)
            )

    def record_consolidation(self, memory_id: str, consolidated_at: datetime) -> None:
        self._db.execute(
            "UPDATE memories SET consolidation_count = consolidation_count + 1, updated_at = ? "
            "WHERE memory_id = ?",
            (consolidated_at.isoformat(), memory_id),
        )

    def list_records(
        self,
        *,
        namespace: str | None,
        state: MemoryState | None,
        limit: int,
        after_memory_id: str | None,
    ) -> tuple[list[MemoryRecord], bool]:
        clauses: list[str] = []
        params: list[object] = []
        if namespace is not None:
            clauses.append("namespace = ?")
            params.append(namespace)
        if state is not None:
            clauses.append("state = ?")
            params.append(state.value)
        else:
            clauses.append("state != ?")  # tombstones excluded unless asked for (ADR-0003)
            params.append(MemoryState.DELETED.value)
        if after_memory_id is not None:
            clauses.append("memory_id > ?")
            params.append(after_memory_id)
        where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        params.append(limit + 1)
        rows = self._db.execute(
            f"SELECT {_RECORD_COLUMNS} FROM memories {where} ORDER BY memory_id LIMIT ?",
            tuple(params),
        ).fetchall()
        records = [_to_record(row) for row in rows[:limit]]
        return records, len(rows) > limit

    def list_versions(self, memory_id: str) -> list[VersionInfo]:
        rows = self._db.execute(
            "SELECT version, previous_version, created_at FROM memory_versions "
            "WHERE memory_id = ? ORDER BY version",
            (memory_id,),
        ).fetchall()
        return [
            VersionInfo(
                version=int(row[0]),
                previous_version=None if row[1] is None else int(row[1]),
                created_at=datetime.fromisoformat(row[2]),
            )
            for row in rows
        ]

    def clear_all(self) -> None:
        self._db.execute("DELETE FROM memory_versions")
        self._db.execute("DELETE FROM memories")

    def dump_state(self) -> dict[str, Any]:
        memories = self._db.execute(
            f"SELECT {_RECORD_COLUMNS} FROM memories ORDER BY memory_id"
        ).fetchall()
        versions = self._db.execute(
            "SELECT memory_id, version, previous_version, object_json, created_at "
            "FROM memory_versions ORDER BY memory_id, version"
        ).fetchall()
        return {"memories": memories, "versions": versions}

    def _insert_version(
        self, memory: MemoryObject, previous_version: int | None, created_at: datetime
    ) -> None:
        try:
            self._db.execute(
                "INSERT INTO memory_versions "
                "(memory_id, version, previous_version, object_json, created_at) "
                "VALUES (?, ?, ?, ?, ?)",
                (
                    memory.memory_id,
                    memory.version,
                    previous_version,
                    memory.to_storage_json(),
                    created_at.isoformat(),
                ),
            )
        except sqlite3.IntegrityError as exc:
            # Version rows are immutable — overwriting one is a corruption attempt.
            raise errors.storage_failure(
                f"version {memory.version} already exists for {memory.memory_id}"
            ) from exc


def _to_record(row: tuple[Any, ...]) -> MemoryRecord:
    return MemoryRecord(
        memory_id=str(row[0]),
        namespace=str(row[1]),
        owner_id=str(row[2]),
        object_type=str(row[3]),
        title=str(row[4]),
        state=MemoryState(row[5]),
        current_version=int(row[6]),
        created_at=datetime.fromisoformat(row[7]),
        updated_at=None if row[8] is None else datetime.fromisoformat(row[8]),
        archived_at=None if row[9] is None else datetime.fromisoformat(row[9]),
        deleted_at=None if row[10] is None else datetime.fromisoformat(row[10]),
        consolidation_count=int(row[11]),
    )
