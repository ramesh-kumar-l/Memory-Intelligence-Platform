import { describe, expect, it } from "vitest";

import { MIPClient } from "../src/client.js";
import { envelope, fakeFetch, jsonResponse } from "./testUtils.js";

describe("AdminResource", () => {
  it("health() returns the ok report", async () => {
    const client = new MIPClient("http://mip.test", {
      fetchImpl: fakeFetch(async () => jsonResponse(envelope({ status: "ok", storage: true }))),
    });
    expect(await client.admin.health()).toEqual({ status: "ok", storage: true });
  });

  it("health() degraded 503 is not raised as an error", async () => {
    const client = new MIPClient("http://mip.test", {
      fetchImpl: fakeFetch(async () =>
        jsonResponse(envelope({ status: "degraded", storage: false }), 503),
      ),
    });
    expect(await client.admin.health()).toEqual({ status: "degraded", storage: false });
  });

  it("version() returns the version report", async () => {
    const client = new MIPClient("http://mip.test", {
      fetchImpl: fakeFetch(async () =>
        jsonResponse(envelope({ service_version: "0.1.0", api_versions: ["1.0"], schema_version: "1.0" })),
      ),
    });
    const info = await client.admin.version();
    expect(info.service_version).toBe("0.1.0");
  });

  it("rebuildProjections() posts to the rebuild endpoint", async () => {
    const client = new MIPClient("http://mip.test", {
      fetchImpl: fakeFetch(async (req) => {
        expect(req.method).toBe("POST");
        expect(new URL(req.url).pathname).toBe("/v1/admin/rebuild-projections");
        return jsonResponse(envelope({ replayed_events: 3, indexed_memories: 1 }));
      }),
    });
    const report = await client.admin.rebuildProjections();
    expect(report.indexed_memories).toBe(1);
  });
});
