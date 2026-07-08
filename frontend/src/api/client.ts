import { MIPClient } from "@mip/sdk";

const STORAGE_KEY = "mip-console:api-base-url";
const API_KEY_STORAGE_KEY = "mip-console:api-key";
const DEFAULT_BASE_URL =
  (import.meta.env.VITE_MIP_API_URL as string | undefined) ?? "http://localhost:8000";

export function getApiBaseUrl(): string {
  if (typeof window === "undefined") return DEFAULT_BASE_URL;
  return window.localStorage.getItem(STORAGE_KEY) ?? DEFAULT_BASE_URL;
}

export function setApiBaseUrl(url: string): void {
  window.localStorage.setItem(STORAGE_KEY, url);
}

/** Only relevant when the backend has `MIP_AUTH_ENABLED=true` (ADR-0007) —
 * left empty, the client behaves exactly as it always has. */
export function getApiKey(): string {
  if (typeof window === "undefined") return "";
  return window.localStorage.getItem(API_KEY_STORAGE_KEY) ?? "";
}

export function setApiKey(key: string): void {
  if (key) window.localStorage.setItem(API_KEY_STORAGE_KEY, key);
  else window.localStorage.removeItem(API_KEY_STORAGE_KEY);
}

let cached: { url: string; apiKey: string; client: MIPClient } | null = null;

/** One MIPClient per (base URL, API key) pair, rebuilt only when either
 * configured value changes (Settings page writes to localStorage; consumers
 * just call getClient()).
 */
export function getClient(): MIPClient {
  const url = getApiBaseUrl();
  const apiKey = getApiKey();
  if (!cached || cached.url !== url || cached.apiKey !== apiKey) {
    cached = { url, apiKey, client: new MIPClient(url, { apiKey: apiKey || undefined }) };
  }
  return cached.client;
}
