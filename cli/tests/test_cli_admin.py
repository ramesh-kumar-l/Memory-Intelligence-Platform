from __future__ import annotations

import json

from click.testing import CliRunner

from mip_cli.main import cli


def test_health(cli_client: CliRunner) -> None:
    result = cli_client.invoke(cli, ["admin", "health"], catch_exceptions=False)
    assert result.exit_code == 0
    assert json.loads(result.output)["status"] == "ok"


def test_version(cli_client: CliRunner) -> None:
    result = cli_client.invoke(cli, ["admin", "version"], catch_exceptions=False)
    assert result.exit_code == 0
    assert "service_version" in json.loads(result.output)


def test_rebuild(cli_client: CliRunner) -> None:
    result = cli_client.invoke(cli, ["admin", "rebuild"], catch_exceptions=False)
    assert result.exit_code == 0
    assert "indexed_memories" in json.loads(result.output)


def test_help_lists_all_subcommands(cli_client: CliRunner) -> None:
    result = cli_client.invoke(cli, ["--help"], catch_exceptions=False)
    assert result.exit_code == 0
    for name in ("memories", "admin", "search", "explain", "context"):
        assert name in result.output
