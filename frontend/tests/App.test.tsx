import { render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import App from "../src/App";
import { createFakeClient, type FakeClient } from "./fakeClient";

let fakeClient: FakeClient;
vi.mock("../src/api/client", () => ({
  getClient: () => fakeClient,
  getApiBaseUrl: () => "http://localhost:8000",
  setApiBaseUrl: vi.fn(),
}));

beforeEach(() => {
  fakeClient = createFakeClient();
});

describe("App", () => {
  it("redirects the root route to /memories", async () => {
    render(<App />);
    expect(await screen.findByRole("heading", { name: "Memories" })).toBeInTheDocument();
  });
});
