import { useEffect, useMemo, useState } from "react";

import { useConsolidate, useRelationships } from "../hooks/useIntelligence";
import {
  useArchiveMemory,
  useDeleteMemory,
  useMemory,
  useMemoryVersions,
  useRestoreMemory,
} from "../hooks/useMemories";
import { useExplain } from "../hooks/useRetrieval";
import { EmptyState } from "./EmptyState";
import { ErrorState } from "./ErrorState";
import { ExplainPanel } from "./ExplainPanel";
import { LifecycleTimeline } from "./LifecycleTimeline";
import { StateBadge } from "./StateBadge";
import { TrustIndicator } from "./TrustIndicator";
import { VersionSwitcher } from "./VersionSwitcher";
import "./MemoryDetail.css";

const TABS = ["overview", "semantics", "relationships", "trust", "history"] as const;
type Tab = (typeof TABS)[number];

export interface MemoryDetailProps {
  memoryId: string;
  onClose: () => void;
}

/** Detail pane: Overview · Semantics · Relationships · Trust · History tabs
 * (18-ui-design-system.md layout). `Esc` closes the pane.
 */
export function MemoryDetail({ memoryId, onClose }: MemoryDetailProps) {
  const [tab, setTab] = useState<Tab>("overview");
  const [selectedVersion, setSelectedVersion] = useState<number | undefined>(undefined);
  const [explainOpen, setExplainOpen] = useState(false);

  const memoryQuery = useMemory(memoryId, selectedVersion);
  const versionsQuery = useMemoryVersions(memoryId);
  const relationshipsQuery = useRelationships(tab === "relationships" ? memoryId : undefined);
  const explainQuery = useExplain(explainOpen ? { memory_id: memoryId } : undefined);
  const archiveMutation = useArchiveMemory(memoryId);
  const restoreMutation = useRestoreMemory(memoryId);
  const deleteMutation = useDeleteMemory(memoryId);
  const consolidateMutation = useConsolidate();

  const latestVersion = useMemo(() => {
    if (!versionsQuery.data || versionsQuery.data.length === 0) return undefined;
    return Math.max(...versionsQuery.data.map((v) => v.version));
  }, [versionsQuery.data]);

  useEffect(() => {
    function handleKeyDown(event: KeyboardEvent): void {
      if (event.key === "Escape") onClose();
    }
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [onClose]);

  if (memoryQuery.isPending) {
    return <p role="status">Loading memory…</p>;
  }
  if (memoryQuery.isError) {
    return <ErrorState error={memoryQuery.error} onRetry={() => void memoryQuery.refetch()} />;
  }

  const memory = memoryQuery.data;

  return (
    <section className="memory-detail" aria-label={`Memory detail: ${memory.content.title}`}>
      <header className="memory-detail__header">
        <button type="button" onClick={onClose} aria-label="Close detail pane">
          ×
        </button>
        <h2>{memory.content.title}</h2>
        <StateBadge state={memory.lifecycle.state} />
      </header>

      {versionsQuery.data && latestVersion !== undefined ? (
        <VersionSwitcher
          versions={versionsQuery.data}
          selectedVersion={selectedVersion ?? memory.lifecycle.version}
          currentVersion={latestVersion}
          onChange={setSelectedVersion}
        />
      ) : null}

      <div className="memory-detail__tabs" role="tablist" aria-label="Memory detail sections">
        {TABS.map((name) => (
          <button
            key={name}
            type="button"
            role="tab"
            aria-selected={tab === name}
            className={tab === name ? "active" : ""}
            onClick={() => setTab(name)}
          >
            {name[0]?.toUpperCase()}
            {name.slice(1)}
          </button>
        ))}
      </div>

      <div className="memory-detail__panel" role="tabpanel">
        {tab === "overview" ? (
          <dl className="memory-detail__grid">
            <dt>Summary</dt>
            <dd>{memory.content.summary || "—"}</dd>
            <dt>Description</dt>
            <dd>{memory.content.description || "—"}</dd>
            <dt>Namespace</dt>
            <dd className="mono">{memory.identity.namespace}</dd>
            <dt>Owner</dt>
            <dd className="mono">{memory.identity.owner_id}</dd>
          </dl>
        ) : null}

        {tab === "semantics" ? (
          <dl className="memory-detail__grid">
            <dt>Keywords</dt>
            <dd>{memory.semantics.keywords.join(", ") || "—"}</dd>
            <dt>Concepts</dt>
            <dd>{memory.semantics.concepts.join(", ") || "—"}</dd>
            <dt>Entities</dt>
            <dd>{memory.semantics.entities.join(", ") || "—"}</dd>
            <dt>Topics</dt>
            <dd>{memory.semantics.topics.join(", ") || "—"}</dd>
          </dl>
        ) : null}

        {tab === "relationships" ? (
          <div className="memory-detail__relationships-panel">
            <h3>Outbound</h3>
            {memory.relationships.length > 0 ? (
              <ul className="memory-detail__relationships">
                {memory.relationships.map((rel) => (
                  <li key={rel.relationship_id}>
                    <span className="mono">{rel.type}</span> → {rel.target_memory_id}
                    {rel.unresolved ? <em> (unresolved)</em> : null}
                  </li>
                ))}
              </ul>
            ) : (
              <EmptyState title="No outbound relationships" description="This memory links to no others yet." />
            )}

            <h3>Inbound</h3>
            {relationshipsQuery.data ? (
              (() => {
                const inbound = relationshipsQuery.data.relationships.filter(
                  (edge) => edge.target_memory_id === memory.memory_id,
                );
                return inbound.length > 0 ? (
                  <ul className="memory-detail__relationships">
                    {inbound.map((edge) => (
                      <li key={edge.relationship_id}>
                        <span className="mono">{edge.type}</span> ← {edge.source_memory_id}
                      </li>
                    ))}
                  </ul>
                ) : (
                  <EmptyState
                    title="No inbound relationships"
                    description="No other memory references this one yet."
                  />
                );
              })()
            ) : (
              <p role="status">Loading relationships…</p>
            )}
          </div>
        ) : null}

        {tab === "trust" ? (
          <div className="memory-detail__trust">
            <TrustIndicator
              confidence={memory.trust.confidence}
              verificationStatus={memory.trust.verification_status}
              sourceCount={memory.trust.source_count}
              onExplain={() => setExplainOpen(true)}
            />
            {explainOpen && explainQuery.data ? (
              <ExplainPanel explanation={explainQuery.data} />
            ) : null}
            {explainOpen && explainQuery.isError ? (
              <ErrorState error={explainQuery.error} onRetry={() => void explainQuery.refetch()} />
            ) : null}
          </div>
        ) : null}

        {tab === "history" ? (
          versionsQuery.data ? (
            <LifecycleTimeline versions={versionsQuery.data} />
          ) : (
            <p role="status">Loading history…</p>
          )
        ) : null}
      </div>

      <footer className="memory-detail__actions">
        {memory.lifecycle.state === "Active" ? (
          <button type="button" onClick={() => archiveMutation.mutate()}>
            Archive
          </button>
        ) : null}
        {memory.lifecycle.state === "Archived" ? (
          <button type="button" onClick={() => restoreMutation.mutate()}>
            Restore
          </button>
        ) : null}
        {memory.lifecycle.state === "Active" ? (
          <button
            type="button"
            onClick={() => {
              const primaryId = window.prompt(
                "Merge this memory into which primary memory_id? (Phase 4 Consolidate — this memory is archived, history preserved)",
              );
              if (primaryId?.trim()) {
                consolidateMutation.mutate({
                  primary_memory_id: primaryId.trim(),
                  duplicate_memory_ids: [memory.memory_id],
                });
              }
            }}
          >
            Merge into…
          </button>
        ) : null}
        {memory.lifecycle.state !== "Deleted" ? (
          <button
            type="button"
            className="memory-detail__danger"
            onClick={() => {
              if (window.confirm("Delete this memory? This cannot be undone.")) {
                deleteMutation.mutate();
              }
            }}
          >
            Delete
          </button>
        ) : null}
      </footer>
    </section>
  );
}
