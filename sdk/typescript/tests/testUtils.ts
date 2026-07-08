import type { FetchLike } from "../src/http.js";

export interface FakeRequest {
  method: string;
  url: string;
  headers: Headers;
  body: string | null;
}

export type Handler = (request: FakeRequest) => Response | Promise<Response>;

export function fakeFetch(handler: Handler): FetchLike {
  return async (input, init) => {
    const method = init?.method ?? "GET";
    const headers = new Headers(init?.headers);
    const body = typeof init?.body === "string" ? init.body : null;
    return handler({ method, url: String(input), headers, body });
  };
}

export function jsonResponse(data: unknown, status = 200): Response {
  return new Response(JSON.stringify(data), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

export function envelope(data: unknown, requestId = "req-1"): Record<string, unknown> {
  return { data, request_id: requestId, schema_version: "1.0", processing_time_ms: 1.23 };
}

export function errorEnvelope(options: {
  code?: string;
  category?: string;
  message?: string;
  details?: Record<string, unknown>;
  recoverable?: boolean;
  requestId?: string;
}): Record<string, unknown> {
  return {
    error: {
      code: options.code ?? "MEM-2001",
      category: options.category ?? "Lifecycle",
      message: options.message ?? "Illegal lifecycle transition",
      details: options.details ?? {},
      recoverable: options.recoverable ?? false,
      documentation_url: `https://example.invalid/errors#${options.code ?? "MEM-2001"}`,
    },
    request_id: options.requestId ?? "req-err",
  };
}
