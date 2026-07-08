import { screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import * as apiClient from "../../src/api/client";
import { SettingsPage } from "../../src/pages/SettingsPage";
import { createFakeClient, type FakeClient } from "../fakeClient";
import { renderWithProviders } from "../renderWithProviders";

let fakeClient: FakeClient;
vi.mock("../../src/api/client", () => ({
  getClient: () => fakeClient,
  getApiBaseUrl: () => "http://localhost:8000",
  setApiBaseUrl: vi.fn(),
  getApiKey: () => "",
  setApiKey: vi.fn(),
}));

beforeEach(() => {
  fakeClient = createFakeClient();
});

describe("SettingsPage", () => {
  it("checks the connection and shows the health status", async () => {
    const user = userEvent.setup();
    renderWithProviders(<SettingsPage />);
    await user.click(screen.getByRole("button", { name: /Save & test connection/ }));
    expect(await screen.findAllByText("ok")).toHaveLength(2);
  });

  it("shows an error state when the health check fails", async () => {
    fakeClient.admin.health.mockRejectedValue(new Error("could not connect"));
    const user = userEvent.setup();
    renderWithProviders(<SettingsPage />);
    await user.click(screen.getByRole("button", { name: /Save & test connection/ }));
    expect(await screen.findByText("could not connect")).toBeInTheDocument();
  });

  it("saves the API key on submit (ADR-0007)", async () => {
    const user = userEvent.setup();
    renderWithProviders(<SettingsPage />);
    await user.type(screen.getByLabelText(/API key/), "secret-key");
    await user.click(screen.getByRole("button", { name: /Save & test connection/ }));
    expect(apiClient.setApiKey).toHaveBeenCalledWith("secret-key");
  });
});
