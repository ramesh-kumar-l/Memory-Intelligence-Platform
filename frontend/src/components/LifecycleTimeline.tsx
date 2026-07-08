import type { VersionInfo } from "@mip/sdk";

import "./LifecycleTimeline.css";

export interface LifecycleTimelineProps {
  versions: VersionInfo[];
}

/** Vertical version history, newest first. The backend does not expose a
 * per-event actor/event-type feed over the public API (only version rows —
 * `storage/interfaces.py VersionInfo`), so this renders version history
 * honestly rather than fabricating event-type/actor detail that isn't there.
 */
export function LifecycleTimeline({ versions }: LifecycleTimelineProps) {
  const sorted = [...versions].sort((a, b) => b.version - a.version);
  return (
    <ol className="lifecycle-timeline" aria-label="Version history, newest first">
      {sorted.map((version) => (
        <li key={version.version} className="lifecycle-timeline__item">
          <span className="lifecycle-timeline__dot" aria-hidden="true" />
          <span className="lifecycle-timeline__version mono">v{version.version}</span>
          <time dateTime={version.created_at} className="lifecycle-timeline__time">
            {new Date(version.created_at).toLocaleString()}
          </time>
          {version.previous_version != null ? (
            <span className="lifecycle-timeline__prev">from v{version.previous_version}</span>
          ) : (
            <span className="lifecycle-timeline__prev">initial version</span>
          )}
        </li>
      ))}
    </ol>
  );
}
