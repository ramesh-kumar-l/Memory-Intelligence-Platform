"""ADR-0007: `api_key` is sent as `Authorization: Bearer <key>` when set, and
omitted entirely when not — auth is opt-in, matching the server default."""

from __future__ import annotations

import httpx

from mip_sdk.client import MIPClient
from tests.conftest import envelope
from tests.factories import sample_memory_dict


def test_api_key_is_sent_as_bearer_header() -> None:
    seen_headers: dict[str, str] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen_headers.update(request.headers)
        return httpx.Response(200, json=envelope(sample_memory_dict()))

    http_client = httpx.Client(transport=httpx.MockTransport(handler), base_url="http://mip.test")
    with MIPClient("http://mip.test", api_key="secret-key", http_client=http_client) as client:
        client.memories.get("00000000-0000-0000-0000-000000000000")
    assert seen_headers["authorization"] == "Bearer secret-key"


def test_no_api_key_means_no_authorization_header() -> None:
    seen_headers: dict[str, str] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen_headers.update(request.headers)
        return httpx.Response(200, json=envelope(sample_memory_dict()))

    http_client = httpx.Client(transport=httpx.MockTransport(handler), base_url="http://mip.test")
    with MIPClient("http://mip.test", http_client=http_client) as client:
        client.memories.get("00000000-0000-0000-0000-000000000000")
    assert "authorization" not in seen_headers
