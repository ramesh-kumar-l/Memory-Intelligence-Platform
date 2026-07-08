from __future__ import annotations

import json

from click.testing import CliRunner

from mip_cli.main import cli
from tests.test_cli_memories import _create


def test_search_finds_created_memory(cli_client: CliRunner) -> None:
    created = _create(cli_client, title="Findable via search")
    result = cli_client.invoke(
        cli,
        ["--json", "search", "Findable", "--mode", "keyword"],
        catch_exceptions=False,
    )
    assert result.exit_code == 0
    response = json.loads(result.output)
    assert any(item["memory_id"] == created["memory_id"] for item in response["items"])


def test_search_table_output(cli_client: CliRunner) -> None:
    _create(cli_client, title="Table search memory")
    result = cli_client.invoke(
        cli, ["search", "Table", "--mode", "keyword"], catch_exceptions=False
    )
    assert result.exit_code == 0
    assert "MEMORY_ID" in result.output


def test_explain_shows_confidence_and_provenance(cli_client: CliRunner) -> None:
    created = _create(cli_client)
    result = cli_client.invoke(cli, ["explain", str(created["memory_id"])], catch_exceptions=False)
    assert result.exit_code == 0
    explanation = json.loads(result.output)
    assert explanation["memory_id"] == created["memory_id"]
    assert "confidence" in explanation
    assert "provenance" in explanation


def test_context_blends_relevance_and_importance(cli_client: CliRunner) -> None:
    created = _create(cli_client, title="Context blending memory")
    result = cli_client.invoke(
        cli,
        ["--json", "context", "Context blending", "--namespace", "demo"],
        catch_exceptions=False,
    )
    assert result.exit_code == 0
    package = json.loads(result.output)
    assert any(item["memory"]["memory_id"] == created["memory_id"] for item in package["items"])


def test_search_unsupported_mode_rejected_by_cli_option(cli_client: CliRunner) -> None:
    result = cli_client.invoke(cli, ["search", "x", "--mode", "bogus"])
    assert result.exit_code != 0
    assert "Invalid value" in result.output
