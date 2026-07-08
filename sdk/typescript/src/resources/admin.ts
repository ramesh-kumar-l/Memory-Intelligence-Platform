/** Health, version negotiation info, and projection rebuild (operational ops). */

import type { Transport } from "../http.js";

export interface HealthReport {
  status: string;
  storage: boolean;
}

export interface VersionReport {
  service_version: string;
  api_versions: string[];
  schema_version: string;
}

export class AdminResource {
  constructor(private readonly transport: Transport) {}

  async health(): Promise<HealthReport> {
    return this.transport.request<HealthReport>("GET", "/v1/health");
  }

  async version(): Promise<VersionReport> {
    return this.transport.request<VersionReport>("GET", "/v1/version");
  }

  async rebuildProjections(): Promise<Record<string, unknown>> {
    return this.transport.request("POST", "/v1/admin/rebuild-projections");
  }
}
