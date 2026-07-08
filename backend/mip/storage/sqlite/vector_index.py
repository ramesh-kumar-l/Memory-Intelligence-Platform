"""sqlite-vec-backed semantic vector index (ADR-0004). A regenerable
projection: rows are derived from Memory Object content, never authoritative.

vec0 virtual tables key rows by an integer rowid; `vector_rowids` maps the
UUID `memory_id` to a stable allocated rowid.
"""

from __future__ import annotations

import sqlite_vec

from mip.storage.interfaces import VectorHit, VectorIndexABC
from mip.storage.sqlite.database import Database


class SqliteVecVectorIndex(VectorIndexABC):
    def __init__(self, db: Database) -> None:
        self._db = db

    def upsert(self, *, memory_id: str, embedding: tuple[float, ...]) -> None:
        rowid = self._rowid_for(memory_id)
        blob = sqlite_vec.serialize_float32(list(embedding))
        self._db.execute("DELETE FROM memory_vectors WHERE rowid = ?", (rowid,))
        self._db.execute(
            "INSERT INTO memory_vectors (rowid, embedding) VALUES (?, ?)", (rowid, blob)
        )

    def search(self, embedding: tuple[float, ...], *, limit: int) -> list[VectorHit]:
        blob = sqlite_vec.serialize_float32(list(embedding))
        rows = self._db.execute(
            "SELECT rowid, distance FROM memory_vectors WHERE embedding MATCH ? AND k = ? "
            "ORDER BY distance",
            (blob, limit),
        ).fetchall()
        if not rows:
            return []
        rowids = [int(row[0]) for row in rows]
        placeholders = ",".join("?" for _ in rowids)
        id_rows = self._db.execute(
            f"SELECT memory_id, rowid FROM vector_rowids WHERE rowid IN ({placeholders})",
            tuple(rowids),
        ).fetchall()
        memory_id_by_rowid = {int(row[1]): str(row[0]) for row in id_rows}
        return [
            VectorHit(memory_id=memory_id_by_rowid[int(row[0])], distance=float(row[1]))
            for row in rows
            if int(row[0]) in memory_id_by_rowid
        ]

    def clear_all(self) -> None:
        self._db.execute("DELETE FROM memory_vectors")
        self._db.execute("DELETE FROM vector_rowids")

    def _rowid_for(self, memory_id: str) -> int:
        row = self._db.execute(
            "SELECT rowid FROM vector_rowids WHERE memory_id = ?", (memory_id,)
        ).fetchone()
        if row is not None:
            return int(row[0])
        next_row = self._db.execute(
            "SELECT COALESCE(MAX(rowid), 0) + 1 FROM vector_rowids"
        ).fetchone()
        rowid = int(next_row[0])
        self._db.execute(
            "INSERT INTO vector_rowids (memory_id, rowid) VALUES (?, ?)", (memory_id, rowid)
        )
        return rowid
