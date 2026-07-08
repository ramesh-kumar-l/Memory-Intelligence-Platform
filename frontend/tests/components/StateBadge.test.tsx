import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { StateBadge } from "../../src/components/StateBadge";

describe("StateBadge", () => {
  it("renders the state name as visible text, not color alone", () => {
    render(<StateBadge state="Active" />);
    expect(screen.getByText("Active")).toBeInTheDocument();
  });

  it("labels the badge for screen readers", () => {
    render(<StateBadge state="Archived" />);
    expect(screen.getByRole("status", { name: "Lifecycle state: Archived" })).toBeInTheDocument();
  });

  it("applies the danger tone for ValidationFailed", () => {
    render(<StateBadge state="ValidationFailed" />);
    expect(screen.getByText("ValidationFailed")).toHaveClass("state-badge--danger");
  });

  it("applies the ok tone for Active and muted for Archived", () => {
    const { rerender } = render(<StateBadge state="Active" />);
    expect(screen.getByText("Active")).toHaveClass("state-badge--ok");
    rerender(<StateBadge state="Archived" />);
    expect(screen.getByText("Archived")).toHaveClass("state-badge--muted");
  });

  it("pulses transitional states", () => {
    render(<StateBadge state="Validating" />);
    expect(screen.getByText("Validating")).toHaveClass("state-badge--pulse");
  });
});
