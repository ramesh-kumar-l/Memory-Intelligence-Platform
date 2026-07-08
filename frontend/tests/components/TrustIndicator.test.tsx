import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { TrustIndicator } from "../../src/components/TrustIndicator";

describe("TrustIndicator", () => {
  it("shows the confidence value as text, not color alone", () => {
    render(<TrustIndicator confidence={0.82} />);
    expect(screen.getByText("0.82")).toBeInTheDocument();
  });

  it("builds an accessible label with sources and verification status", () => {
    render(<TrustIndicator confidence={0.82} sourceCount={3} verificationStatus="Verified" />);
    expect(
      screen.getByRole("group", { name: "Confidence 0.82, 3 sources, verified" }),
    ).toBeInTheDocument();
  });

  it("calls onExplain when Why? is clicked", async () => {
    const onExplain = vi.fn();
    const user = userEvent.setup();
    render(<TrustIndicator confidence={0.5} onExplain={onExplain} />);
    await user.click(screen.getByRole("button", { name: "Why?" }));
    expect(onExplain).toHaveBeenCalledOnce();
  });

  it("omits the Why? button when onExplain is not provided", () => {
    render(<TrustIndicator confidence={0.5} />);
    expect(screen.queryByRole("button", { name: "Why?" })).not.toBeInTheDocument();
  });
});
