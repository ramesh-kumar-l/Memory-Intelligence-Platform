"""Opaque search continuation tokens (ADR-0004): self-contained, no server session."""

from __future__ import annotations

import pytest

from mip.api.v1.pagination import decode_search_token, encode_search_token
from mip.api.v1.retrieval_common import resolve_cursor
from mip.core.errors import ValidationError


def test_round_trip_preserves_all_fields() -> None:
    token = encode_search_token(query="revenue", mode="hybrid", namespace="ns1", offset=20)
    decoded = decode_search_token(token)
    assert decoded == {"query": "revenue", "mode": "hybrid", "namespace": "ns1", "offset": 20}


def test_round_trip_with_no_namespace() -> None:
    token = encode_search_token(query="revenue", mode="keyword", namespace=None, offset=0)
    decoded = decode_search_token(token)
    assert decoded["namespace"] is None


def test_decode_malformed_token_raises_validation_error() -> None:
    with pytest.raises(ValidationError):
        decode_search_token("not-base64!!")


def test_decode_token_from_a_different_scheme_raises() -> None:
    from mip.api.v1.pagination import encode_token

    with pytest.raises(ValidationError):
        decode_search_token(encode_token("some-memory-id"))


def test_resolve_cursor_uses_token_when_present() -> None:
    token = encode_search_token(query="revenue", mode="hybrid", namespace="ns1", offset=5)
    query, mode, namespace, offset = resolve_cursor(
        query=None, mode="keyword", namespace=None, continuation_token=token
    )
    assert (query, mode, namespace, offset) == ("revenue", "hybrid", "ns1", 5)


def test_resolve_cursor_requires_query_without_token() -> None:
    with pytest.raises(ValidationError):
        resolve_cursor(query=None, mode="hybrid", namespace=None, continuation_token=None)


def test_resolve_cursor_uses_request_body_when_no_token() -> None:
    query, mode, namespace, offset = resolve_cursor(
        query="revenue", mode="hybrid", namespace="ns1", continuation_token=None
    )
    assert (query, mode, namespace, offset) == ("revenue", "hybrid", "ns1", 0)
