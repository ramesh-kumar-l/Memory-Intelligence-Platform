/**
 * Request types are generated from the backend's OpenAPI schema (openapi.json
 * -> src/generated/schema.ts via `npm run generate:types`, ADR-0005).
 *
 * Response types are hand-written: FastAPI routes return raw `JSONResponse`
 * envelopes rather than `response_model=`-typed bodies (05-api-design.md —
 * OpenAPI here documents the transport, it is not the contract), so
 * `openapi-typescript` cannot generate anything useful for them. These mirror
 * `sdk/python/mip_sdk/models/{memory,retrieval}.py` field-for-field.
 */

import type { components } from "./generated/schema.js";

export type ObjectType = components["schemas"]["ObjectType"];
export type VerificationStatus = components["schemas"]["VerificationStatus"];
export type RelationshipType = components["schemas"]["RelationshipType"];
export type RelationshipDirection = components["schemas"]["RelationshipDirection"];
/** Request-shaped Semantics (fields optional, matches CreateMemoryRequest's
 * defaults) — NOT the same shape as the response's `Semantics` below, whose
 * array fields are always present (never undefined).
 */
export type SemanticsInput = components["schemas"]["Semantics"];
export type Provenance = components["schemas"]["Provenance"];
export type RelationshipSpec = components["schemas"]["RelationshipSpec"];
export type CreateMemoryRequest = components["schemas"]["CreateMemoryRequest"];
export type UpdateMemoryRequest = components["schemas"]["UpdateMemoryRequest"];
export type SearchRequestBody = components["schemas"]["SearchRequest"];
export type ExplainRequestBody = components["schemas"]["ExplainRequest"];
export type ContextRequestBody = components["schemas"]["ContextRequest"];
export type ConsolidateRequestBody = components["schemas"]["ConsolidateRequest"];
export type LearnRequestBody = components["schemas"]["LearnRequest"];
export type ExportRequestBody = components["schemas"]["ExportRequest"];

export type MemoryState =
  | "Created"
  | "Validating"
  | "ValidationFailed"
  | "Validated"
  | "Enriching"
  | "Indexed"
  | "GraphLinked"
  | "Active"
  | "Updating"
  | "Archived"
  | "Deleted";

export interface Header {
  schema_version: string;
  object_type: ObjectType;
  encoding_version: string;
  checksum: string | null;
}

export interface Identity {
  memory_id: string;
  namespace: string;
  owner_id: string;
  tenant_id: string | null;
  parent_id: string | null;
  root_episode_id: string | null;
}

export interface Content {
  title: string;
  summary: string;
  description: string;
  language: string;
  attachments: string[];
  media_refs: string[];
  notes: string[];
}

/** Section 4 as returned in a Memory Object — array fields are always
 * present (backend defaults to `()`, serialized as `[]`), unlike the
 * request-shaped `SemanticsInput` above.
 */
export interface Semantics {
  entities: string[];
  concepts: string[];
  activities: string[];
  events: string[];
  locations: string[];
  topics: string[];
  timestamps: string[];
  keywords: string[];
  sentiment: Record<string, unknown> | null;
  intent: Record<string, unknown> | null;
}

export interface Relationship {
  relationship_id: string;
  target_memory_id: string;
  type: RelationshipType;
  direction: RelationshipDirection;
  confidence: number;
  created_at: string;
  unresolved: boolean;
}

export interface Context {
  importance_score: number;
  recency_score: number;
  access_frequency: number;
  last_accessed: string | null;
  relevance_tags: string[];
  goals: string[];
}

export interface Trust {
  confidence: number;
  freshness: number;
  provenance: Provenance;
  evidence: Record<string, unknown>[];
  verification_status: VerificationStatus;
  source_count: number;
  explanation: string;
}

export interface Lifecycle {
  version: number;
  state: MemoryState;
  created_at: string;
  updated_at: string | null;
  archived_at: string | null;
  deleted_at: string | null;
  consolidation_count: number;
}

export interface AuditMetadata {
  created_by: string;
  updated_by: string | null;
  update_reason: string | null;
  change_set: string | null;
  trace_id: string | null;
  request_id: string | null;
}

/** Full Memory Object as returned by GetMemory/Create/Update/Archive/Restore. */
export interface MemoryObject {
  memory_id: string;
  header: Header;
  identity: Identity;
  content: Content;
  semantics: Semantics;
  relationships: Relationship[];
  context: Context;
  trust: Trust;
  lifecycle: Lifecycle;
  extensions: Record<string, unknown>;
  audit: AuditMetadata;
}

/** Lifecycle-summary projection row returned by list() — lighter than
 * MemoryObject; fetch a memory_id individually via `.get()` for the full object.
 */
export interface MemoryRecord {
  memory_id: string;
  namespace: string;
  owner_id: string;
  object_type: string;
  title: string;
  state: MemoryState;
  current_version: number;
  created_at: string;
  updated_at: string | null;
  archived_at: string | null;
  deleted_at: string | null;
  consolidation_count: number;
}

export interface VersionInfo {
  version: number;
  previous_version: number | null;
  created_at: string;
}

export interface Page<T> {
  items: T[];
  complete: boolean;
  continuation_token: string | null;
}

export interface SearchItemExplanation {
  mode: string;
  keyword_score: number | null;
  semantic_score: number | null;
}

export interface SearchItem {
  memory_id: string;
  score: number;
  explanation: SearchItemExplanation;
}

export interface SearchResponse {
  query: string;
  mode: string;
  items: SearchItem[];
  complete: boolean;
  continuation_token: string | null;
}

export interface RankingExplanation {
  mode: string;
  score: number;
  keyword_score: number | null;
  semantic_score: number | null;
  matched: boolean;
}

export interface Explanation {
  memory_id: string;
  confidence: number;
  freshness: number;
  verification_status: string;
  source_count: number;
  provenance: Record<string, unknown>;
  evidence: Record<string, unknown>[];
  ranking: RankingExplanation | null;
}

export interface ContextItem {
  memory: MemoryObject;
  relevance_score: number;
  importance_score: number;
  blended_score: number;
}

export interface ContextPackage {
  query: string;
  namespace: string | null;
  mode: string;
  items: ContextItem[];
  complete: boolean;
  total_candidates: number;
  continuation_token: string | null;
}

/** One relationship-graph edge (Phase 4 task 1, ADR-0006). */
export interface GraphEdge {
  relationship_id: string;
  source_memory_id: string;
  target_memory_id: string;
  type: string;
  direction: string;
  confidence: number;
}

/** `GET /v1/memories/{id}/relationships` response. */
export interface RelationshipsView {
  memory_id: string;
  relationships: GraphEdge[];
}

export interface ImportSkip {
  memory_id: string;
  reason: string;
}

export interface ImportRejection {
  memory_id: string | null;
  violations: Record<string, unknown>[];
}

/** `POST /v1/import` response (Phase 4 task 4, ADR-0006). */
export interface ImportReport {
  imported: string[];
  skipped: ImportSkip[];
  rejected: ImportRejection[];
}

/** `POST /v1/export` response — pass straight to `client.portability.import_()`. */
export interface ExportBundle {
  schema_version: string;
  exported_at: string;
  namespace: string | null;
  memory_count: number;
  memories: Record<string, unknown>[];
}
