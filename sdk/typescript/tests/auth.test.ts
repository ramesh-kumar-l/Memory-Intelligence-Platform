import { describe, expect, it } from "vitest";

import { MIPClient } from "../src/client.js";
import { envelope, fakeFetch, jsonResponse } from "./testUtils.js";

describe("MIPClient auth (ADR-0007)", () => {
  it("sends apiKey as an Authorization Bearer header", async () => {
    const seenHeaders: Headers[] = [];
    const client = new MIPClient("http://mip.test", {
      apiKey: "secret-key",
      fetchImpl: fakeFetch(async (req) => {
        seenHeaders.push(req.headers);
        return jsonResponse(envelope({ status: "ok", storage: true }));
      }),
    });
    await client.admin.health();
    expect(seenHeaders[0]?.get("authorization")).toBe("Bearer secret-key");
  });

  it("omits Authorization when no apiKey is configured", async () => {
    const seenHeaders: Headers[] = [];
    const client = new MIPClient("http://mip.test", {
      fetchImpl: fakeFetch(async (req) => {
        seenHeaders.push(req.headers);
        return jsonResponse(envelope({ status: "ok", storage: true }));
      }),
    });
    await client.admin.health();
    expect(seenHeaders[0]?.has("authorization")).toBe(false);
  });
});
