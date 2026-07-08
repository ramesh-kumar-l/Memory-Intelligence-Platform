import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { EmptyState } from "../../src/components/EmptyState";

describe("EmptyState", () => {
  it("renders the title and optional description", () => {
    render(<EmptyState title="No memories yet" description="Create one to see it here." />);
    expect(screen.getByText("No memories yet")).toBeInTheDocument();
    expect(screen.getByText("Create one to see it here.")).toBeInTheDocument();
  });

  it("renders without a description", () => {
    render(<EmptyState title="No results" />);
    expect(screen.getByText("No results")).toBeInTheDocument();
  });
});
