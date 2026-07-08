/** Search / Explain / BuildContext — the Phase 2 canonical operations
 * (05-api-design.md). Three small resources in one module.
 */

import type { Transport } from "../http.js";
import type {
  ContextPackage,
  ContextRequestBody,
  Explanation,
  ExplainRequestBody,
  SearchRequestBody,
  SearchResponse,
} from "../types.js";

export class SearchResource {
  constructor(private readonly transport: Transport) {}

  async search(request: SearchRequestBody): Promise<SearchResponse> {
    return this.transport.request<SearchResponse>("POST", "/v1/search", { json: request });
  }
}

export class ExplainResource {
  constructor(private readonly transport: Transport) {}

  async explain(request: ExplainRequestBody): Promise<Explanation> {
    return this.transport.request<Explanation>("POST", "/v1/explain", { json: request });
  }
}

export class ContextResource {
  constructor(private readonly transport: Transport) {}

  async build(request: ContextRequestBody): Promise<ContextPackage> {
    return this.transport.request<ContextPackage>("POST", "/v1/context", { json: request });
  }
}
