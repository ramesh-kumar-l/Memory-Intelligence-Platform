/**
 * Low-level HTTP transport: envelope unwrapping, error translation. The only
 * module allowed to call `fetch` directly (mirrors the Python SDK's
 * `_http.py` and the backend's "SQL confined to storage/" rule).
 */

import { errorFromEnvelope, MIPConnectionError } from "./errors.js";

export const DEFAULT_API_VERSION = "1.0";

export type FetchLike = (input: string, init?: RequestInit) => Promise<Response>;

export type QueryParams = Record<string, string | number | undefined | null>;

export interface RequestOptions {
  json?: unknown;
  params?: QueryParams | undefined;
  headers?: Record<string, string> | undefined;
}

export interface TransportOptions {
  apiVersion?: string | undefined;
  fetchImpl?: FetchLike | undefined;
  apiKey?: string | undefined;
}

export class Transport {
  private readonly baseUrl: string;
  private readonly apiVersion: string;
  private readonly fetchImpl: FetchLike;
  private readonly apiKey: string | undefined;

  constructor(baseUrl: string, options: TransportOptions = {}) {
    this.baseUrl = baseUrl.replace(/\/$/, "");
    this.apiVersion = options.apiVersion ?? DEFAULT_API_VERSION;
    this.fetchImpl = options.fetchImpl ?? ((input, init) => fetch(input, init));
    this.apiKey = options.apiKey;
  }

  async request<T = unknown>(
    method: string,
    path: string,
    { json, params, headers }: RequestOptions = {},
  ): Promise<T> {
    const url = this.buildUrl(path, params);
    const requestHeaders: Record<string, string> = {
      "MIP-API-Version": this.apiVersion,
      // Sent only when the caller opts in; the server ignores it entirely
      // unless MIP_AUTH_ENABLED=true (ADR-0007).
      ...(this.apiKey !== undefined ? { Authorization: `Bearer ${this.apiKey}` } : {}),
      ...headers,
    };
    const init: RequestInit = { method, headers: requestHeaders };
    if (json !== undefined) {
      requestHeaders["Content-Type"] = "application/json";
      init.body = JSON.stringify(json);
    }

    let response: Response;
    try {
      response = await this.fetchImpl(url, init);
    } catch (cause) {
      throw new MIPConnectionError(`Could not reach MIP API at ${url}`, { cause });
    }

    const text = await response.text();
    const body: unknown = text ? JSON.parse(text) : {};

    // Keyed on the presence of an `error` envelope, not the HTTP status: some
    // endpoints (e.g. /v1/health) legitimately return a non-2xx status with a
    // normal `data` envelope to signal degraded state to infra, not a MEM-* error.
    if (body && typeof body === "object" && "error" in body) {
      throw errorFromEnvelope(body as { error?: object; request_id?: string }, response.status);
    }
    return (body as { data?: T }).data as T;
  }

  private buildUrl(path: string, params: QueryParams | undefined): string {
    const searchParams = new URLSearchParams();
    for (const [key, value] of Object.entries(params ?? {})) {
      if (value !== undefined && value !== null) searchParams.set(key, String(value));
    }
    const query = searchParams.toString();
    return `${this.baseUrl}${path}${query ? `?${query}` : ""}`;
  }
}
