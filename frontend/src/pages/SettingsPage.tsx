import { useState } from "react";

import { getApiBaseUrl, getApiKey, setApiBaseUrl, setApiKey } from "../api/client";
import { ErrorState } from "../components/ErrorState";
import { useHealth } from "../hooks/useAdmin";
import "./SettingsPage.css";

export function SettingsPage() {
  const [url, setUrl] = useState(getApiBaseUrl());
  const [apiKey, setApiKeyInput] = useState(getApiKey());
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
          setApiKey(apiKey);
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
        <label htmlFor="settings-api-key">
          API key <span className="settings-page__hint">(only if the server requires one)</span>
        </label>
        <input
          id="settings-api-key"
          type="password"
          value={apiKey}
          onChange={(event) => setApiKeyInput(event.target.value)}
          placeholder="Leave blank if auth is disabled"
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
