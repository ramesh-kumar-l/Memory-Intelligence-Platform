import { useState } from "react";

import { EmptyState } from "../components/EmptyState";
import { ErrorState } from "../components/ErrorState";
import { MemoryCard } from "../components/MemoryCard";
import { MemoryDetail } from "../components/MemoryDetail";
import { useMemoriesList } from "../hooks/useMemories";
import "./MemoriesPage.css";

/** Roving arrow-key navigation between MemoryCard buttons in the list pane. */
function handleListKeyDown(event: React.KeyboardEvent<HTMLDivElement>): void {
  if (event.key !== "ArrowDown" && event.key !== "ArrowUp") return;
  const buttons = Array.from(event.currentTarget.querySelectorAll("button"));
  const currentIndex = buttons.indexOf(document.activeElement as HTMLButtonElement);
  if (currentIndex === -1) return;
  event.preventDefault();
  const nextIndex =
    event.key === "ArrowDown"
      ? Math.min(currentIndex + 1, buttons.length - 1)
      : Math.max(currentIndex - 1, 0);
  buttons[nextIndex]?.focus();
}

export function MemoriesPage() {
  const [namespace, setNamespace] = useState("");
  const [selectedId, setSelectedId] = useState<string | undefined>(undefined);
  const listQuery = useMemoriesList({ namespace: namespace.trim() || undefined, limit: 50 });

  return (
    <div className="memories-page">
      <h1>Memories</h1>
      <div className="memories-page__filters">
        <label htmlFor="memories-namespace-filter">Namespace</label>
        <input
          id="memories-namespace-filter"
          value={namespace}
          onChange={(event) => setNamespace(event.target.value)}
          placeholder="all namespaces"
        />
      </div>
      <div className="memories-page__panes">
        <div
          className="memories-page__list"
          role="list"
          aria-label="Memories"
          onKeyDown={handleListKeyDown}
        >
          {listQuery.isPending ? <p role="status">Loading memories…</p> : null}
          {listQuery.isError ? (
            <ErrorState error={listQuery.error} onRetry={() => void listQuery.refetch()} />
          ) : null}
          {listQuery.data && listQuery.data.items.length === 0 ? (
            <EmptyState
              title="No memories yet"
              description="Create one via the Python/TypeScript SDK or CLI to see it here."
            />
          ) : null}
          {listQuery.data?.items.map((record) => (
            <div role="listitem" key={record.memory_id}>
              <MemoryCard
                record={record}
                selected={record.memory_id === selectedId}
                onSelect={setSelectedId}
              />
            </div>
          ))}
        </div>
        {selectedId ? (
          <div className="memories-page__detail">
            <MemoryDetail memoryId={selectedId} onClose={() => setSelectedId(undefined)} />
          </div>
        ) : null}
      </div>
    </div>
  );
}
