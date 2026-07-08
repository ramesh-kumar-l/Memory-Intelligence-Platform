/** `MIPClient` — the SDK entry point. One client per base URL; resources are
 * thin wrappers sharing a single transport.
 */

import { DEFAULT_API_VERSION, Transport, type FetchLike } from "./http.js";
import { AdminResource } from "./resources/admin.js";
import { MemoriesResource } from "./resources/memories.js";
import { ContextResource, ExplainResource, SearchResource } from "./resources/retrieval.js";

export interface MIPClientOptions {
  apiVersion?: string | undefined;
  fetchImpl?: FetchLike | undefined;
}

/**
 * Client for the MIP REST API.
 *
 * @example
 * const client = new MIPClient("http://localhost:8000");
 * const result = await client.search.search({ query: "onboarding" });
 */
export class MIPClient {
  readonly memories: MemoriesResource;
  readonly search: SearchResource;
  readonly explain: ExplainResource;
  readonly context: ContextResource;
  readonly admin: AdminResource;

  constructor(baseUrl: string, options: MIPClientOptions = {}) {
    const transport = new Transport(baseUrl, {
      apiVersion: options.apiVersion ?? DEFAULT_API_VERSION,
      fetchImpl: options.fetchImpl,
    });
    this.memories = new MemoriesResource(transport);
    this.search = new SearchResource(transport);
    this.explain = new ExplainResource(transport);
    this.context = new ContextResource(transport);
    this.admin = new AdminResource(transport);
  }
}
