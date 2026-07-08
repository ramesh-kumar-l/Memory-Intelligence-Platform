import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { IntelligencePage } from "../../src/pages/IntelligencePage";
import { createFakeClient, type FakeClient } from "../fakeClient";
import { renderWithProviders } from "../renderWithProviders";

let fakeClient: FakeClient;
vi.mock("../../src/api/client", () => ({
  getClient: () => fakeClient,
}));

beforeEach(() => {
  fakeClient = createFakeClient();
});

describe("IntelligencePage", () => {
  it("consolidates a primary and duplicate ids", async () => {
    const user = userEvent.setup();
    renderWithProviders(<IntelligencePage />);

    await user.type(screen.getByLabelText("Primary memory ID"), "primary-1");
    await user.type(screen.getByLabelText("Duplicate memory IDs (comma-separated)"), "dup-1, dup-2");
    await user.click(screen.getByRole("button", { name: "Merge" }));

    await waitFor(() =>
      expect(fakeClient.consolidate.consolidate).toHaveBeenCalledWith({
        primary_memory_id: "primary-1",
        duplicate_memory_ids: ["dup-1", "dup-2"],
      }),
    );
    expect(await screen.findByText(/consolidation_count = 1/)).toBeInTheDocument();
  });

  it("learns derived concepts for a memory", async () => {
    const user = userEvent.setup();
    renderWithProviders(<IntelligencePage />);

    await user.type(screen.getByLabelText("Memory ID"), "memory-1");
    await user.type(screen.getByLabelText("Derived concepts (comma-separated)"), "durability");
    await user.type(screen.getByLabelText("Reason"), "pattern observed");
    await user.click(screen.getByRole("button", { name: "Learn" }));

    await waitFor(() =>
      expect(fakeClient.learn.learn).toHaveBeenCalledWith({
        memory_id: "memory-1",
        derived: { concepts: ["durability"] },
        reason: "pattern observed",
      }),
    );
    expect(await screen.findByText(/Concepts: durability/)).toBeInTheDocument();
  });

  it("exports a namespace bundle", async () => {
    const user = userEvent.setup();
    renderWithProviders(<IntelligencePage />);

    await user.type(screen.getByLabelText("Namespace (optional)"), "demo");
    await user.click(screen.getByRole("button", { name: "Export & download" }));

    await waitFor(() => expect(fakeClient.portability.export).toHaveBeenCalledWith({ namespace: "demo" }));
    expect(await screen.findByText(/Exported 1 memories/)).toBeInTheDocument();
  });
});
