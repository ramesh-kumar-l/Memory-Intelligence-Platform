import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { MemoriesPage } from "../../src/pages/MemoriesPage";
import { createFakeClient, MEMORY_ID, type FakeClient } from "../fakeClient";
import { renderWithProviders } from "../renderWithProviders";

let fakeClient: FakeClient;
vi.mock("../../src/api/client", () => ({
  getClient: () => fakeClient,
}));

beforeEach(() => {
  fakeClient = createFakeClient();
});

describe("MemoriesPage", () => {
  it("shows the list and lets the user select a memory to see its detail", async () => {
    const user = userEvent.setup();
    renderWithProviders(<MemoriesPage />);

    expect(await screen.findByText("Sample memory")).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: /Sample memory/ }));

    await waitFor(() => expect(fakeClient.memories.get).toHaveBeenCalledWith(MEMORY_ID, { version: undefined }));
    expect(await screen.findByRole("tab", { name: "Trust" })).toBeInTheDocument();
  });

  it("shows an empty state when there are no memories", async () => {
    fakeClient.memories.list.mockResolvedValue({ items: [], complete: true, continuation_token: null });
    renderWithProviders(<MemoriesPage />);
    expect(await screen.findByText("No memories yet")).toBeInTheDocument();
  });

  it("shows an error state when the list request fails", async () => {
    fakeClient.memories.list.mockRejectedValue(new Error("network down"));
    renderWithProviders(<MemoriesPage />);
    expect(await screen.findByText("network down")).toBeInTheDocument();
  });

  it("filters by namespace", async () => {
    const user = userEvent.setup();
    renderWithProviders(<MemoriesPage />);
    await screen.findByText("Sample memory");
    await user.type(screen.getByLabelText("Namespace"), "team-a");
    await waitFor(() =>
      expect(fakeClient.memories.list).toHaveBeenLastCalledWith(
        expect.objectContaining({ namespace: "team-a" }),
      ),
    );
  });

  it("closes the detail pane on Escape", async () => {
    const user = userEvent.setup();
    renderWithProviders(<MemoriesPage />);
    await user.click(await screen.findByRole("button", { name: /Sample memory/ }));
    await screen.findByRole("tab", { name: "Trust" });
    await user.keyboard("{Escape}");
    await waitFor(() => expect(screen.queryByRole("tab", { name: "Trust" })).not.toBeInTheDocument());
  });
});
