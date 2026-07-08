"""ADR-0007: `--api-key` / `MIP_API_KEY` is forwarded to `MIPClient`. Auth is
opt-in — this only matters when the server has `MIP_AUTH_ENABLED=true`.
"""

from __future__ import annotations

import pytest
from click.testing import CliRunner

from mip_cli.main import cli


def test_api_key_option_is_forwarded_to_client(monkeypatch: pytest.MonkeyPatch) -> None:
    seen: dict[str, object] = {}

    class _FakeClient:
        def __init__(self, base_url: str, api_key: str | None = None) -> None:
            seen["base_url"] = base_url
            seen["api_key"] = api_key

        def close(self) -> None:
            pass

    monkeypatch.setattr("mip_cli.main.MIPClient", _FakeClient)
    result = CliRunner().invoke(
        cli, ["--api-key", "secret-key", "admin", "health"], catch_exceptions=True
    )
    assert seen["api_key"] == "secret-key"
    assert result.exit_code != 0  # fake client has no .admin — irrelevant to this assertion


def test_api_key_env_var_is_forwarded_to_client(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    seen: dict[str, object] = {}

    class _FakeClient:
        def __init__(self, base_url: str, api_key: str | None = None) -> None:
            seen["api_key"] = api_key

        def close(self) -> None:
            pass

    monkeypatch.setattr("mip_cli.main.MIPClient", _FakeClient)
    monkeypatch.setenv("MIP_API_KEY", "env-key")
    CliRunner().invoke(cli, ["admin", "health"], catch_exceptions=True)
    assert seen["api_key"] == "env-key"


def test_no_api_key_defaults_to_none(monkeypatch: pytest.MonkeyPatch) -> None:
    seen: dict[str, object] = {}

    class _FakeClient:
        def __init__(self, base_url: str, api_key: str | None = None) -> None:
            seen["api_key"] = api_key

        def close(self) -> None:
            pass

    monkeypatch.setattr("mip_cli.main.MIPClient", _FakeClient)
    CliRunner().invoke(cli, ["admin", "health"], catch_exceptions=True)
    assert seen["api_key"] is None
