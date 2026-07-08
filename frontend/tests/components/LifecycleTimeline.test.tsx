import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { LifecycleTimeline } from "../../src/components/LifecycleTimeline";

describe("LifecycleTimeline", () => {
  it("renders versions newest first", () => {
    render(
      <LifecycleTimeline
        versions={[
          { version: 1, previous_version: null, created_at: "2026-07-01T00:00:00Z" },
          { version: 2, previous_version: 1, created_at: "2026-07-02T00:00:00Z" },
        ]}
      />,
    );
    const items = screen.getAllByRole("listitem");
    expect(items[0]).toHaveTextContent("v2");
    expect(items[1]).toHaveTextContent("v1");
  });

  it("labels the initial version distinctly from a derived one", () => {
    render(
      <LifecycleTimeline
        versions={[{ version: 1, previous_version: null, created_at: "2026-07-01T00:00:00Z" }]}
      />,
    );
    expect(screen.getByText("initial version")).toBeInTheDocument();
  });
});
