/** Export/Import — Phase 4 task 4 (ADR-0006). */

import type { Transport } from "../http.js";
import type { ExportBundle, ExportRequestBody, ImportReport } from "../types.js";

export class PortabilityResource {
  constructor(private readonly transport: Transport) {}

  async export(request: ExportRequestBody = {}): Promise<ExportBundle> {
    return this.transport.request<ExportBundle>("POST", "/v1/export", { json: request });
  }

  /** Named `import_` — `import` is a reserved word in JavaScript/TypeScript. */
  async import_(bundle: ExportBundle | Record<string, unknown>): Promise<ImportReport> {
    return this.transport.request<ImportReport>("POST", "/v1/import", { json: bundle });
  }
}
