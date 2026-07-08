import { useEffect, useRef } from "react";

import "./SearchBar.css";

export type SearchMode = "keyword" | "semantic" | "hybrid" | "graph";

export interface SearchBarProps {
  query: string;
  mode: SearchMode;
  namespace: string;
  onQueryChange: (query: string) => void;
  onModeChange: (mode: SearchMode) => void;
  onNamespaceChange: (namespace: string) => void;
  onSubmit: () => void;
}

/** Mode selector (keyword/semantic/hybrid), query, namespace filter chip.
 * `/` focuses the query input, unless another text field already has focus.
 */
export function SearchBar({
  query,
  mode,
  namespace,
  onQueryChange,
  onModeChange,
  onNamespaceChange,
  onSubmit,
}: SearchBarProps) {
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    function handleKeyDown(event: KeyboardEvent): void {
      if (event.key !== "/") return;
      const target = event.target as HTMLElement | null;
      if (target && ["INPUT", "TEXTAREA", "SELECT"].includes(target.tagName)) return;
      event.preventDefault();
      inputRef.current?.focus();
    }
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, []);

  return (
    <form
      className="search-bar"
      role="search"
      onSubmit={(event) => {
        event.preventDefault();
        onSubmit();
      }}
    >
      <label className="visually-hidden" htmlFor="search-bar-query">
        Search memories
      </label>
      <input
        id="search-bar-query"
        ref={inputRef}
        type="search"
        placeholder={
          mode === "graph"
            ? "Seed memory ID… (press / to focus)"
            : "Search memories… (press / to focus)"
        }
        value={query}
        onChange={(event) => onQueryChange(event.target.value)}
      />
      <label className="visually-hidden" htmlFor="search-bar-mode">
        Search mode
      </label>
      <select
        id="search-bar-mode"
        value={mode}
        onChange={(event) => onModeChange(event.target.value as SearchMode)}
      >
        <option value="hybrid">Hybrid</option>
        <option value="keyword">Keyword</option>
        <option value="semantic">Semantic</option>
        <option value="graph">Graph</option>
      </select>
      <label className="visually-hidden" htmlFor="search-bar-namespace">
        Namespace filter
      </label>
      <input
        id="search-bar-namespace"
        placeholder="namespace (optional)"
        value={namespace}
        onChange={(event) => onNamespaceChange(event.target.value)}
      />
      <button type="submit">Search</button>
    </form>
  );
}
