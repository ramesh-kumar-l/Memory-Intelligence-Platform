from __future__ import annotations

import json

from click.testing import CliRunner

from mip_cli.main import cli


def _create(runner: CliRunner, *, title: str = "CLI test memory") -> dict[str, object]:
    result = runner.invoke(
        cli,
        [
            "--json",
            "memories",
            "create",
            "--namespace",
            "demo",
            "--owner",
            "user-1",
            "--title",
            title,
            "--summary",
            "A memory created by the CLI test suite.",
            "--keyword",
            "cli",
            "--keyword",
            "test",
            "--source",
            "cli-test-suite",
        ],
        catch_exceptions=False,
    )
    assert result.exit_code == 0, result.output
    data: dict[str, object] = json.loads(result.output)
    return data


def test_create_and_get(cli_client: CliRunner) -> None:
    created = _create(cli_client)
    memory_id = created["memory_id"]

    result = cli_client.invoke(
        cli, ["--json", "memories", "get", str(memory_id)], catch_exceptions=False
    )
    assert result.exit_code == 0
    fetched = json.loads(result.output)
    assert fetched["memory_id"] == memory_id
    assert fetched["content"]["title"] == "CLI test memory"


def test_create_table_output_shows_title(cli_client: CliRunner) -> None:
    result = cli_client.invoke(
        cli,
        [
            "memories",
            "create",
            "--namespace",
            "demo",
            "--owner",
            "user-1",
            "--title",
            "Table output memory",
            "--source",
            "cli-test-suite",
            "--keyword",
            "table",
        ],
        catch_exceptions=False,
    )
    assert result.exit_code == 0
    assert "Table output memory" in result.output
    assert "Active" in result.output


def test_list_memories(cli_client: CliRunner) -> None:
    _create(cli_client, title="List me")
    result = cli_client.invoke(
        cli, ["--json", "memories", "list", "--namespace", "demo"], catch_exceptions=False
    )
    assert result.exit_code == 0
    page = json.loads(result.output)
    assert any(item["title"] == "List me" for item in page["items"])


def test_update_requires_if_match(cli_client: CliRunner) -> None:
    created = _create(cli_client)
    result = cli_client.invoke(
        cli,
        [
            "--json",
            "memories",
            "update",
            str(created["memory_id"]),
            "--if-match",
            "1",
            "--title",
            "Updated via CLI",
        ],
        catch_exceptions=False,
    )
    assert result.exit_code == 0
    updated = json.loads(result.output)
    assert updated["content"]["title"] == "Updated via CLI"
    assert updated["lifecycle"]["version"] == 2


def test_archive_restore_and_delete(cli_client: CliRunner) -> None:
    created = _create(cli_client)
    memory_id = str(created["memory_id"])

    archived = cli_client.invoke(cli, ["memories", "archive", memory_id], catch_exceptions=False)
    assert archived.exit_code == 0
    assert "Archived" in archived.output

    restored = cli_client.invoke(cli, ["memories", "restore", memory_id], catch_exceptions=False)
    assert restored.exit_code == 0
    assert "Active" in restored.output

    deleted = cli_client.invoke(
        cli, ["--json", "memories", "delete", memory_id], catch_exceptions=False
    )
    assert deleted.exit_code == 0


def test_version_conflict_exits_nonzero_with_error_message(cli_client: CliRunner) -> None:
    created = _create(cli_client)
    result = cli_client.invoke(
        cli,
        [
            "memories",
            "update",
            str(created["memory_id"]),
            "--if-match",
            "99",
            "--title",
            "stale",
        ],
    )
    assert result.exit_code == 1
    assert "MEM-4001" in result.output


def test_get_missing_memory_exits_nonzero(cli_client: CliRunner) -> None:
    result = cli_client.invoke(cli, ["memories", "get", "00000000-0000-0000-0000-000000000000"])
    assert result.exit_code == 1
    assert "MEM-3001" in result.output
