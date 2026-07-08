from __future__ import annotations

import httpx
import pytest

from mip_sdk.errors import (
    ConcurrencyError,
    IdentityError,
    LifecycleError,
    MIPAPIError,
    MIPConnectionError,
    SecurityError,
    StorageError,
    SyncError,
    TrustError,
    ValidationError,
)
from tests.conftest import MakeClient, error_envelope

CATEGORY_CASES = [
    ("Validation", ValidationError),
    ("Lifecycle", LifecycleError),
    ("Identity", IdentityError),
    ("Concurrency", ConcurrencyError),
    ("Trust", TrustError),
    ("Storage", StorageError),
    ("Sync", SyncError),
    ("Security", SecurityError),
]


@pytest.mark.parametrize("category,expected_cls", CATEGORY_CASES)
def test_error_category_maps_to_typed_exception(
    make_client: MakeClient, category: str, expected_cls: type[MIPAPIError]
) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(409, json=error_envelope(category=category, code="MEM-9999"))

    client = make_client(handler)
    with pytest.raises(expected_cls) as excinfo:
        client.admin.health()
    assert excinfo.value.code == "MEM-9999"
    assert excinfo.value.category == category
    assert excinfo.value.http_status == 409


def test_unknown_category_falls_back_to_base_error(make_client: MakeClient) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(500, json=error_envelope(category="SomethingNew", code="MEM-0001"))

    client = make_client(handler)
    with pytest.raises(MIPAPIError) as excinfo:
        client.admin.health()
    assert type(excinfo.value) is MIPAPIError
    assert excinfo.value.code == "MEM-0001"


def test_recoverable_and_details_are_preserved(make_client: MakeClient) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            409,
            json=error_envelope(
                category="Concurrency",
                code="MEM-4001",
                recoverable=True,
                details={"expected": 1, "actual": 2},
            ),
        )

    client = make_client(handler)
    with pytest.raises(ConcurrencyError) as excinfo:
        client.admin.health()
    assert excinfo.value.recoverable is True
    assert excinfo.value.details == {"expected": 1, "actual": 2}


def test_connection_failure_raises_typed_error() -> None:
    from mip_sdk.client import MIPClient

    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("connection refused", request=request)

    http_client = httpx.Client(transport=httpx.MockTransport(handler), base_url="http://mip.test")
    client = MIPClient("http://mip.test", http_client=http_client)
    with pytest.raises(MIPConnectionError):
        client.admin.health()
    client.close()
