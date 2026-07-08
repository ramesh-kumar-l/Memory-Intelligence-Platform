import type { MemoryState } from "@mip/sdk";

import "./StateBadge.css";

const TRANSITIONAL: ReadonlySet<MemoryState> = new Set([
  "Created",
  "Validating",
  "Enriching",
  "Indexed",
  "GraphLinked",
  "Updating",
]);

type Tone = "ok" | "muted" | "danger" | "warn";

function toneFor(state: MemoryState): Tone {
  if (state === "Active") return "ok";
  if (state === "Archived" || state === "Deleted") return "muted";
  if (state === "ValidationFailed") return "danger";
  return "warn";
}

export interface StateBadgeProps {
  state: MemoryState;
}

/** Lifecycle state pill (18-ui-design-system.md). Color is never the sole
 * signal — the state name is always rendered as text too.
 */
export function StateBadge({ state }: StateBadgeProps) {
  const tone = toneFor(state);
  const pulsing = TRANSITIONAL.has(state);
  return (
    <span
      className={`state-badge state-badge--${tone}${pulsing ? " state-badge--pulse" : ""}`}
      role="status"
      aria-label={`Lifecycle state: ${state}`}
    >
      {state}
    </span>
  );
}
