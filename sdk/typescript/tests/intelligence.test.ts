import { describe, expect, it } from "vitest";

import { MIPClient } from "../src/client.js";
import type { ConsolidateRequestBody, LearnRequestBody } from "../src/types.js";
import { MEMORY_ID, sampleMemoryObject } from "./factories.js";
import { envelope, fakeFetch, jsonResponse } from "./testUtils.js";

describe("ConsolidateResource", () => {
  it("consolidate() posts primary + duplicate ids", async () => {
    let capturedBody: unknown;
    const client = new MIPClient("http://mip.test", {
      fetchImpl: fakeFetch(async (req) => {
        expect(req.url).toBe("http://mip.test/v1/consolidate");
        capturedBody = JSON.parse(req.body ?? "{}");
        return jsonResponse(
          envelope(sampleMemoryObject({ lifecycle: { ...sampleMemoryObject().lifecycle, consolidation_count: 1 } })),
        );
      }),
    });

    const request: ConsolidateRequestBody = {
      primary_memory_id: MEMORY_ID,
      duplicate_memory_ids: ["dup-1"],
    };
    const merged = await client.consolidate.consolidate(request);
    expect(merged.lifecycle.consolidation_count).toBe(1);
    expect(capturedBody).toEqual(request);
  });
});

describe("LearnResource", () => {
  it("learn() posts derived semantics and sends the Idempotency-Key header", async () => {
    let seenHeader: string | null = null;
    const client = new MIPClient("http://mip.test", {
      fetchImpl: fakeFetch(async (req) => {
        seenHeader = req.headers.get("Idempotency-Key");
        return jsonResponse(envelope(sampleMemoryObject()));
      }),
    });

    const request: LearnRequestBody = {
      memory_id: MEMORY_ID,
      derived: { concepts: ["replication"] },
      reason: "pattern observed",
    };
    await client.learn.learn(request, { idempotencyKey: "learn-key-1" });
    expect(seenHeader).toBe("learn-key-1");
  });
});
