import 'server-only';

/**
 * **What a call to the backend came to**, normalised once so that every feature branches on the
 * same thing: the wire's error `code`, never its message (ADR-0187 §6).
 *
 * Three codes are the site's own, for failures that carry no envelope:
 *
 * - `backend_unreachable`: the request never got an answer (refused, reset, timed out).
 * - `backend_failed`: an answer without an error envelope, such as a proxy's 502 page.
 * - `request_invalid`: a `422`, whatever its envelope says (the backend's reads
 *   `validation_error` and names no field). The site sent something the contract refuses, which
 *   is a bug here.
 */

export interface ApiError {
  /** `0` when the backend never answered. */
  readonly status: number;
  readonly code: string;
  /** `details.field`, when the refusal names the control it is about: `password_too_weak`'s. */
  readonly field?: string;
}

export type Outcome<T> =
  { readonly ok: true; readonly data: T } | { readonly ok: false; readonly error: ApiError };

/** The shape every openapi-fetch call resolves to. */
export interface FetchResult<T> {
  readonly data?: T;
  readonly error?: unknown;
  readonly response: Response;
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null;
}

export function toApiError(status: number, body: unknown): ApiError {
  if (status === 422) return { status, code: 'request_invalid' };
  if (isRecord(body) && typeof body.code === 'string') {
    const field = isRecord(body.details) ? body.details.field : undefined;
    return typeof field === 'string'
      ? { status, code: body.code, field }
      : { status, code: body.code };
  }
  return { status, code: 'backend_failed' };
}

export const UNREACHABLE: ApiError = { status: 0, code: 'backend_unreachable' };

/**
 * Run one call and settle it. A thrown fetch is `backend_unreachable`; anything answered is
 * classified by its body. Failures that are nobody's doing (unreachable, a 5xx, a 422) are
 * logged by code and trace id, never with a payload.
 */
export async function settle<T>(call: () => Promise<FetchResult<T>>): Promise<Outcome<T>> {
  let result: FetchResult<T>;
  try {
    result = await call();
  } catch {
    console.error('[public] backend unreachable');
    return { ok: false, error: UNREACHABLE };
  }
  if (result.response.ok) return { ok: true, data: result.data as T };

  const error = toApiError(result.response.status, result.error);
  if (error.status >= 500 || error.status === 422 || error.code === 'backend_failed') {
    const trace = isRecord(result.error) ? result.error.trace_id : undefined;
    console.error(`[public] backend refused: ${error.status} ${error.code}`, trace ?? '');
  }
  return { ok: false, error };
}
