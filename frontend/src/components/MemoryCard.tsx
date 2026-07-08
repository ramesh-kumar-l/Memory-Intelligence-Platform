import type { MemoryRecord } from "@mip/sdk";

import { StateBadge } from "./StateBadge";
import "./MemoryCard.css";

export interface MemoryCardProps {
  record: MemoryRecord;
  selected?: boolean;
  onSelect: (memoryId: string) => void;
}

/** List-pane card: title, type, state badge, relative time. Entire card is
 * clickable. Note: the list endpoint returns a lightweight `MemoryRecord`
 * projection (no confidence/summary) — the full Trust panel lives in the
 * detail pane once a memory_id is selected.
 */
export function MemoryCard({ record, selected = false, onSelect }: MemoryCardProps) {
  return (
    <button
      type="button"
      className={`memory-card${selected ? " memory-card--selected" : ""}`}
      onClick={() => onSelect(record.memory_id)}
      aria-current={selected ? "true" : undefined}
    >
      <div className="memory-card__header">
        <span className="memory-card__type">{record.object_type}</span>
        <StateBadge state={record.state} />
      </div>
      <h3 className="memory-card__title">{record.title}</h3>
      <p className="memory-card__time">{new Date(record.created_at).toLocaleString()}</p>
    </button>
  );
}
