# mip-sdk — Python SDK

Official Python client for the Memory Intelligence Platform REST API (`/v1`). A thin
typed wrapper — every call is a plain HTTP request; no engine or storage logic lives here.
Architecture: `../../project-memory-bank/adr/ADR-0005-developer-platform-architecture.md`.

## Quickstart

```bash
cd sdk/python
python -m venv .venv && .venv/Scripts/activate   # Windows (use bin/activate on POSIX)
pip install -e .[dev]
```

```python
from mip_sdk import MIPClient
from mip_sdk.models.memory import Semantics
from mip_sdk.models.requests import CreateMemoryRequest, ProvenanceInput, UpdateMemoryRequest

with MIPClient("http://localhost:8000") as client:
    memory = client.memories.create(CreateMemoryRequest(
        namespace="demo",
        owner_id="user-1",
        title="Q3 onboarding notes",
        summary="Key steps for new hires.",
        semantics=Semantics(keywords=("onboarding", "notes")),
        provenance=ProvenanceInput(source="manual-entry"),
    ))
    print(memory.memory_id, memory.lifecycle.state)

    results = client.search.search(query="onboarding", mode="hybrid")
    for item in results.items:
        print(item.memory_id, item.score)

    updated = client.memories.update(
        memory.memory_id,
        UpdateMemoryRequest(title="Q3 onboarding notes (revised)"),
        expected_version=1,
    )
```

A runnable version of this is at `../../examples/python/quickstart.py`.

## Error handling

Every failure raises a typed exception mirroring the `MEM-*` envelope
(`../../project-memory-bank/05-api-design.md`) — key on `.code`, never on `.message`:

```python
from mip_sdk.errors import ConcurrencyError, MIPAPIError

try:
    client.memories.update(memory_id, spec, expected_version=1)
except ConcurrencyError as exc:
    print(exc.code, exc.details)          # MEM-4001, {"expected": 1, "actual": 2}
except MIPAPIError as exc:
    print(exc.code, exc.category, exc.message)
```

## Quality gates (all must pass)

```bash
ruff check . && ruff format --check .
mypy
pytest
```

`tests/test_integration_live_app.py` runs the SDK against the real backend app
in-process (via `fastapi.testclient.TestClient`) — no mocks — to catch drift between
this package's hand-written response models and the actual API.

## Layout

```text
mip_sdk/
├── client.py       # MIPClient — the entry point
├── _http.py        # transport: envelope unwrapping, error translation (only httpx import)
├── errors.py       # MIPAPIError hierarchy ↔ MEM-1000..8000 categories
├── models/         # memory.py (response models), requests.py, retrieval.py
└── resources/      # memories.py, retrieval.py (search/explain/context), admin.py
```
