# @mip/sdk — TypeScript SDK

Official TypeScript client for the Memory Intelligence Platform REST API (`/v1`). Thin
typed wrapper over `fetch` — zero runtime dependencies. Request types are generated
from the backend's OpenAPI schema; response types are hand-written (see
`../../project-memory-bank/adr/ADR-0005-developer-platform-architecture.md` for why).

## Quickstart

```bash
cd sdk/typescript
npm install
npm run build
```

```ts
import { MIPClient } from "@mip/sdk";

const client = new MIPClient("http://localhost:8000");

const memory = await client.memories.create({
  namespace: "demo",
  owner_id: "user-1",
  title: "Q3 onboarding notes",
  summary: "Key steps for new hires.",
  semantics: { keywords: ["onboarding", "notes"] },
  provenance: { source: "manual-entry" },
});
console.log(memory.memory_id, memory.lifecycle.state);

const results = await client.search.search({ query: "onboarding", mode: "hybrid" });
for (const item of results.items) console.log(item.memory_id, item.score);

const updated = await client.memories.update(
  memory.memory_id,
  { title: "Q3 onboarding notes (revised)" },
  { expectedVersion: 1 },
);
```

A runnable version is at `../../examples/typescript/quickstart.ts`.

## Error handling

Every failure throws a typed exception mirroring the `MEM-*` envelope — key on
`.code`, never on `.message`:

```ts
import { ConcurrencyError, MIPAPIError } from "@mip/sdk";

try {
  await client.memories.update(memoryId, spec, { expectedVersion: 1 });
} catch (err) {
  if (err instanceof ConcurrencyError) console.log(err.code, err.details); // MEM-4001
  else if (err instanceof MIPAPIError) console.log(err.code, err.category, err.message);
  else throw err;
}
```

## Regenerating request types

After a backend API change: `python ../../backend/scripts/export_openapi.py` then
`npm run generate:types` (regenerates `src/generated/schema.ts`). Response types in
`src/types.ts` are hand-written and must be updated to match
`sdk/python/mip_sdk/models/{memory,retrieval}.py` — the one accepted asymmetry.

## Quality gates (all must pass)

```bash
npm run lint
npm run typecheck
npm test        # includes tests/liveServer.test.ts — spawns the real backend, no mocks
npm run build
```

## Layout

```text
src/
├── client.ts        # MIPClient — the entry point
├── http.ts           # transport: envelope unwrapping, error translation (only fetch caller)
├── errors.ts         # MIPAPIError hierarchy ↔ MEM-1000..8000 categories
├── types.ts          # generated request types re-exported + hand-written response types
├── generated/        # schema.ts — do not hand-edit, regenerate instead
└── resources/         # memories.ts, retrieval.ts (search/explain/context), admin.ts
```
