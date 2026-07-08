import "@testing-library/jest-dom/vitest";

import { cleanup } from "@testing-library/react";
import { afterEach } from "vitest";

// vitest.config.ts does not set `test.globals: true`, so RTL's own automatic
// cleanup registration (which depends on a global `afterEach`) never fires —
// register it explicitly or DOM nodes accumulate across tests in a file.
afterEach(() => {
  cleanup();
});
