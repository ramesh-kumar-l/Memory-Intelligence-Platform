import { MIPConnectionError, ValidationError } from "@mip/sdk";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { ErrorState } from "../../src/components/ErrorState";

describe("ErrorState", () => {
  it("shows the MEM-* code and message for a typed API error", () => {
    const error = new ValidationError(
      {
        code: "MEM-1007",
        category: "Validation",
        message: "Requested search mode is not supported",
        details: {},
        recoverable: false,
        documentation_url: "https://example.invalid/errors#MEM-1007",
      },
      400,
      "req-1",
    );
    render(<ErrorState error={error} />);
    expect(screen.getByText("MEM-1007")).toBeInTheDocument();
    expect(screen.getByText("Requested search mode is not supported")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Learn more" })).toHaveAttribute(
      "href",
      "https://example.invalid/errors#MEM-1007",
    );
  });

  it("shows a friendly message for a connection error", () => {
    render(<ErrorState error={new MIPConnectionError("could not connect")} />);
    expect(screen.getByText(/Could not reach the MIP API/)).toBeInTheDocument();
  });

  it("calls onRetry when the Retry button is clicked", async () => {
    const onRetry = vi.fn();
    const user = userEvent.setup();
    render(<ErrorState error={new Error("boom")} onRetry={onRetry} />);
    await user.click(screen.getByRole("button", { name: "Retry" }));
    expect(onRetry).toHaveBeenCalledOnce();
  });

  it("does not misclassify an unrelated error type as a MIPAPIError", () => {
    render(<ErrorState error={new Error("plain error")} />);
    expect(screen.getByText("plain error")).toBeInTheDocument();
    expect(screen.queryByText(/^MEM-/)).not.toBeInTheDocument();
  });
});
