import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { ExplainPanel } from "../../src/components/ExplainPanel";

describe("ExplainPanel", () => {
  it("renders confidence, freshness, verification, and source count", () => {
    render(
      <ExplainPanel
        explanation={{
          memory_id: "m1",
          confidence: 0.8,
          freshness: 0.95,
          verification_status: "Verified",
          source_count: 2,
          provenance: { source: "test" },
          evidence: [],
          ranking: null,
        }}
      />,
    );
    expect(screen.getByText("0.80")).toBeInTheDocument();
    expect(screen.getByText("0.95")).toBeInTheDocument();
    expect(screen.getByText("Verified")).toBeInTheDocument();
  });

  it("renders a matched ranking breakdown", () => {
    render(
      <ExplainPanel
        explanation={{
          memory_id: "m1",
          confidence: 0.8,
          freshness: 0.95,
          verification_status: "Verified",
          source_count: 2,
          provenance: { source: "test" },
          evidence: [],
          ranking: { mode: "hybrid", score: 0.87, keyword_score: 0.9, semantic_score: 0.8, matched: true },
        }}
      />,
    );
    expect(screen.getByText("Score: 0.8700")).toBeInTheDocument();
  });

  it("renders a not-matched ranking explanation", () => {
    render(
      <ExplainPanel
        explanation={{
          memory_id: "m1",
          confidence: 0.8,
          freshness: 0.95,
          verification_status: "Verified",
          source_count: 2,
          provenance: { source: "test" },
          evidence: [],
          ranking: { mode: "hybrid", score: 0, keyword_score: null, semantic_score: null, matched: false },
        }}
      />,
    );
    expect(screen.getByText("Did not match this query within the ranking window.")).toBeInTheDocument();
  });
});
