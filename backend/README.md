# MIP Core — Backend

Local-first Memory Operating System core service (Phase 1: Core Memory Engine).
Architecture: `../project-memory-bank/03-system-architecture.md` · API: `../project-memory-bank/05-api-design.md`.

## Quickstart

```bash
cd backend
python -m venv .venv && .venv/Scripts/activate   # Windows (use bin/activate on POSIX)
pip install -e .[dev]
uvicorn mip.api.main:app --reload                # serves http://127.0.0.1:8000 (OpenAPI at /docs)
```

Data lives in `./data/mip.db` (SQLite, WAL). Override with `MIP_DB_PATH`.

## Quality gates (all must pass)

```bash
ruff check . && ruff format --check .
mypy
pytest
```

Normative suites live in `tests/invariants/`, `tests/lifecycle/`, `tests/api/` — they are never
allowed to be red or skipped (see `../project-memory-bank/20-testing-strategy.md`).

## Layout

```text
mip/
├── api/        # FastAPI transport: routes, DTOs, middleware, error envelope
├── core/       # pure domain: model, states, invariants, errors — no I/O
├── engines/    # validation, memory_manager (lifecycle orchestration)
├── events/     # event types + projection rebuild (event sourcing)
├── storage/    # repository interfaces + sqlite/ adapters (all SQL lives here)
└── config.py   # pydantic-settings (MIP_* env vars)
```
