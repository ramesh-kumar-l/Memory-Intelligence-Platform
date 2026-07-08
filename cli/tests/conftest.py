"""CLI tests run against the *real* FastAPI app (in-process, no network) via
`click.testing.CliRunner`, mirroring the SDK's integration-test approach —
this exercises the actual output formatting against real API responses.
"""

from __future__ import annotations

import sys
from collections.abc import Iterator
from pathlib import Path

_BACKEND_ROOT = Path(__file__).resolve().parents[2] / "backend"
if str(_BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(_BACKEND_ROOT))

import pytest  # noqa: E402
from click.testing import CliRunner  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from mip.api.app import create_app  # noqa: E402
from mip.config import MIPSettings  # noqa: E402
from mip_sdk.client import MIPClient  # noqa: E402


@pytest.fixture
def cli_client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Iterator[CliRunner]:
    settings = MIPSettings(db_path=tmp_path / "mip.db")
    app = create_app(settings)
    with TestClient(app) as test_client:
        sdk_client = MIPClient("http://testserver", http_client=test_client)
        monkeypatch.setattr("mip_cli.main.MIPClient", lambda base_url: sdk_client)
        yield CliRunner()
