import { describe, expect, it } from "vitest";

import { MIPClient } from "../src/client.js";
import {
  ConcurrencyError,
  IdentityError,
  LifecycleError,
  MIPAPIError,
  MIPConnectionError,
  SecurityError,
  StorageError,
  SyncError,
  TrustError,
  ValidationError,
} from "../src/errors.js";
import { errorEnvelope, fakeFetch, jsonResponse } from "./testUtils.js";

const CATEGORY_CASES: Array<[string, new (...args: never[]) => MIPAPIError]> = [
  ["Validation", ValidationError],
  ["Lifecycle", LifecycleError],
  ["Identity", IdentityError],
  ["Concurrency", ConcurrencyError],
  ["Trust", TrustError],
  ["Storage", StorageError],
  ["Sync", SyncError],
  ["Security", SecurityError],
];

describe("error mapping", () => {
  it.each(CATEGORY_CASES)("category %s maps to a typed exception", async (category, expectedCls) => {
    const client = new MIPClient("http://mip.test", {
      fetchImpl: fakeFetch(async () =>
        jsonResponse(errorEnvelope({ category, code: "MEM-9999" }), 409),
      ),
    });

    try {
      await client.admin.health();
      expect.unreachable("expected an error to be thrown");
    } catch (err) {
      expect(err).toBeInstanceOf(expectedCls);
      expect((err as MIPAPIError).code).toBe("MEM-9999");
      expect((err as MIPAPIError).category).toBe(category);
      expect((err as MIPAPIError).httpStatus).toBe(409);
    }
  });

  it("unknown category falls back to the base error", async () => {
    const client = new MIPClient("http://mip.test", {
      fetchImpl: fakeFetch(async () =>
        jsonResponse(errorEnvelope({ category: "SomethingNew", code: "MEM-0001" }), 500),
      ),
    });

    try {
      await client.admin.health();
      expect.unreachable("expected an error to be thrown");
    } catch (err) {
      expect(Object.getPrototypeOf(err)).toBe(MIPAPIError.prototype);
      expect((err as MIPAPIError).code).toBe("MEM-0001");
    }
  });

  it("preserves recoverable flag and details", async () => {
    const client = new MIPClient("http://mip.test", {
      fetchImpl: fakeFetch(async () =>
        jsonResponse(
          errorEnvelope({
            category: "Concurrency",
            code: "MEM-4001",
            recoverable: true,
            details: { expected: 1, actual: 2 },
          }),
          409,
        ),
      ),
    });

    try {
      await client.admin.health();
      expect.unreachable("expected an error to be thrown");
    } catch (err) {
      expect((err as ConcurrencyError).recoverable).toBe(true);
      expect((err as ConcurrencyError).details).toEqual({ expected: 1, actual: 2 });
    }
  });

  it("raises MIPConnectionError when the network call itself fails", async () => {
    const client = new MIPClient("http://mip.test", {
      fetchImpl: async () => {
        throw new TypeError("network down");
      },
    });

    await expect(client.admin.health()).rejects.toBeInstanceOf(MIPConnectionError);
  });
});
