import { MIPClient } from "@mip/sdk";

const STORAGE_KEY = "mip-console:api-base-url";
const DEFAULT_BASE_URL =
  (import.meta.env.VITE_MIP_API_URL as string | undefined) ?? "http://localhost:8000";

export function getApiBaseUrl(): string {
  if (typeof window === "undefined") return DEFAULT_BASE_URL;
  return window.localStorage.getItem(STORAGE_KEY) ?? DEFAULT_BASE_URL;
}

export function setApiBaseUrl(url: string): void {
  window.localStorage.setItem(STORAGE_KEY, url);
}

let cached: { url: string; client: MIPClient } | null = null;

/** One MIPClient per base URL, rebuilt only when the configured URL changes
 * (Settings page writes to localStorage; consumers just call getClient()).
 */
export function getClient(): MIPClient {
  const url = getApiBaseUrl();
  if (!cached || cached.url !== url) {
    cached = { url, client: new MIPClient(url) };
  }
  return cached.client;
}
