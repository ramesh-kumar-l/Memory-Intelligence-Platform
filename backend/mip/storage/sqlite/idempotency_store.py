"""Idempotency-Key storage: a repeated key returns the original stored response."""

from __future__ import annotations

from datetime import datetime

from mip.storage.interfaces import IdempotencyRecord, IdempotencyStoreABC
from mip.storage.sqlite.database import Database


class SqliteIdempotencyStore(IdempotencyStoreABC):
    def __init__(self, db: Database) -> None:
        self._db = db

    def lookup(self, key: str, endpoint: str) -> IdempotencyRecord | None:
        row = self._db.execute(
            "SELECT request_hash, status_code, response_json FROM idempotency_keys "
            "WHERE idempotency_key = ? AND endpoint = ?",
            (key, endpoint),
        ).fetchone()
        if row is None:
            return None
        return IdempotencyRecord(
            request_hash=str(row[0]), status_code=int(row[1]), response_json=str(row[2])
        )

    def store(
        self,
        key: str,
        endpoint: str,
        request_hash: str,
        status_code: int,
        response_json: str,
        created_at: datetime,
    ) -> None:
        self._db.execute(
            "INSERT OR IGNORE INTO idempotency_keys "
            "(idempotency_key, endpoint, request_hash, status_code, response_json, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (key, endpoint, request_hash, status_code, response_json, created_at.isoformat()),
        )
