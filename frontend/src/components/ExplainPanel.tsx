import type { Explanation } from "@mip/sdk";

import "./ExplainPanel.css";

export interface ExplainPanelProps {
  explanation: Explanation;
}

/** The signature explainability component — a direct render of `/v1/explain`:
 * why retrieved, evidence, confidence, freshness, provenance chain.
 */
export function ExplainPanel({ explanation }: ExplainPanelProps) {
  return (
    <section className="explain-panel" aria-label="Explanation">
      <h3>Why this memory?</h3>
      <dl className="explain-panel__grid">
        <dt>Confidence</dt>
        <dd className="mono">{explanation.confidence.toFixed(2)}</dd>
        <dt>Freshness</dt>
        <dd className="mono">{explanation.freshness.toFixed(2)}</dd>
        <dt>Verification</dt>
        <dd>{explanation.verification_status}</dd>
        <dt>Sources</dt>
        <dd>{explanation.source_count}</dd>
      </dl>

      {explanation.ranking ? (
        <div className="explain-panel__section">
          <h4>Ranking ({explanation.ranking.mode})</h4>
          {explanation.ranking.matched ? (
            <>
              <p>Score: {explanation.ranking.score.toFixed(4)}</p>
              {explanation.ranking.keyword_score != null && (
                <p>Keyword score: {explanation.ranking.keyword_score.toFixed(4)}</p>
              )}
              {explanation.ranking.semantic_score != null && (
                <p>Semantic score: {explanation.ranking.semantic_score.toFixed(4)}</p>
              )}
            </>
          ) : (
            <p>Did not match this query within the ranking window.</p>
          )}
        </div>
      ) : null}

      <div className="explain-panel__section">
        <h4>Provenance</h4>
        <pre className="mono explain-panel__pre">{JSON.stringify(explanation.provenance, null, 2)}</pre>
      </div>

      {explanation.evidence.length > 0 ? (
        <div className="explain-panel__section">
          <h4>Evidence ({explanation.evidence.length})</h4>
          <ul>
            {explanation.evidence.map((item, index) => (
              <li key={index}>
                <pre className="mono explain-panel__pre">{JSON.stringify(item)}</pre>
              </li>
            ))}
          </ul>
        </div>
      ) : null}
    </section>
  );
}
