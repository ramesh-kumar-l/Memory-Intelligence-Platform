"""SQLite-backed relationship-graph adjacency index (ADR-0006). A regenerable
projection: rows are derived from each Memory Object's `relationships` field,
never authoritative on their own.
"""

from __future__ import annotations

from mip.storage.interfaces import GraphEdge, GraphIndexABC
from mip.storage.sqlite.database import Database

_COLUMNS = "relationship_id, source_memory_id, target_memory_id, type, direction, confidence"


class SqliteGraphIndex(GraphIndexABC):
    def __init__(self, db: Database) -> None:
        self._db = db

    def index_relationships(self, memory_id: str, edges: tuple[GraphEdge, ...]) -> None:
        self._db.execute(
            "DELETE FROM memory_relationship_edges WHERE source_memory_id = ?", (memory_id,)
        )
        for edge in edges:
            self._db.execute(
                f"INSERT INTO memory_relationship_edges ({_COLUMNS}) VALUES (?, ?, ?, ?, ?, ?)",
                (
                    edge.relationship_id,
                    edge.source_memory_id,
                    edge.target_memory_id,
                    edge.type,
                    edge.direction,
                    edge.confidence,
                ),
            )

    def edges_touching(self, memory_id: str) -> list[GraphEdge]:
        rows = self._db.execute(
            f"SELECT {_COLUMNS} FROM memory_relationship_edges "
            "WHERE source_memory_id = ? OR target_memory_id = ?",
            (memory_id, memory_id),
        ).fetchall()
        return [
            GraphEdge(
                relationship_id=str(row[0]),
                source_memory_id=str(row[1]),
                target_memory_id=str(row[2]),
                type=str(row[3]),
                direction=str(row[4]),
                confidence=float(row[5]),
            )
            for row in rows
        ]

    def clear_all(self) -> None:
        self._db.execute("DELETE FROM memory_relationship_edges")
