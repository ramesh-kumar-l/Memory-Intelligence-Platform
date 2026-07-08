/**
 * Typed error hierarchy mirroring the `MEM-*` envelope (05-api-design.md).
 * Mirrors the category taxonomy in `backend/mip/core/errors.py` and
 * `sdk/python/mip_sdk/errors.py` so client code can catch `LifecycleError`
 * etc. the same way server code does. Callers must key on `.code`, never on
 * `.message` (message text is not part of the contract).
 */

export interface ErrorEnvelope {
  code: string;
  category: string;
  message: string;
  details: Record<string, unknown>;
  recoverable: boolean;
  documentation_url: string;
}

export class MIPAPIError extends Error {
  readonly code: string;
  readonly category: string;
  readonly details: Record<string, unknown>;
  readonly recoverable: boolean;
  readonly documentationUrl: string;
  readonly httpStatus: number;
  readonly requestId: string | null;

  constructor(envelope: ErrorEnvelope, httpStatus: number, requestId: string | null) {
    super(`${envelope.code}: ${envelope.message}`);
    this.name = new.target.name;
    // `.message` holds the clean envelope text (mirrors the Python SDK's
    // `self.message = message`); `.code` carries the machine-readable part.
    // Callers who want "CODE: text" can compose `${err.code}: ${err.message}`.
    this.message = envelope.message;
    this.code = envelope.code;
    this.category = envelope.category;
    this.details = envelope.details;
    this.recoverable = envelope.recoverable;
    this.documentationUrl = envelope.documentation_url;
    this.httpStatus = httpStatus;
    this.requestId = requestId;
  }
}

export class ValidationError extends MIPAPIError {}
export class LifecycleError extends MIPAPIError {}
export class IdentityError extends MIPAPIError {}
export class ConcurrencyError extends MIPAPIError {}
export class TrustError extends MIPAPIError {}
export class StorageError extends MIPAPIError {}
export class SyncError extends MIPAPIError {}
export class SecurityError extends MIPAPIError {}

/** The server could not be reached at all (no HTTP response received). */
export class MIPConnectionError extends Error {
  constructor(message: string, options?: { cause?: unknown }) {
    super(message, options);
    this.name = "MIPConnectionError";
  }
}

const CATEGORY_TO_ERROR: Record<string, new (...args: ConstructorParameters<typeof MIPAPIError>) => MIPAPIError> = {
  Validation: ValidationError,
  Lifecycle: LifecycleError,
  Identity: IdentityError,
  Concurrency: ConcurrencyError,
  Trust: TrustError,
  Storage: StorageError,
  Sync: SyncError,
  Security: SecurityError,
};

export function errorFromEnvelope(
  body: { error?: Partial<ErrorEnvelope>; request_id?: string },
  httpStatus: number,
): MIPAPIError {
  const error = body.error ?? {};
  const envelope: ErrorEnvelope = {
    code: error.code ?? "MEM-0000",
    category: error.category ?? "Unknown",
    message: error.message ?? "Unknown error",
    details: error.details ?? {},
    recoverable: error.recoverable ?? false,
    documentation_url: error.documentation_url ?? "",
  };
  const ErrorClass = CATEGORY_TO_ERROR[envelope.category] ?? MIPAPIError;
  return new ErrorClass(envelope, httpStatus, body.request_id ?? null);
}
