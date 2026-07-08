# mip-cli — Command-Line Interface

Official CLI for the Memory Intelligence Platform, built on `mip_sdk`. Every command
parses args, calls the SDK, and formats the result — no business logic lives here.

## Quickstart

```bash
cd cli
python -m venv .venv && .venv/Scripts/activate   # Windows (use bin/activate on POSIX)
pip install -e .[dev]
pip install -e ../sdk/python

mip --api-url http://localhost:8000 admin health

mip memories create --namespace demo --owner user-1 --title "Q3 onboarding notes" \
  --summary "Key steps for new hires." --keyword onboarding --keyword notes \
  --source manual-entry

mip memories list --namespace demo
mip search "onboarding" --mode hybrid
mip explain <memory_id> --query onboarding
```

Pass `--json` before the subcommand for machine-readable output, e.g.
`mip --json memories list`. Set `MIP_API_URL` to avoid repeating `--api-url`.

A runnable walkthrough is at `../examples/cli/quickstart.sh`.

## Commands

| Group | Commands |
| --- | --- |
| `memories` | `create`, `get`, `list`, `update`, `delete`, `archive`, `restore`, `versions` |
| — | `search`, `explain`, `context` (top-level — mirror the canonical retrieval operations) |
| `admin` | `health`, `version`, `rebuild` |

Every command exits non-zero and prints the `MEM-*` code on API failure (e.g. a stale
`--if-match` on `memories update` prints `MEM-4001` and exits 1).

## Quality gates (all must pass)

```bash
ruff check . && ruff format --check .
mypy
pytest
```

`tests/` run every command against the real backend app in-process (via
`click.testing.CliRunner` + `fastapi.testclient.TestClient`), not a mock.
