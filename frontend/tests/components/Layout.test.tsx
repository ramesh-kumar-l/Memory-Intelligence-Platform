import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { describe, expect, it } from "vitest";

import { Layout } from "../../src/components/Layout";

function renderLayout() {
  return render(
    <MemoryRouter initialEntries={["/memories"]}>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route path="memories" element={<div>Memories content</div>} />
        </Route>
      </Routes>
    </MemoryRouter>,
  );
}

describe("Layout", () => {
  it("renders the primary nav", () => {
    renderLayout();
    expect(screen.getByRole("link", { name: "Memories" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Search" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Settings" })).toBeInTheDocument();
  });

  it("renders the routed outlet content", () => {
    renderLayout();
    expect(screen.getByText("Memories content")).toBeInTheDocument();
  });

  it("toggles the data-theme attribute on the root element", async () => {
    const user = userEvent.setup();
    renderLayout();
    await user.selectOptions(screen.getByLabelText("Theme"), "dark");
    expect(document.documentElement.getAttribute("data-theme")).toBe("dark");
    await user.selectOptions(screen.getByLabelText("Theme"), "system");
    expect(document.documentElement.hasAttribute("data-theme")).toBe(false);
  });
});
