"""`mip consolidate|learn` CLI tests (Phase 4 tasks 2/3, ADR-0006)."""

from __future__ import annotations

import json

from click.testing import CliRunner

from mip_cli.main import cli
from tests.test_cli_memories import _create


def test_consolidate_merges_duplicate(cli_client: CliRunner) -> None:
    primary = _create(cli_client, title="primary")
    duplicate = _create(cli_client, title="duplicate")
    result = cli_client.invoke(
        cli,
        [
            "--json",
            "consolidate",
            "--primary",
            str(primary["memory_id"]),
            "--duplicate",
            str(duplicate["memory_id"]),
        ],
        catch_exceptions=False,
    )
    assert result.exit_code == 0, result.output
    merged = json.loads(result.output)
    assert merged["lifecycle"]["consolidation_count"] == 1

    relationships = cli_client.invoke(
        cli,
        ["--json", "memories", "relationships", str(duplicate["memory_id"])],
        catch_exceptions=False,
    )
    assert relationships.exit_code == 0, relationships.output
    view = json.loads(relationships.output)
    assert view["relationships"][0]["type"] == "duplicate_of"


def test_learn_adds_derived_concept(cli_client: CliRunner) -> None:
    created = _create(cli_client, title="learnable")
    result = cli_client.invoke(
        cli,
        [
            "--json",
            "learn",
            str(created["memory_id"]),
            "--concept",
            "durability",
            "--reason",
            "pattern observed",
        ],
        catch_exceptions=False,
    )
    assert result.exit_code == 0, result.output
    updated = json.loads(result.output)
    assert "durability" in updated["semantics"]["concepts"]


def test_learn_matures_evidence(cli_client: CliRunner) -> None:
    created = _create(cli_client, title="evidence memory")
    result = cli_client.invoke(
        cli,
        [
            "--json",
            "learn",
            str(created["memory_id"]),
            "--evidence",
            '{"source": "doc-1"}',
            "--evidence",
            '{"source": "doc-2"}',
            "--reason",
            "corroborating documents",
        ],
        catch_exceptions=False,
    )
    assert result.exit_code == 0, result.output
    updated = json.loads(result.output)
    assert updated["trust"]["source_count"] == 3
