"""Shared cursor resolution for /v1/search and /v1/context (ADR-0004): a
continuation token is self-contained, so it fully overrides the request body.
"""

from __future__ import annotations

from mip.api.v1.pagination import decode_search_token
from mip.core import errors


def resolve_cursor(
    *, query: str | None, mode: str, namespace: str | None, continuation_token: str | None
) -> tuple[str, str, str | None, int]:
    if continuation_token:
        cursor = decode_search_token(continuation_token)
        namespace_raw = cursor.get("namespace")
        return (
            str(cursor["query"]),
            str(cursor["mode"]),
            None if namespace_raw is None else str(namespace_raw),
            int(cursor["offset"]),  # type: ignore[call-overload]
        )
    if not query:
        raise errors.invalid_request(
            [{"field": "query", "message": "required unless continuation_token is provided"}]
        )
    return query, mode, namespace, 0
