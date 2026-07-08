import { screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { SearchPage } from "../../src/pages/SearchPage";
import { createFakeClient, MEMORY_ID, type FakeClient } from "../fakeClient";
import { renderWithProviders } from "../renderWithProviders";

let fakeClient: FakeClient;
vi.mock("../../src/api/client", () => ({
  getClient: () => fakeClient,
}));

beforeEach(() => {
  fakeClient = createFakeClient();
});

describe("SearchPage", () => {
  it("runs a search and shows results with a score", async () => {
    const user = userEvent.setup();
    renderWithProviders(<SearchPage />);

    await user.type(screen.getByLabelText("Search memories"), "onboarding");
    await user.click(screen.getByRole("button", { name: "Search" }));

    expect(await screen.findByText(MEMORY_ID)).toBeInTheDocument();
    expect(screen.getByText("score 0.8700")).toBeInTheDocument();
    expect(fakeClient.search.search).toHaveBeenCalledWith(
      expect.objectContaining({ query: "onboarding", mode: "hybrid" }),
    );
  });

  it("opens the explain panel for a result", async () => {
    const user = userEvent.setup();
    renderWithProviders(<SearchPage />);
    await user.type(screen.getByLabelText("Search memories"), "onboarding");
    await user.click(screen.getByRole("button", { name: "Search" }));
    await screen.findByText(MEMORY_ID);

    await user.click(screen.getByRole("button", { name: "Why this result?" }));
    expect(await screen.findByText("Why this memory?")).toBeInTheDocument();
  });

  it("shows an empty state for no results", async () => {
    fakeClient.search.search.mockResolvedValue({
      query: "nothing",
      mode: "hybrid",
      items: [],
      complete: true,
      continuation_token: null,
    });
    const user = userEvent.setup();
    renderWithProviders(<SearchPage />);
    await user.type(screen.getByLabelText("Search memories"), "nothing");
    await user.click(screen.getByRole("button", { name: "Search" }));
    expect(await screen.findByText(/No results/)).toBeInTheDocument();
  });

  it("does not search on an empty query", async () => {
    const user = userEvent.setup();
    renderWithProviders(<SearchPage />);
    await user.click(screen.getByRole("button", { name: "Search" }));
    expect(fakeClient.search.search).not.toHaveBeenCalled();
  });
});
