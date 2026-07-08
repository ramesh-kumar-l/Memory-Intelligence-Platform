import { describe, expect, it } from "vitest";

import { MIPClient } from "../src/client.js";
import { ValidationError } from "../src/errors.js";
import { MEMORY_ID, sampleMemoryObject } from "./factories.js";
import { envelope, errorEnvelope, fakeFetch, jsonResponse } from "./testUtils.js";

describe("SearchResource", () => {
  it("search() returns a typed SearchResponse", async () => {
    const client = new MIPClient("http://mip.test", {
      fetchImpl: fakeFetch(async (req) => {
        expect(new URL(req.url).pathname).toBe("/v1/search");
        const body = JSON.parse(req.body ?? "{}");
        expect(body.query).toBe("onboarding");
        return jsonResponse(
          envelope({
            query: "onboarding",
            mode: "hybrid",
            items: [
              {
                memory_id: MEMORY_ID,
                score: 0.87,
                explanation: { mode: "hybrid", keyword_score: 0.9, semantic_score: 0.8 },
              },
            ],
            complete: true,
            continuation_token: null,
          }),
        );
      }),
    });

    const response = await client.search.search({ query: "onboarding", mode: "hybrid" });
    expect(response.items).toHaveLength(1);
    expect(response.items[0]?.score).toBe(0.87);
  });

  it("unsupported mode surfaces as a typed ValidationError", async () => {
    const client = new MIPClient("http://mip.test", {
      fetchImpl: fakeFetch(async () =>
        jsonResponse(
          errorEnvelope({
            code: "MEM-1007",
            category: "Validation",
            message: "Requested search mode is not supported",
            details: { requested: "bogus", supported: ["keyword", "semantic", "hybrid"] },
          }),
          400,
        ),
      ),
    });

    await expect(client.search.search({ query: "x", mode: "bogus" })).rejects.toBeInstanceOf(
      ValidationError,
    );
    try {
      await client.search.search({ query: "x", mode: "bogus" });
      expect.unreachable("expected ValidationError to be thrown");
    } catch (err) {
      expect(err).toBeInstanceOf(ValidationError);
      expect((err as ValidationError).code).toBe("MEM-1007");
    }
  });
});

describe("ExplainResource", () => {
  it("explain() returns confidence, freshness, and ranking", async () => {
    const client = new MIPClient("http://mip.test", {
      fetchImpl: fakeFetch(async (req) => {
        expect(new URL(req.url).pathname).toBe("/v1/explain");
        return jsonResponse(
          envelope({
            memory_id: MEMORY_ID,
            confidence: 0.8,
            freshness: 0.95,
            verification_status: "Unknown",
            source_count: 1,
            provenance: { source: "test-suite" },
            evidence: [],
            ranking: { mode: "hybrid", score: 0.87, keyword_score: 0.9, semantic_score: 0.8, matched: true },
          }),
        );
      }),
    });

    const explanation = await client.explain.explain({ memory_id: MEMORY_ID, query: "onboarding" });
    expect(explanation.confidence).toBe(0.8);
    expect(explanation.ranking?.matched).toBe(true);
  });
});

describe("ContextResource", () => {
  it("build() returns a typed ContextPackage", async () => {
    const client = new MIPClient("http://mip.test", {
      fetchImpl: fakeFetch(async (req) => {
        expect(new URL(req.url).pathname).toBe("/v1/context");
        return jsonResponse(
          envelope({
            query: "onboarding",
            namespace: "demo",
            mode: "hybrid",
            items: [
              {
                memory: sampleMemoryObject(),
                relevance_score: 0.87,
                importance_score: 0.5,
                blended_score: 0.76,
              },
            ],
            complete: true,
            total_candidates: 1,
            continuation_token: null,
          }),
        );
      }),
    });

    const pkg = await client.context.build({ query: "onboarding", namespace: "demo" });
    expect(pkg.total_candidates).toBe(1);
    expect(pkg.items[0]?.memory.memory_id).toBe(MEMORY_ID);
  });
});
