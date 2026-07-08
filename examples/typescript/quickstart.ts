/** Runnable TypeScript SDK quickstart.
 *
 * Prereqs: a running MIP backend (see backend/README.md), and `@mip/sdk` built
 * (`npm install && npm run build --workspace=@mip/sdk` from the repo root).
 *
 * Usage (from the repo root, Node >=22.6 strips types natively):
 *   node examples/typescript/quickstart.ts [baseUrl]
 */

import { ConcurrencyError, MIPClient } from "@mip/sdk";

async function main(): Promise<void> {
  const baseUrl = process.argv[2] ?? "http://localhost:8000";
  const client = new MIPClient(baseUrl);

  const health = await client.admin.health();
  console.log(`backend status: ${health.status}`);

  const memory = await client.memories.create({
    namespace: "demo",
    owner_id: "user-1",
    title: "Q3 onboarding notes",
    summary: "Key steps for new hires.",
    semantics: { keywords: ["onboarding", "notes"] },
    provenance: { source: "quickstart-example" },
  });
  console.log(`created ${memory.memory_id} (version ${memory.lifecycle.version})`);

  const results = await client.search.search({ query: "onboarding", mode: "hybrid" });
  console.log(`search found ${results.items.length} result(s)`);
  for (const item of results.items) console.log(`  ${item.memory_id} score=${item.score.toFixed(4)}`);

  const explanation = await client.explain.explain({ memory_id: memory.memory_id, query: "onboarding" });
  console.log(`confidence=${explanation.confidence.toFixed(2)} freshness=${explanation.freshness.toFixed(2)}`);

  const updated = await client.memories.update(
    memory.memory_id,
    { title: "Q3 onboarding notes (revised)" },
    { expectedVersion: 1 },
  );
  console.log(`updated to version ${updated.lifecycle.version}: ${JSON.stringify(updated.content.title)}`);

  try {
    await client.memories.update(memory.memory_id, { title: "stale update" }, { expectedVersion: 1 });
  } catch (err) {
    if (err instanceof ConcurrencyError) {
      console.log(`expected conflict: ${err.code} ${JSON.stringify(err.details)}`);
    } else {
      throw err;
    }
  }

  const archived = await client.memories.archive(memory.memory_id);
  console.log(`archived (state=${archived.lifecycle.state})`);
  const restored = await client.memories.restore(memory.memory_id);
  console.log(`restored (state=${restored.lifecycle.state})`);

  // Delete is only legal from Active (INV-STATE-002) — restore first.
  await client.memories.delete(memory.memory_id);
  console.log("deleted the demo memory");
}

main().catch((err: unknown) => {
  console.error(err);
  process.exitCode = 1;
});
