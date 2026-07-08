/** Phase 4 end-to-end check against the real backend (ADR-0006): graph
 * relationships, Consolidate, Learn, Export/Import round-trip.
 */

import { afterAll, beforeAll, describe, expect, it } from "vitest";

import { MIPClient } from "../src/client.js";
import type { ExportBundle, RelationshipSpec } from "../src/types.js";
import { startLiveServer, type LiveServer } from "./liveServer.js";

const PORT = 18_774;

let server: LiveServer;
let client: MIPClient;

beforeAll(async () => {
  server = await startLiveServer(PORT);
  client = new MIPClient(server.baseUrl);
}, 30_000);

afterAll(async () => {
  await server.stop();
});

async function create(title: string, relationships: RelationshipSpec[] = []) {
  return client.memories.create({
    namespace: "phase4",
    owner_id: "user-1",
    title,
    semantics: { keywords: ["phase4"] },
    provenance: { source: "ts-sdk-phase4-test" },
    relationships,
  });
}

describe("MIPClient Phase 4 operations against the real backend", () => {
  it("graph search mode + relationships view", async () => {
    const target = await create("graph target");
    const source = await create("graph source", [
      { target_memory_id: target.memory_id, type: "references" as const },
    ]);

    const results = await client.search.search({ query: source.memory_id, mode: "graph" });
    expect(results.items[0]?.memory_id).toBe(target.memory_id);

    const edges = await client.memories.relationships(source.memory_id);
    expect(edges.relationships[0]?.target_memory_id).toBe(target.memory_id);
  }, 20_000);

  it("consolidate merges a duplicate and preserves history", async () => {
    const primary = await create("primary");
    const duplicate = await create("duplicate");
    const merged = await client.consolidate.consolidate({
      primary_memory_id: primary.memory_id,
      duplicate_memory_ids: [duplicate.memory_id],
    });
    expect(merged.lifecycle.consolidation_count).toBe(1);
    const archived = await client.memories.get(duplicate.memory_id);
    expect(archived.lifecycle.state).toBe("Archived");
  });

  it("learn unions derived semantics and matures evidence", async () => {
    const memory = await create("learnable memory");
    const updated = await client.learn.learn({
      memory_id: memory.memory_id,
      derived: { concepts: ["durability"] },
      new_evidence: [{ source: "doc-1" }, { source: "doc-2" }],
      reason: "corroborating documents found",
    });
    expect(updated.semantics.concepts).toContain("durability");
    expect(updated.trust.source_count).toBe(3);
    expect(updated.trust.verification_status).toBe("Verified");
  });

  it("export then import round-trips (already-present memories are skipped)", async () => {
    const memory = await create("export me");
    const bundle: ExportBundle = await client.portability.export({ namespace: "phase4" });
    expect(bundle.memory_count).toBeGreaterThanOrEqual(1);

    const report = await client.portability.import_(bundle);
    expect(report.skipped.some((skip) => skip.memory_id === memory.memory_id)).toBe(true);
    expect(report.rejected).toEqual([]);
  });
});
