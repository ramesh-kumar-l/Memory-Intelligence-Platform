import { MIPAPIError, MIPConnectionError } from "@mip/sdk";

import "./ErrorState.css";

export interface ErrorStateProps {
  error: unknown;
  onRetry?: () => void;
}

/** Every list/panel error state mirrors the API error envelope: code + human
 * message + recovery action, per 18-ui-design-system.md.
 */
export function ErrorState({ error, onRetry }: ErrorStateProps) {
  const isApiError = error instanceof MIPAPIError;
  const isConnectionError = error instanceof MIPConnectionError;
  const message = isApiError
    ? error.message
    : isConnectionError
      ? "Could not reach the MIP API. Check the API URL in Settings and that the server is running."
      : error instanceof Error
        ? error.message
        : "Something went wrong.";

  return (
    <div className="error-state" role="alert">
      {isApiError ? <p className="error-state__code mono">{error.code}</p> : null}
      <p className="error-state__message">{message}</p>
      <div className="error-state__actions">
        {onRetry ? (
          <button type="button" onClick={onRetry}>
            Retry
          </button>
        ) : null}
        {isApiError && error.documentationUrl ? (
          <a href={error.documentationUrl} target="_blank" rel="noreferrer">
            Learn more
          </a>
        ) : null}
      </div>
    </div>
  );
}
