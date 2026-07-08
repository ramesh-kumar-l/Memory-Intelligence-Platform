/** CreateMemory/GetMemory/UpdateMemory/DeleteMemory/Archive/Restore/List —
 * the Phase 1 canonical operations (05-api-design.md).
 */

import type { Transport } from "../http.js";
import type {
  CreateMemoryRequest,
  MemoryObject,
  MemoryRecord,
  MemoryState,
  Page,
  RelationshipsView,
  UpdateMemoryRequest,
  VersionInfo,
} from "../types.js";

export class MemoriesResource {
  constructor(private readonly transport: Transport) {}

  async create(
    request: CreateMemoryRequest,
    options: { idempotencyKey?: string } = {},
  ): Promise<MemoryObject> {
    const headers = options.idempotencyKey
      ? { "Idempotency-Key": options.idempotencyKey }
      : undefined;
    return this.transport.request<MemoryObject>("POST", "/v1/memories", {
      json: request,
      headers,
    });
  }

  async get(memoryId: string, options: { version?: number } = {}): Promise<MemoryObject> {
    return this.transport.request<MemoryObject>("GET", `/v1/memories/${memoryId}`, {
      params: { version: options.version },
    });
  }

  /** Version history (lightweight `VersionInfo` rows, not full Memory
   * Objects — fetch a specific version via `.get(memoryId, { version })`.
   */
  async listVersions(memoryId: string): Promise<VersionInfo[]> {
    const data = await this.transport.request<{ memory_id: string; versions: VersionInfo[] }>(
      "GET",
      `/v1/memories/${memoryId}/versions`,
    );
    return data.versions;
  }

  /** Filtered read of lifecycle-summary records (not full Memory Objects —
   * this is a projection listing, not Search). Fetch a specific memory_id
   * via `.get()` for the full object.
   */
  async list(
    options: {
      namespace?: string;
      state?: MemoryState;
      limit?: number;
      continuationToken?: string;
    } = {},
  ): Promise<Page<MemoryRecord>> {
    return this.transport.request<Page<MemoryRecord>>("GET", "/v1/memories", {
      params: {
        namespace: options.namespace,
        state: options.state,
        limit: options.limit,
        continuation_token: options.continuationToken,
      },
    });
  }

  async update(
    memoryId: string,
    request: UpdateMemoryRequest,
    options: { expectedVersion: number; idempotencyKey?: string },
  ): Promise<MemoryObject> {
    const headers: Record<string, string> = { "If-Match": String(options.expectedVersion) };
    if (options.idempotencyKey) headers["Idempotency-Key"] = options.idempotencyKey;
    return this.transport.request<MemoryObject>("PATCH", `/v1/memories/${memoryId}`, {
      json: request,
      headers,
    });
  }

  async delete(memoryId: string): Promise<Record<string, unknown>> {
    return this.transport.request("DELETE", `/v1/memories/${memoryId}`);
  }

  async archive(memoryId: string): Promise<MemoryObject> {
    return this.transport.request<MemoryObject>("POST", `/v1/memories/${memoryId}/archive`);
  }

  async restore(memoryId: string): Promise<MemoryObject> {
    return this.transport.request<MemoryObject>("POST", `/v1/memories/${memoryId}/restore`);
  }

  /** Graph edges touching this memory, outbound and inbound (Phase 4 task 1,
   * ADR-0006) — a read-only view over the relationship-graph projection.
   */
  async relationships(memoryId: string): Promise<RelationshipsView> {
    return this.transport.request<RelationshipsView>(
      "GET",
      `/v1/memories/${memoryId}/relationships`,
    );
  }
}
