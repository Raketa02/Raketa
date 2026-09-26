import 'server-only';

/**
 * **What a call to the backend came to**, normalised once so that every feature branches on the
 * same thing: the wire's error `code`, never its message (ADR-0187 §6).
 *
 * Three codes are the website's own, for failures that carry no envelope:
 *
 * - `backend_unreachable`: the request never got an answer (refused, reset, timed out).
 * - `backend_failed`: an answer without an error envelope, such as a proxy's 502 page.
 * - `request_invalid`: a `422`, whatever its envelope says (the backend's reads
 *   `validation_error` and names no field). The website sent a body the contract refuses. The
 *   one box a desk types that the contract checks by format is an email (`format: email`), so a
 *   form with an email box places it there; anywhere else it is a bug here, said over the form.
 */

export interface ApiError {
  /** `0` when the backend never answered. */
  readonly status: number;
  readonly code: string;
  /** `details.field`, when the refusal names the control it is about. */
  readonly field?: string;
  /**
   * `details`' words, when the code defines any: `club_sport_declared_by_group` names the sport
   * and the group. Only a string survives; the code says what each one means.
   */
  readonly details?: Readonly<Record<string, string>>;
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

/** The string entries of an envelope's `details`, or nothing when it has none. */
function wordsOf(details: unknown): Record<string, string> | undefined {
  if (!isRecord(details)) return undefined;
  const words = Object.entries(details).filter(
    (entry): entry is [string, string] => typeof entry[1] === 'string',
  );
  return words.length === 0 ? undefined : Object.fromEntries(words);
}

export function toApiError(status: number, body: unknown): ApiError {
  if (status === 422) return { status, code: 'request_invalid' };
  if (isRecord(body) && typeof body.code === 'string') {
    const details = wordsOf(body.details);
    if (details === undefined) return { status, code: body.code };
    const { field } = details;
    return field === undefined
      ? { status, code: body.code, details }
      : { status, code: body.code, field, details };
  }
  return { status, code: 'backend_failed' };
}

export const UNREACHABLE: ApiError = { status: 0, code: 'backend_unreachable' };

/**
 * Run one call and settle it. A thrown fetch is `backend_unreachable`; anything answered is
 * classified by its body. Failures that are nobody's typing (unreachable, a 5xx, a 422) are
 * logged by code and trace id, never with a payload.
 */
export async function settle<T>(call: () => Promise<FetchResult<T>>): Promise<Outcome<T>> {
  let result: FetchResult<T>;
  try {
    result = await call();
  } catch {
    console.error('[club] backend unreachable');
    return { ok: false, error: UNREACHABLE };
  }
  if (result.response.ok) return { ok: true, data: result.data as T };

  const error = toApiError(result.response.status, result.error);
  if (error.status >= 500 || error.status === 422) {
    const trace = isRecord(result.error) ? result.error.trace_id : undefined;
    console.error(`[club] backend refused: ${error.status} ${error.code}`, trace ?? '');
  }
  return { ok: false, error };
}
