"""Append-only SQLite event store. Events are never updated or deleted."""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime
from typing import Any
from uuid import UUID

from mip.core import errors
from mip.events.types import EventType, MemoryEvent
from mip.storage.interfaces import EventStoreABC
from mip.storage.sqlite.database import Database

_COLUMNS = "sequence, event_id, memory_id, event_type, payload, actor, trace_id, created_at"


class SqliteEventStore(EventStoreABC):
    def __init__(self, db: Database) -> None:
        self._db = db

    def append(self, event: MemoryEvent) -> MemoryEvent:
        try:
            cursor = self._db.execute(
                "INSERT INTO events "
                "(event_id, memory_id, event_type, payload, actor, trace_id, created_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)",
                (
                    str(event.event_id),
                    event.memory_id,
                    event.event_type.value,
                    json.dumps(event.payload, sort_keys=True),
                    event.actor,
                    event.trace_id,
                    event.created_at.isoformat(),
                ),
            )
        except sqlite3.IntegrityError as exc:
            raise errors.storage_failure("duplicate event_id") from exc
        if cursor.lastrowid is None:  # pragma: no cover - sqlite always sets it on INSERT
            raise errors.storage_failure("no sequence assigned")
        return event.model_copy(update={"sequence": int(cursor.lastrowid)})

    def events_for(self, memory_id: str) -> list[MemoryEvent]:
        rows = self._db.execute(
            f"SELECT {_COLUMNS} FROM events WHERE memory_id = ? ORDER BY sequence",
            (memory_id,),
        ).fetchall()
        return [_to_event(row) for row in rows]

    def all_events(self) -> list[MemoryEvent]:
        rows = self._db.execute(f"SELECT {_COLUMNS} FROM events ORDER BY sequence").fetchall()
        return [_to_event(row) for row in rows]

    def count(self) -> int:
        row = self._db.execute("SELECT COUNT(*) FROM events").fetchone()
        return int(row[0])


def _to_event(row: tuple[Any, ...]) -> MemoryEvent:
    payload: dict[str, Any] = json.loads(row[4])
    return MemoryEvent(
        sequence=int(row[0]),
        event_id=UUID(row[1]),
        memory_id=str(row[2]),
        event_type=EventType(row[3]),
        payload=payload,
        actor=str(row[5]),
        trace_id=str(row[6]),
        created_at=datetime.fromisoformat(row[7]),
    )
