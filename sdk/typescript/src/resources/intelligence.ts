/** Consolidate + Learn — Phase 4 tasks 2/3 (ADR-0006). */

import type { Transport } from "../http.js";
import type { ConsolidateRequestBody, LearnRequestBody, MemoryObject } from "../types.js";

export class ConsolidateResource {
  constructor(private readonly transport: Transport) {}

  async consolidate(request: ConsolidateRequestBody): Promise<MemoryObject> {
    return this.transport.request<MemoryObject>("POST", "/v1/consolidate", { json: request });
  }
}

export class LearnResource {
  constructor(private readonly transport: Transport) {}

  async learn(
    request: LearnRequestBody,
    options: { idempotencyKey?: string } = {},
  ): Promise<MemoryObject> {
    const headers = options.idempotencyKey
      ? { "Idempotency-Key": options.idempotencyKey }
      : undefined;
    return this.transport.request<MemoryObject>("POST", "/v1/learn", { json: request, headers });
  }
}
