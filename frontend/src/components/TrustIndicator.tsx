import "./TrustIndicator.css";

export interface TrustIndicatorProps {
  confidence: number;
  verificationStatus?: string;
  sourceCount?: number;
  onExplain?: () => void;
}

/** Confidence as a labeled numeric + 5-segment bar (never color alone).
 * The "Why?" affordance opens the ExplainPanel for this memory.
 */
export function TrustIndicator({
  confidence,
  verificationStatus,
  sourceCount,
  onExplain,
}: TrustIndicatorProps) {
  const filled = Math.round(confidence * 5);
  const parts = [`Confidence ${confidence.toFixed(2)}`];
  if (sourceCount !== undefined) parts.push(`${sourceCount} source${sourceCount === 1 ? "" : "s"}`);
  if (verificationStatus) parts.push(verificationStatus.toLowerCase());
  const label = parts.join(", ");

  return (
    <div className="trust-indicator" role="group" aria-label={label} title={label}>
      <span className="trust-indicator__value mono">{confidence.toFixed(2)}</span>
      <span className="trust-indicator__bar" aria-hidden="true">
        {Array.from({ length: 5 }, (_, index) => (
          <span
            key={index}
            className={`trust-indicator__segment${
              index < filled ? " trust-indicator__segment--filled" : ""
            }`}
          />
        ))}
      </span>
      {onExplain ? (
        <button type="button" className="trust-indicator__why" onClick={onExplain}>
          Why?
        </button>
      ) : null}
    </div>
  );
}
