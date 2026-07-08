"""`mip export|import` CLI tests (Phase 4 task 4, ADR-0006)."""

from __future__ import annotations

import json
from pathlib import Path

from click.testing import CliRunner

from mip_cli.main import cli
from tests.test_cli_memories import _create


def test_export_writes_bundle_to_file(cli_client: CliRunner, tmp_path: Path) -> None:
    _create(cli_client, title="exportable")
    output = tmp_path / "bundle.json"
    result = cli_client.invoke(
        cli, ["export", "--namespace", "demo", "--output", str(output)], catch_exceptions=False
    )
    assert result.exit_code == 0, result.output
    assert output.exists()
    bundle = json.loads(output.read_text(encoding="utf-8"))
    assert bundle["memory_count"] >= 1


def test_export_then_import_round_trips(cli_client: CliRunner, tmp_path: Path) -> None:
    created = _create(cli_client, title="round trip cli memory")
    output = tmp_path / "bundle.json"
    cli_client.invoke(
        cli, ["export", "--namespace", "demo", "--output", str(output)], catch_exceptions=False
    )

    result = cli_client.invoke(cli, ["--json", "import", str(output)], catch_exceptions=False)
    assert result.exit_code == 0, result.output
    report = json.loads(result.output)
    assert any(skip["memory_id"] == created["memory_id"] for skip in report["skipped"])
    assert report["rejected"] == []
