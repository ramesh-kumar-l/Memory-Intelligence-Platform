import { useState } from "react";

import { getApiBaseUrl, setApiBaseUrl } from "../api/client";
import { ErrorState } from "../components/ErrorState";
import { useHealth } from "../hooks/useAdmin";
import "./SettingsPage.css";

export function SettingsPage() {
  const [url, setUrl] = useState(getApiBaseUrl());
  const [checked, setChecked] = useState(false);
  const healthQuery = useHealth(checked);

  return (
    <div className="settings-page">
      <h1>Settings</h1>
      <form
        className="settings-page__form"
        onSubmit={(event) => {
          event.preventDefault();
          setApiBaseUrl(url);
          setChecked(true);
          void healthQuery.refetch();
        }}
      >
        <label htmlFor="settings-api-url">API base URL</label>
        <input
          id="settings-api-url"
          value={url}
          onChange={(event) => setUrl(event.target.value)}
          placeholder="http://localhost:8000"
        />
        <button type="submit">Save &amp; test connection</button>
      </form>

      {checked && healthQuery.isPending ? <p role="status">Checking connection…</p> : null}
      {checked && healthQuery.isError ? (
        <ErrorState error={healthQuery.error} onRetry={() => void healthQuery.refetch()} />
      ) : null}
      {checked && healthQuery.data ? (
        <p role="status" className="settings-page__status">
          Status: <strong>{healthQuery.data.status}</strong> · Storage:{" "}
          <strong>{healthQuery.data.storage ? "ok" : "degraded"}</strong>
        </p>
      ) : null}
    </div>
  );
}
