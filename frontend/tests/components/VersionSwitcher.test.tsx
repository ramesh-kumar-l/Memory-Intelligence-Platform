import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { VersionSwitcher } from "../../src/components/VersionSwitcher";

const VERSIONS = [
  { version: 1, previous_version: null, created_at: "2026-07-01T00:00:00Z" },
  { version: 2, previous_version: 1, created_at: "2026-07-02T00:00:00Z" },
];

describe("VersionSwitcher", () => {
  it("marks the current version in its label", () => {
    render(
      <VersionSwitcher versions={VERSIONS} selectedVersion={2} currentVersion={2} onChange={() => {}} />,
    );
    expect(screen.getByRole("option", { name: "v2 (current)" })).toBeInTheDocument();
  });

  it("shows the immutable watermark only for a non-current selection", () => {
    render(
      <VersionSwitcher versions={VERSIONS} selectedVersion={1} currentVersion={2} onChange={() => {}} />,
    );
    expect(screen.getByText("immutable historical version")).toBeInTheDocument();
  });

  it("does not show the watermark for the current version", () => {
    render(
      <VersionSwitcher versions={VERSIONS} selectedVersion={2} currentVersion={2} onChange={() => {}} />,
    );
    expect(screen.queryByText("immutable historical version")).not.toBeInTheDocument();
  });

  it("calls onChange when a different version is selected", async () => {
    const onChange = vi.fn();
    const user = userEvent.setup();
    render(
      <VersionSwitcher versions={VERSIONS} selectedVersion={2} currentVersion={2} onChange={onChange} />,
    );
    await user.selectOptions(screen.getByLabelText("Version"), "1");
    expect(onChange).toHaveBeenCalledWith(1);
  });
});
