"""Opaque continuation tokens — offset pagination is prohibited by the contract."""

from __future__ import annotations

import base64
import binascii

from mip.core import errors

_PREFIX = "mid:"


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
