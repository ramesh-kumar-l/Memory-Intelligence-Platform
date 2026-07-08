import type { MemoryObject, MemoryRecord } from "../src/types.js";

export const MEMORY_ID = "5f8d9a4e-1b2c-4d3e-9f0a-1234567890ab";

export function sampleMemoryObject(overrides: Partial<MemoryObject> = {}): MemoryObject {
  const base: MemoryObject = {
    memory_id: MEMORY_ID,
    header: {
      schema_version: "1.0",
      object_type: "Experience",
      encoding_version: "1.0",
      checksum: null,
    },
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
      concepts: ["onboarding"],
      activities: [],
      events: [],
      locations: [],
      topics: [],
      timestamps: [],
      keywords: ["sample"],
      sentiment: null,
      intent: null,
    },
    relationships: [],
    context: {
      importance_score: 0.5,
      recency_score: 1.0,
      access_frequency: 0,
      last_accessed: null,
      relevance_tags: [],
      goals: [],
    },
    trust: {
      confidence: 0.8,
      freshness: 1.0,
      provenance: {
        source: "test-suite",
        method: null,
        location: null,
        captured_at: null,
        agent: null,
      },
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
  };
  return { ...base, ...overrides };
}
