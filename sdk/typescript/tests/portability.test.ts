import { describe, expect, it } from "vitest";

import { MIPClient } from "../src/client.js";
import type { ExportBundle } from "../src/types.js";
import { envelope, fakeFetch, jsonResponse } from "./testUtils.js";

function bundle(): ExportBundle {
  return {
    schema_version: "1.0",
    exported_at: "2026-07-08T00:00:00Z",
    namespace: "demo",
    memory_count: 0,
    memories: [],
  };
}

describe("PortabilityResource", () => {
  it("export() returns a typed bundle", async () => {
    const client = new MIPClient("http://mip.test", {
      fetchImpl: fakeFetch(async (req) => {
        expect(req.url).toBe("http://mip.test/v1/export");
        return jsonResponse(envelope(bundle()));
      }),
    });

    const result = await client.portability.export({ namespace: "demo" });
    expect(result.namespace).toBe("demo");
    expect(result.memory_count).toBe(0);
  });

  it("import_() posts the bundle and returns a typed report", async () => {
    const client = new MIPClient("http://mip.test", {
      fetchImpl: fakeFetch(async (req) => {
        if (req.url === "http://mip.test/v1/export") {
          return jsonResponse(envelope(bundle()));
        }
        expect(req.url).toBe("http://mip.test/v1/import");
        return jsonResponse(envelope({ imported: [], skipped: [], rejected: [] }));
      }),
    });

    const exported = await client.portability.export({});
    const report = await client.portability.import_(exported);
    expect(report.imported).toEqual([]);
    expect(report.skipped).toEqual([]);
    expect(report.rejected).toEqual([]);
  });
});
