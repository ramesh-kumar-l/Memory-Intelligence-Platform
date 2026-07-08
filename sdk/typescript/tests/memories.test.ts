import { describe, expect, it } from "vitest";

import { MIPClient } from "../src/client.js";
import type { CreateMemoryRequest, UpdateMemoryRequest } from "../src/types.js";
import { MEMORY_ID, sampleMemoryObject, sampleMemoryRecord } from "./factories.js";
import { envelope, fakeFetch, jsonResponse } from "./testUtils.js";

const baseCreateRequest: CreateMemoryRequest = {
  namespace: "demo",
  owner_id: "user-1",
  title: "Sample memory",
  semantics: { keywords: ["sample"] },
  provenance: { source: "test-suite" },
};

describe("MemoriesResource", () => {
  it("create() returns a typed MemoryObject and posts the body", async () => {
    let capturedBody: unknown;
    const client = new MIPClient("http://mip.test", {
      fetchImpl: fakeFetch(async (req) => {
        expect(req.method).toBe("POST");
        expect(req.url).toBe("http://mip.test/v1/memories");
        capturedBody = JSON.parse(req.body ?? "{}");
        return jsonResponse(envelope(sampleMemoryObject()), 201);
      }),
    });

    const memory = await client.memories.create(baseCreateRequest);
    expect(memory.memory_id).toBe(MEMORY_ID);
    expect(memory.content.title).toBe("Sample memory");
    expect((capturedBody as { title: string }).title).toBe("Sample memory");
  });

  it("create() sends the Idempotency-Key header", async () => {
    let seenHeader: string | null = null;
    const client = new MIPClient("http://mip.test", {
      fetchImpl: fakeFetch(async (req) => {
        seenHeader = req.headers.get("Idempotency-Key");
        return jsonResponse(envelope(sampleMemoryObject()), 201);
      }),
    });

    await client.memories.create(baseCreateRequest, { idempotencyKey: "key-123" });
    expect(seenHeader).toBe("key-123");
  });

  it("get() passes the version query param", async () => {
    const client = new MIPClient("http://mip.test", {
      fetchImpl: fakeFetch(async (req) => {
        expect(req.url).toBe(`http://mip.test/v1/memories/${MEMORY_ID}?version=2`);
        return jsonResponse(
          envelope(sampleMemoryObject({ lifecycle: { ...sampleMemoryObject().lifecycle, version: 2 } })),
        );
      }),
    });

    const memory = await client.memories.get(MEMORY_ID, { version: 2 });
    expect(memory.lifecycle.version).toBe(2);
  });

  it("list() returns lightweight MemoryRecord items, not full Memory Objects", async () => {
    const client = new MIPClient("http://mip.test", {
      fetchImpl: fakeFetch(async (req) => {
        expect(req.url).toBe("http://mip.test/v1/memories?namespace=demo&limit=10");
        return jsonResponse(
          envelope({ items: [sampleMemoryRecord()], complete: false, continuation_token: "mid:next" }),
        );
      }),
    });

    const page = await client.memories.list({ namespace: "demo", limit: 10 });
    expect(page.items).toHaveLength(1);
    expect(page.items[0]?.memory_id).toBe(MEMORY_ID);
    expect(page.complete).toBe(false);
    expect(page.continuation_token).toBe("mid:next");
  });

  it("update() sends If-Match and the partial body", async () => {
    let seenIfMatch: string | null = null;
    const client = new MIPClient("http://mip.test", {
      fetchImpl: fakeFetch(async (req) => {
        seenIfMatch = req.headers.get("If-Match");
        const body = JSON.parse(req.body ?? "{}") as UpdateMemoryRequest;
        expect(body.title).toBe("New title");
        return jsonResponse(
          envelope(sampleMemoryObject({ content: { ...sampleMemoryObject().content, title: "New title" } })),
        );
      }),
    });

    const memory = await client.memories.update(
      MEMORY_ID,
      { title: "New title" },
      { expectedVersion: 1 },
    );
    expect(seenIfMatch).toBe("1");
    expect(memory.content.title).toBe("New title");
  });

  it("delete()/archive()/restore() hit the right endpoints", async () => {
    const calls: string[] = [];
    const client = new MIPClient("http://mip.test", {
      fetchImpl: fakeFetch(async (req) => {
        calls.push(`${req.method} ${new URL(req.url).pathname}`);
        if (req.method === "DELETE") return jsonResponse(envelope({ memory_id: MEMORY_ID, deleted: true }));
        const state = req.url.endsWith("archive") ? "Archived" : "Active";
        return jsonResponse(
          envelope(sampleMemoryObject({ lifecycle: { ...sampleMemoryObject().lifecycle, state } })),
        );
      }),
    });

    const archived = await client.memories.archive(MEMORY_ID);
    const restored = await client.memories.restore(MEMORY_ID);
    const deleted = await client.memories.delete(MEMORY_ID);

    expect(archived.lifecycle.state).toBe("Archived");
    expect(restored.lifecycle.state).toBe("Active");
    expect(deleted).toEqual({ memory_id: MEMORY_ID, deleted: true });
    expect(calls).toEqual([
      `POST /v1/memories/${MEMORY_ID}/archive`,
      `POST /v1/memories/${MEMORY_ID}/restore`,
      `DELETE /v1/memories/${MEMORY_ID}`,
    ]);
  });

  it("listVersions() returns VersionInfo rows", async () => {
    const client = new MIPClient("http://mip.test", {
      fetchImpl: fakeFetch(async () =>
        jsonResponse(
          envelope({
            memory_id: MEMORY_ID,
            versions: [{ version: 1, previous_version: null, created_at: "2026-07-08T00:00:00Z" }],
          }),
        ),
      ),
    });

    const versions = await client.memories.listVersions(MEMORY_ID);
    expect(versions).toHaveLength(1);
    expect(versions[0]?.version).toBe(1);
  });
});
