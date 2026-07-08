"""FTS5-backed keyword index (ADR-0004). A regenerable projection: rows are
derived from Memory Object content, never authoritative on their own.
"""

from __future__ import annotations

import re

from mip.storage.interfaces import SearchHit, SearchIndexABC
from mip.storage.sqlite.database import Database

_TOKEN_RE = re.compile(r"[A-Za-z0-9]+")


def _match_expression(query: str) -> str | None:
    """Turn free-text into a safe OR-of-quoted-tokens FTS5 MATCH expression,
    so user input can never break FTS5 query syntax (quotes, ^, NOT, ...).
    """
    tokens = _TOKEN_RE.findall(query)
    if not tokens:
        return None
    return " OR ".join(f'"{token}"' for token in tokens)


class Fts5SearchIndex(SearchIndexABC):
    def __init__(self, db: Database) -> None:
        self._db = db

    def index(
        self,
        *,
        memory_id: str,
        namespace: str,
        title: str,
        summary: str,
        description: str,
        keywords: str,
    ) -> None:
        self._db.execute("DELETE FROM memory_fts WHERE memory_id = ?", (memory_id,))
        self._db.execute(
            "INSERT INTO memory_fts (memory_id, namespace, title, summary, description, keywords) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (memory_id, namespace, title, summary, description, keywords),
        )

    def search(self, query: str, *, namespace: str | None, limit: int) -> list[SearchHit]:
        match = _match_expression(query)
        if match is None:
            return []
        clauses = ["memory_fts MATCH ?"]
        params: list[object] = [match]
        if namespace is not None:
            clauses.append("namespace = ?")
            params.append(namespace)
        params.append(limit)
        rows = self._db.execute(
            "SELECT memory_id, bm25(memory_fts) AS rank FROM memory_fts "
            f"WHERE {' AND '.join(clauses)} ORDER BY rank LIMIT ?",
            tuple(params),
        ).fetchall()
        # bm25() is lower-is-better; negate so higher SearchHit.score is better (ADR-0004).
        return [SearchHit(memory_id=str(row[0]), score=-float(row[1])) for row in rows]

    def clear_all(self) -> None:
        self._db.execute("DELETE FROM memory_fts")
