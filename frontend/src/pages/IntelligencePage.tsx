import { useState } from "react";

import { ErrorState } from "../components/ErrorState";
import {
  useConsolidate,
  useExportBundle,
  useImportBundle,
  useLearn,
} from "../hooks/useIntelligence";
import "./IntelligencePage.css";

/** Phase 4 actions (ADR-0006): Consolidate, Learn, Export/Import. Kept on one
 * page — these are occasional maintenance operations, not daily-driver flows
 * like Memories/Search, so they don't warrant their own nav-level pages each.
 */
export function IntelligencePage() {
  return (
    <div className="intelligence-page">
      <h1>Intelligence</h1>
      <ConsolidateSection />
      <LearnSection />
      <PortabilitySection />
    </div>
  );
}

function ConsolidateSection() {
  const [primaryId, setPrimaryId] = useState("");
  const [duplicateIds, setDuplicateIds] = useState("");
  const consolidate = useConsolidate();

  return (
    <section className="intelligence-page__section" aria-labelledby="consolidate-heading">
      <h2 id="consolidate-heading">Consolidate</h2>
      <p className="intelligence-page__hint">
        Merge duplicate memories into a primary. Duplicates are archived, never deleted — history
        is preserved.
      </p>
      <form
        onSubmit={(event) => {
          event.preventDefault();
          const ids = duplicateIds
            .split(",")
            .map((id) => id.trim())
            .filter(Boolean);
          if (!primaryId.trim() || ids.length === 0) return;
          consolidate.mutate({ primary_memory_id: primaryId.trim(), duplicate_memory_ids: ids });
        }}
      >
        <label htmlFor="consolidate-primary">Primary memory ID</label>
        <input
          id="consolidate-primary"
          value={primaryId}
          onChange={(event) => setPrimaryId(event.target.value)}
        />
        <label htmlFor="consolidate-duplicates">Duplicate memory IDs (comma-separated)</label>
        <input
          id="consolidate-duplicates"
          value={duplicateIds}
          onChange={(event) => setDuplicateIds(event.target.value)}
        />
        <button type="submit" disabled={consolidate.isPending}>
          Merge
        </button>
      </form>
      {consolidate.isError ? (
        <ErrorState error={consolidate.error} onRetry={() => consolidate.reset()} />
      ) : null}
      {consolidate.isSuccess ? (
        <p role="status" className="intelligence-page__status">
          Merged. Primary now has consolidation_count ={" "}
          {consolidate.data.lifecycle.consolidation_count}.
        </p>
      ) : null}
    </section>
  );
}

function LearnSection() {
  const [memoryId, setMemoryId] = useState("");
  const [concepts, setConcepts] = useState("");
  const [reason, setReason] = useState("");
  const learn = useLearn();

  return (
    <section className="intelligence-page__section" aria-labelledby="learn-heading">
      <h2 id="learn-heading">Learn</h2>
      <p className="intelligence-page__hint">
        Add derived concepts to a memory's semantics. Never modifies original evidence — only
        unions new knowledge in.
      </p>
      <form
        onSubmit={(event) => {
          event.preventDefault();
          const conceptList = concepts
            .split(",")
            .map((c) => c.trim())
            .filter(Boolean);
          if (!memoryId.trim() || conceptList.length === 0 || !reason.trim()) return;
          learn.mutate({
            memory_id: memoryId.trim(),
            derived: { concepts: conceptList },
            reason: reason.trim(),
          });
        }}
      >
        <label htmlFor="learn-memory-id">Memory ID</label>
        <input
          id="learn-memory-id"
          value={memoryId}
          onChange={(event) => setMemoryId(event.target.value)}
        />
        <label htmlFor="learn-concepts">Derived concepts (comma-separated)</label>
        <input
          id="learn-concepts"
          value={concepts}
          onChange={(event) => setConcepts(event.target.value)}
        />
        <label htmlFor="learn-reason">Reason</label>
        <input id="learn-reason" value={reason} onChange={(event) => setReason(event.target.value)} />
        <button type="submit" disabled={learn.isPending}>
          Learn
        </button>
      </form>
      {learn.isError ? <ErrorState error={learn.error} onRetry={() => learn.reset()} /> : null}
      {learn.isSuccess ? (
        <p role="status" className="intelligence-page__status">
          Learned. Concepts: {learn.data.semantics.concepts.join(", ")}
        </p>
      ) : null}
    </section>
  );
}

function PortabilitySection() {
  const [namespace, setNamespace] = useState("");
  const exportBundle = useExportBundle();
  const importBundle = useImportBundle();

  return (
    <section className="intelligence-page__section" aria-labelledby="portability-heading">
      <h2 id="portability-heading">Export / Import</h2>
      <p className="intelligence-page__hint">
        Export a namespace to a portable JSON file (backup/migration); import a bundle exported
        from this or another MIP instance.
      </p>
      <div className="intelligence-page__portability-row">
        <label htmlFor="export-namespace">Namespace (optional)</label>
        <input
          id="export-namespace"
          value={namespace}
          onChange={(event) => setNamespace(event.target.value)}
        />
        <button
          type="button"
          disabled={exportBundle.isPending}
          onClick={() =>
            exportBundle.mutate(namespace.trim() || undefined, {
              onSuccess: (bundle) => downloadJson(bundle, "mip-export.json"),
            })
          }
        >
          Export &amp; download
        </button>
      </div>
      {exportBundle.isError ? (
        <ErrorState error={exportBundle.error} onRetry={() => exportBundle.reset()} />
      ) : null}
      {exportBundle.isSuccess ? (
        <p role="status" className="intelligence-page__status">
          Exported {exportBundle.data.memory_count} memories.
        </p>
      ) : null}

      <div className="intelligence-page__portability-row">
        <label htmlFor="import-file">Import bundle file</label>
        <input
          id="import-file"
          type="file"
          accept="application/json"
          onChange={(event) => {
            const file = event.target.files?.[0];
            if (!file) return;
            void file.text().then((text) => importBundle.mutate(JSON.parse(text)));
          }}
        />
      </div>
      {importBundle.isError ? (
        <ErrorState error={importBundle.error} onRetry={() => importBundle.reset()} />
      ) : null}
      {importBundle.isSuccess ? (
        <p role="status" className="intelligence-page__status">
          Imported {importBundle.data.imported.length}, skipped {importBundle.data.skipped.length},
          rejected {importBundle.data.rejected.length}.
        </p>
      ) : null}
    </section>
  );
}

function downloadJson(data: unknown, filename: string): void {
  const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  link.click();
  URL.revokeObjectURL(url);
}
