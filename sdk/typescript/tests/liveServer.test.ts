/** End-to-end contract check: the SDK against the *real* backend (a spawned
 * uvicorn process, real HTTP, no mocks). Guards against the hand-written
 * response types drifting from the actual backend — the same role the
 * Python SDK's test_integration_live_app.py plays.
 */

import { afterAll, beforeAll, describe, expect, it } from "vitest";

import { MIPClient } from "../src/client.js";
import { ConcurrencyError, IdentityError } from "../src/errors.js";
import { startLiveServer, type LiveServer } from "./liveServer.js";

const PORT = 18_773;

let server: LiveServer;
let client: MIPClient;

beforeAll(async () => {
  server = await startLiveServer(PORT);
  client = new MIPClient(server.baseUrl);
}, 30_000);

afterAll(async () => {
  await server.stop();
});

describe("MIPClient against the real backend", () => {
  it("supports the full create -> search -> explain -> context -> archive -> restore -> delete lifecycle", async () => {
    const created = await client.memories.create({
      namespace: "demo",
      owner_id: "user-1",
      title: "TS SDK integration memory",
      summary: "Testing the TypeScript SDK end to end.",
      semantics: { keywords: ["integration", "typescript"] },
      provenance: { source: "ts-sdk-integration-test" },
    });
    expect(created.lifecycle.state).toBe("Active");
    expect(created.lifecycle.version).toBe(1);

    const fetched = await client.memories.get(created.memory_id);
    expect(fetched.memory_id).toBe(created.memory_id);

    const updated = await client.memories.update(
      created.memory_id,
      { title: "Updated via TS SDK" },
      { expectedVersion: 1 },
    );
    expect(updated.lifecycle.version).toBe(2);
    expect(updated.content.title).toBe("Updated via TS SDK");

    const page = await client.memories.list({ namespace: "demo" });
    expect(page.items.some((record) => record.memory_id === created.memory_id)).toBe(true);

    const versions = await client.memories.listVersions(created.memory_id);
    expect(versions.map((v) => v.version)).toEqual([1, 2]);

    const searchResponse = await client.search.search({ query: "integration", mode: "keyword" });
    expect(searchResponse.items.some((item) => item.memory_id === created.memory_id)).toBe(true);

    const explanation = await client.explain.explain({
      memory_id: created.memory_id,
      query: "integration",
    });
    expect(explanation.confidence).toBeGreaterThanOrEqual(0);
    expect(explanation.confidence).toBeLessThanOrEqual(1);
    expect(explanation.ranking?.matched).toBe(true);

    const contextPackage = await client.context.build({ query: "integration", namespace: "demo" });
    expect(contextPackage.total_candidates).toBeGreaterThanOrEqual(1);

    const archived = await client.memories.archive(created.memory_id);
    expect(archived.lifecycle.state).toBe("Archived");
    const restored = await client.memories.restore(created.memory_id);
    expect(restored.lifecycle.state).toBe("Active");

    const deleteResult = await client.memories.delete(created.memory_id);
    expect(deleteResult).toBeTruthy();

    const health = await client.admin.health();
    expect(health.status).toBe("ok");

    const rebuildReport = await client.admin.rebuildProjections();
    expect(rebuildReport).toHaveProperty("indexed_memories");
  }, 20_000);

  it("surfaces a 404 as a typed IdentityError", async () => {
    await expect(
      client.memories.get("00000000-0000-0000-0000-000000000000"),
    ).rejects.toBeInstanceOf(IdentityError);
  });

  it("surfaces a version conflict as a typed ConcurrencyError", async () => {
    const created = await client.memories.create({
      namespace: "demo",
      owner_id: "user-1",
      title: "Conflict test",
      semantics: { keywords: ["conflict"] },
      provenance: { source: "ts-sdk-integration-test" },
    });

    await expect(
      client.memories.update(created.memory_id, { title: "stale" }, { expectedVersion: 99 }),
    ).rejects.toBeInstanceOf(ConcurrencyError);
  });
});
