"""Rate limiting contract tests (ADR-0007). Disabled by default — see
`test_disabled_by_default_allows_bursts` and `22-deployment.md`.
"""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from mip.api.app import create_app
from mip.config import MIPSettings


@pytest.fixture
def limited_client(tmp_path: Path) -> Iterator[TestClient]:
    settings = MIPSettings(
        db_path=tmp_path / "ratelimit.db",
        rate_limit_enabled=True,
        rate_limit_requests_per_minute=2,
    )
    with TestClient(create_app(settings)) as test_client:
        yield test_client


def test_requests_within_limit_succeed(limited_client: TestClient) -> None:
    assert limited_client.get("/v1/health").status_code == 200
    assert limited_client.get("/v1/health").status_code == 200


def test_exceeding_limit_returns_429_with_retry_after(limited_client: TestClient) -> None:
    limited_client.get("/v1/health")
    limited_client.get("/v1/health")
    response = limited_client.get("/v1/health")
    assert response.status_code == 429
    assert response.json()["error"]["code"] == "MEM-8005"
    assert "Retry-After" in response.headers


def test_disabled_by_default_allows_bursts(client: TestClient) -> None:
    for _ in range(20):
        assert client.get("/v1/health").status_code == 200
