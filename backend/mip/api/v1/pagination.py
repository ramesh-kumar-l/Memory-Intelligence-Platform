"""Opaque continuation tokens — offset pagination is prohibited by the contract."""

from __future__ import annotations

import base64
import binascii
import json

from mip.core import errors

_PREFIX = "mid:"
_SEARCH_PREFIX = "srch:"


def encode_token(last_memory_id: str) -> str:
    return base64.urlsafe_b64encode(f"{_PREFIX}{last_memory_id}".encode()).decode()


def decode_token(token: str) -> str:
    try:
        decoded = base64.urlsafe_b64decode(token.encode()).decode()
    except (binascii.Error, UnicodeDecodeError) as exc:
        raise errors.invalid_request(
            [{"field": "continuation_token", "message": "malformed token"}]
        ) from exc
    if not decoded.startswith(_PREFIX):
        raise errors.invalid_request(
            [{"field": "continuation_token", "message": "unrecognized token"}]
        )
    return decoded[len(_PREFIX) :]


def encode_search_token(*, query: str, mode: str, namespace: str | None, offset: int) -> str:
    """Self-contained search cursor: the server holds no session state, so the
    token itself carries everything needed to resume (ADR-0004).
    """
    payload = json.dumps({"query": query, "mode": mode, "namespace": namespace, "offset": offset})
    return base64.urlsafe_b64encode(f"{_SEARCH_PREFIX}{payload}".encode()).decode()


def decode_search_token(token: str) -> dict[str, object]:
    try:
        decoded = base64.urlsafe_b64decode(token.encode()).decode()
    except (binascii.Error, UnicodeDecodeError) as exc:
        raise errors.invalid_request(
            [{"field": "continuation_token", "message": "malformed token"}]
        ) from exc
    if not decoded.startswith(_SEARCH_PREFIX):
        raise errors.invalid_request(
            [{"field": "continuation_token", "message": "unrecognized token"}]
        )
    try:
        payload = json.loads(decoded[len(_SEARCH_PREFIX) :])
    except json.JSONDecodeError as exc:
        raise errors.invalid_request(
            [{"field": "continuation_token", "message": "malformed token payload"}]
        ) from exc
    if not isinstance(payload, dict):
        raise errors.invalid_request(
            [{"field": "continuation_token", "message": "malformed token payload"}]
        )
    return payload
