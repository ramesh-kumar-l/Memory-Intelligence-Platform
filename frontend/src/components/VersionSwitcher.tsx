import type { VersionInfo } from "@mip/sdk";

import "./VersionSwitcher.css";

export interface VersionSwitcherProps {
  versions: VersionInfo[];
  selectedVersion: number;
  currentVersion: number;
  onChange: (version: number) => void;
}

/** Version dropdown on the memory detail pane. Older versions are clearly
 * watermarked "immutable historical version".
 */
export function VersionSwitcher({
  versions,
  selectedVersion,
  currentVersion,
  onChange,
}: VersionSwitcherProps) {
  const sorted = [...versions].sort((a, b) => b.version - a.version);
  return (
    <div className="version-switcher">
      <label htmlFor="version-switcher-select">Version</label>
      <select
        id="version-switcher-select"
        value={selectedVersion}
        onChange={(event) => onChange(Number(event.target.value))}
      >
        {sorted.map((version) => (
          <option key={version.version} value={version.version}>
            v{version.version}
            {version.version === currentVersion ? " (current)" : ""}
          </option>
        ))}
      </select>
      {selectedVersion !== currentVersion ? (
        <span className="version-switcher__watermark" role="note">
          immutable historical version
        </span>
      ) : null}
    </div>
  );
}
