/** Official TypeScript SDK for the Memory Intelligence Platform (MIP) REST
 * API. Thin typed client over `/v1` (05-api-design.md, FR-API-001) — no
 * engine or storage logic lives here; every call is a plain HTTP request.
 */

export { MIPClient, type MIPClientOptions } from "./client.js";
export {
  ConcurrencyError,
  errorFromEnvelope,
  IdentityError,
  LifecycleError,
  MIPAPIError,
  MIPConnectionError,
  SecurityError,
  StorageError,
  SyncError,
  TrustError,
  ValidationError,
  type ErrorEnvelope,
} from "./errors.js";
export type { FetchLike } from "./http.js";
export { AdminResource, type HealthReport, type VersionReport } from "./resources/admin.js";
export { ConsolidateResource, LearnResource } from "./resources/intelligence.js";
export { MemoriesResource } from "./resources/memories.js";
export { PortabilityResource } from "./resources/portability.js";
export { ContextResource, ExplainResource, SearchResource } from "./resources/retrieval.js";
export * from "./types.js";

export const VERSION = "0.1.0";
