/** Spawns the real backend (uvicorn) against a temp SQLite DB, for the
 * cross-language integration check in liveServer.test.ts. Node can't import
 * Python in-process the way the Python SDK's tests use ASGITransport/
 * TestClient, so this is the equivalent: a real HTTP server, real process.
 */

import { type ChildProcess, spawn } from "node:child_process";
import { mkdtemp, rm } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";

const BACKEND_ROOT = join(import.meta.dirname, "..", "..", "..", "backend");
const UVICORN =
  process.platform === "win32"
    ? join(BACKEND_ROOT, ".venv", "Scripts", "uvicorn.exe")
    : join(BACKEND_ROOT, ".venv", "bin", "uvicorn");

export interface LiveServer {
  baseUrl: string;
  stop: () => Promise<void>;
}

async function waitForHealth(baseUrl: string, timeoutMs: number): Promise<void> {
  const deadline = Date.now() + timeoutMs;
  while (Date.now() < deadline) {
    try {
      const response = await fetch(`${baseUrl}/v1/health`);
      if (response.ok || response.status === 503) return;
    } catch {
      // server not accepting connections yet — retry
    }
    await new Promise((resolve) => setTimeout(resolve, 100));
  }
  throw new Error(`Backend did not become healthy within ${timeoutMs}ms`);
}

export async function startLiveServer(port: number): Promise<LiveServer> {
  const dbDir = await mkdtemp(join(tmpdir(), "mip-ts-sdk-"));
  const dbPath = join(dbDir, "mip.db");

  const child: ChildProcess = spawn(
    UVICORN,
    ["mip.api.app:create_app", "--factory", "--host", "127.0.0.1", "--port", String(port)],
    {
      cwd: BACKEND_ROOT,
      env: { ...process.env, MIP_DB_PATH: dbPath },
      stdio: "ignore",
    },
  );

  const baseUrl = `http://127.0.0.1:${port}`;
  try {
    await waitForHealth(baseUrl, 15_000);
  } catch (err) {
    child.kill();
    await rm(dbDir, { recursive: true, force: true });
    throw err;
  }

  return {
    baseUrl,
    stop: async () => {
      await new Promise<void>((resolve) => {
        child.once("exit", () => resolve());
        child.kill();
        setTimeout(resolve, 3_000);
      });
      // Windows can hold the SQLite file/WAL handles briefly after the
      // process exits; retry the directory removal instead of racing it.
      await rm(dbDir, { recursive: true, force: true, maxRetries: 5, retryDelay: 250 });
    },
  };
}
