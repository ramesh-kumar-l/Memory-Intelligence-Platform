# Quickstart Examples

Runnable, end-to-end examples for each Phase 3 client, all against a plain running
backend (`cd backend && uvicorn mip.api.main:app --reload`). Each one: creates a
memory, searches for it, explains it, updates it (and demonstrates the expected
`MEM-4001` version conflict), then archives/restores/deletes it.

| Client | Run |
| --- | --- |
| Python SDK | `python examples/python/quickstart.py [base_url]` (after `pip install -e sdk/python`) |
| TypeScript SDK | `node examples/typescript/quickstart.ts [base_url]` (after `npm install && npm run build --workspace=@mip/sdk` from the repo root) |
| CLI | `examples/cli/quickstart.sh [base_url]` (after `pip install -e sdk/python -e cli`) |
| Console | see `../frontend/README.md` — `npm run dev` and open the Memories/Search/Settings pages |

All three scripted examples were run against a real backend during Phase 3
development to confirm they work, not just read plausibly.
