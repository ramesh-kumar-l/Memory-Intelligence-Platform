from __future__ import annotations

from collections.abc import Callable, Iterator

import httpx
import pytest

from mip_sdk.client import MIPClient

Handler = Callable[[httpx.Request], httpx.Response]
MakeClient = Callable[[Handler], MIPClient]


@pytest.fixture
def make_client() -> Iterator[MakeClient]:
    created: list[MIPClient] = []

    def _make(handler: Handler) -> MIPClient:
        http_client = httpx.Client(
            transport=httpx.MockTransport(handler), base_url="http://mip.test"
        )
        client = MIPClient("http://mip.test", http_client=http_client)
        created.append(client)
        return client

    yield _make
    for client in created:
        client.close()


def envelope(data: object, *, request_id: str = "req-1") -> dict[str, object]:
    return {
        "data": data,
        "request_id": request_id,
        "schema_version": "1.0",
        "processing_time_ms": 1.23,
    }


def error_envelope(
    *,
    code: str = "MEM-2001",
    category: str = "Lifecycle",
    message: str = "Illegal lifecycle transition",
    details: dict[str, object] | None = None,
    recoverable: bool = False,
    request_id: str = "req-err",
) -> dict[str, object]:
    return {
        "error": {
            "code": code,
            "category": category,
            "message": message,
            "details": details or {},
            "recoverable": recoverable,
            "documentation_url": f"https://example.invalid/errors#{code}",
        },
        "request_id": request_id,
    }
