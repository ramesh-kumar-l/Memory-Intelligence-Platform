import type { MemoryObject, MemoryRecord, Page } from "@mip/sdk";
import { vi } from "vitest";

export const MEMORY_ID = "5f8d9a4e-1b2c-4d3e-9f0a-1234567890ab";

export function sampleMemoryObject(overrides: Partial<MemoryObject> = {}): MemoryObject {
  const base: MemoryObject = {
    memory_id: MEMORY_ID,
    header: { schema_version: "1.0", object_type: "Experience", encoding_version: "1.0", checksum: null },
    identity: {
      memory_id: MEMORY_ID,
      namespace: "demo",
      owner_id: "user-1",
      tenant_id: null,
      parent_id: null,
      root_episode_id: null,
    },
    content: {
      title: "Sample memory",
      summary: "A short summary.",
      description: "",
      language: "en",
      attachments: [],
      media_refs: [],
      notes: [],
    },
    semantics: {
      entities: [],
      concepts: [],
      activities: [],
      events: [],
      locations: [],
      topics: ["onboarding"],
      timestamps: [],
      keywords: ["sample"],
      sentiment: null,
      intent: null,
    },
    relationships: [],
    context: {
      importance_score: 0.5,
      recency_score: 1,
      access_frequency: 0,
      last_accessed: null,
      relevance_tags: [],
      goals: [],
    },
    trust: {
      confidence: 0.8,
      freshness: 1,
      provenance: { source: "test-suite", method: null, location: null, captured_at: null, agent: null },
      evidence: [],
      verification_status: "Unknown",
      source_count: 1,
      explanation: "",
    },
    lifecycle: {
      version: 1,
      state: "Active",
      created_at: "2026-07-08T00:00:00Z",
      updated_at: null,
      archived_at: null,
      deleted_at: null,
      consolidation_count: 0,
    },
    extensions: {},
    audit: {
      created_by: "req-1",
      updated_by: null,
      update_reason: null,
      change_set: null,
      trace_id: "trace-1",
      request_id: "req-1",
    },
  };
  return { ...base, ...overrides };
}

export function sampleMemoryRecord(overrides: Partial<MemoryRecord> = {}): MemoryRecord {
  const base: MemoryRecord = {
    memory_id: MEMORY_ID,
    namespace: "demo",
    owner_id: "user-1",
    object_type: "Experience",
    title: "Sample memory",
    state: "Active",
    current_version: 1,
    created_at: "2026-07-08T00:00:00Z",
    updated_at: null,
    archived_at: null,
    deleted_at: null,
    consolidation_count: 0,
  };
  return { ...base, ...overrides };
}

export function samplePage(items: MemoryRecord[] = [sampleMemoryRecord()]): Page<MemoryRecord> {
  return { items, complete: true, continuation_token: null };
}

/** A hand-rolled stand-in for `MIPClient` shaped exactly like the resources
 * the console's hooks call — avoids adding a network-mocking dependency for
 * page-level tests.
 */
export function createFakeClient() {
  return {
    memories: {
      list: vi.fn().mockResolvedValue(samplePage()),
      get: vi.fn().mockResolvedValue(sampleMemoryObject()),
      listVersions: vi
        .fn()
        .mockResolvedValue([{ version: 1, previous_version: null, created_at: "2026-07-08T00:00:00Z" }]),
      create: vi.fn(),
      update: vi.fn(),
      archive: vi.fn().mockResolvedValue(sampleMemoryObject({ lifecycle: { ...sampleMemoryObject().lifecycle, state: "Archived" } })),
      restore: vi.fn().mockResolvedValue(sampleMemoryObject()),
      delete: vi.fn().mockResolvedValue({ memory_id: MEMORY_ID, deleted: true }),
      relationships: vi.fn().mockResolvedValue({ memory_id: MEMORY_ID, relationships: [] }),
    },
    search: {
      search: vi.fn().mockResolvedValue({
        query: "onboarding",
        mode: "hybrid",
        items: [{ memory_id: MEMORY_ID, score: 0.87, explanation: { mode: "hybrid", keyword_score: 0.9, semantic_score: 0.8 } }],
        complete: true,
        continuation_token: null,
      }),
    },
    explain: {
      explain: vi.fn().mockResolvedValue({
        memory_id: MEMORY_ID,
        confidence: 0.8,
        freshness: 0.95,
        verification_status: "Unknown",
        source_count: 1,
        provenance: { source: "test-suite" },
        evidence: [],
        ranking: null,
      }),
    },
    context: {
      build: vi.fn(),
    },
    admin: {
      health: vi.fn().mockResolvedValue({ status: "ok", storage: true }),
    },
    consolidate: {
      consolidate: vi.fn().mockResolvedValue(
        sampleMemoryObject({ lifecycle: { ...sampleMemoryObject().lifecycle, consolidation_count: 1 } }),
      ),
    },
    learn: {
      learn: vi.fn().mockResolvedValue(
        sampleMemoryObject({
          semantics: { ...sampleMemoryObject().semantics, concepts: ["durability"] },
        }),
      ),
    },
    portability: {
      export: vi.fn().mockResolvedValue({
        schema_version: "1.0",
        exported_at: "2026-07-08T00:00:00Z",
        namespace: "demo",
        memory_count: 1,
        memories: [],
      }),
      import_: vi.fn().mockResolvedValue({ imported: [], skipped: [], rejected: [] }),
    },
  };
}

export type FakeClient = ReturnType<typeof createFakeClient>;
