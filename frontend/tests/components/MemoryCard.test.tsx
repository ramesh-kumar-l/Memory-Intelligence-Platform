import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { MemoryCard } from "../../src/components/MemoryCard";

const RECORD = {
  memory_id: "5f8d9a4e-1b2c-4d3e-9f0a-1234567890ab",
  namespace: "demo",
  owner_id: "user-1",
  object_type: "Experience",
  title: "Sample memory",
  state: "Active" as const,
  current_version: 1,
  created_at: "2026-07-08T00:00:00Z",
  updated_at: null,
  archived_at: null,
  deleted_at: null,
  consolidation_count: 0,
};

describe("MemoryCard", () => {
  it("renders the title, type, and state badge", () => {
    render(<MemoryCard record={RECORD} onSelect={() => {}} />);
    expect(screen.getByText("Sample memory")).toBeInTheDocument();
    expect(screen.getByText("Experience")).toBeInTheDocument();
    expect(screen.getByText("Active")).toBeInTheDocument();
  });

  it("calls onSelect with the memory_id when clicked", async () => {
    const onSelect = vi.fn();
    const user = userEvent.setup();
    render(<MemoryCard record={RECORD} onSelect={onSelect} />);
    await user.click(screen.getByRole("button"));
    expect(onSelect).toHaveBeenCalledWith(RECORD.memory_id);
  });

  it("marks the card as current when selected", () => {
    render(<MemoryCard record={RECORD} selected onSelect={() => {}} />);
    expect(screen.getByRole("button")).toHaveAttribute("aria-current", "true");
  });
});
