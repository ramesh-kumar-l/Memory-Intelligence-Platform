import { useState } from "react";

import { EmptyState } from "../components/EmptyState";
import { ErrorState } from "../components/ErrorState";
import { ExplainPanel } from "../components/ExplainPanel";
import { SearchBar, type SearchMode } from "../components/SearchBar";
import { useExplain, useSearch } from "../hooks/useRetrieval";
import "./SearchPage.css";

interface SubmittedQuery {
  query: string;
  mode: SearchMode;
  namespace: string | undefined;
}

export function SearchPage() {
  const [query, setQuery] = useState("");
  const [mode, setMode] = useState<SearchMode>("hybrid");
  const [namespace, setNamespace] = useState("");
  const [submitted, setSubmitted] = useState<SubmittedQuery | null>(null);
  const [explainFor, setExplainFor] = useState<string | undefined>(undefined);

  const searchQuery = useSearch(
    {
      query: submitted?.query ?? "",
      mode: submitted?.mode ?? "hybrid",
      namespace: submitted?.namespace,
    },
    submitted !== null,
  );

  const explainQuery = useExplain(
    explainFor ? { memory_id: explainFor, query: submitted?.query, mode: submitted?.mode } : undefined,
  );

  return (
    <div className="search-page">
      <h1>Search</h1>
      <SearchBar
        query={query}
        mode={mode}
        namespace={namespace}
        onQueryChange={setQuery}
        onModeChange={setMode}
        onNamespaceChange={setNamespace}
        onSubmit={() => {
          if (!query.trim()) return;
          setExplainFor(undefined);
          setSubmitted({ query, mode, namespace: namespace.trim() || undefined });
        }}
      />

      {submitted && searchQuery.isPending ? <p role="status">Searching…</p> : null}
      {submitted && searchQuery.isError ? (
        <ErrorState error={searchQuery.error} onRetry={() => void searchQuery.refetch()} />
      ) : null}
      {submitted && searchQuery.data && searchQuery.data.items.length === 0 ? (
        <EmptyState title="No results" description={`No memories matched "${submitted.query}".`} />
      ) : null}

      <ul className="search-page__results">
        {searchQuery.data?.items.map((item) => (
          <li key={item.memory_id} className="search-page__result">
            <div className="search-page__result-header">
              <span className="mono">{item.memory_id}</span>
              <span>score {item.score.toFixed(4)}</span>
            </div>
            <button type="button" onClick={() => setExplainFor(item.memory_id)}>
              Why this result?
            </button>
            {explainFor === item.memory_id && explainQuery.data ? (
              <ExplainPanel explanation={explainQuery.data} />
            ) : null}
          </li>
        ))}
      </ul>

      {searchQuery.data && !searchQuery.data.complete ? (
        <p className="search-page__more">More results are available (load-more is not yet wired up).</p>
      ) : null}
    </div>
  );
}
