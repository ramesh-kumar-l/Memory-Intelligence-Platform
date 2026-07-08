import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { SearchBar } from "../../src/components/SearchBar";

function renderBar(overrides: Partial<React.ComponentProps<typeof SearchBar>> = {}) {
  const props = {
    query: "",
    mode: "hybrid" as const,
    namespace: "",
    onQueryChange: vi.fn(),
    onModeChange: vi.fn(),
    onNamespaceChange: vi.fn(),
    onSubmit: vi.fn(),
    ...overrides,
  };
  render(<SearchBar {...props} />);
  return props;
}

describe("SearchBar", () => {
  it("submits the current query on Enter / button click", async () => {
    const user = userEvent.setup();
    const props = renderBar({ query: "onboarding" });
    await user.click(screen.getByRole("button", { name: "Search" }));
    expect(props.onSubmit).toHaveBeenCalledOnce();
  });

  it("pressing / focuses the query input when nothing else has focus", async () => {
    const user = userEvent.setup();
    renderBar();
    const input = screen.getByPlaceholderText(/Search memories/);
    expect(input).not.toHaveFocus();
    await user.keyboard("/");
    expect(input).toHaveFocus();
  });

  it("does not steal focus from another text field when / is typed there", async () => {
    const user = userEvent.setup();
    renderBar();
    const namespaceInput = screen.getByLabelText("Namespace filter");
    await user.click(namespaceInput);
    await user.keyboard("/");
    expect(namespaceInput).toHaveFocus();
  });
});
