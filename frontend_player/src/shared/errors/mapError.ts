/**
 * Backend envelope -> `AppError`. The one place a wire failure becomes something a
 * screen may look at.
 *
 * The envelope is `{ code, message, trace_id, details? }` on **every** error response,
 * including FastAPI's 422 and Starlette's own 4xx — the backend was corrected so that no
 * client has to special-case two body shapes.
 *
 * **Mapping is by `code` first and status second.** A status is a category; a code is the
 * failure. `question_not_outstanding` and `assessment_already_finished` are both 409s
 * from the same endpoint family and demand opposite recoveries, which is exactly why the
 * backend gives each error its own code and why this table is keyed on it.
 *
 * An unrecognised code is NOT an error in itself: old clients live on real phones for
 * months and the backend will add codes this build has never seen. Falling back to the
 * status keeps a future failure recoverable instead of terminal.
 */

import {
  AppError,
  networkUnavailable,
  unknownFailure,
  type AppErrorKind,
  type Recovery,
} from "./AppError";

/** The parsed envelope. Deliberately tolerant — a body may be truncated or absent. */
export interface ErrorEnvelope {
  readonly code?: unknown;
  readonly message?: unknown;
  readonly trace_id?: unknown;
  readonly details?: unknown;
}

type Classification = readonly [AppErrorKind, Recovery];

/**
 * Codes whose recovery does not follow from their status. Every entry here is a
 * deliberate correction, and the comment is the reason — a table that merely restated
 * the status map would be the status map written twice, drifting.
 */
const BY_CODE: Readonly<Record<string, Classification>> = {
  // --- 401s that are NOT "your session ended" ------------------------------------
  //
  // These arrive from a sign-in attempt, where there is no session to end. Treating
  // them as re-authentication would mean the sign-in screen reacting to a mistyped
  // password by tearing down a session the player never had — and, once #22's rotation
  // lands, by trying to refresh a token that does not exist.
  invalid_credentials: ["unauthorized", "requires-user-correction"],
  // The account exists and the password was right. Retrying changes nothing and the
  // player cannot fix it from the app.
  account_disabled: ["unauthorized", "terminal"],
  user_not_eligible: ["unauthorized", "terminal"],

  // --- 409s the player fixes by typing something else ----------------------------
  //
  // A conflict by status, but the recovery is a correction: pick another email or
  // nickname. Routing these to "business-conflict" would put a reconcile-and-retry
  // affordance on what is really a field error.
  email_already_registered: ["conflict", "requires-user-correction"],
  nickname_already_taken: ["conflict", "requires-user-correction"],
};

/**
 * Status -> classification, for every code this build has not been taught.
 *
 * 401 defaults to re-authentication because an authenticated request whose token the
 * server rejected is overwhelmingly the common case; the exceptions above are the
 * unauthenticated endpoints, which are a closed and short list.
 */
function byStatus(status: number): Classification {
  if (status === 400) return ["validation", "requires-user-correction"];
  if (status === 401) return ["unauthorized", "requires-reauthentication"];
  // A 403 is "you may not do this", said to a session that is perfectly valid. It must
  // never touch the session state machine. See docs/architecture.md Part 6.
  if (status === 403) return ["forbidden", "terminal"];
  if (status === 404) return ["not-found", "terminal"];
  if (status === 409) return ["conflict", "business-conflict"];
  if (status === 422) return ["validation", "requires-user-correction"];
  if (status === 429) return ["rate-limit", "retryable-by-user"];
  if (status >= 500) return ["server", "retryable-automatically"];
  return ["unknown", "terminal"];
}

function asString(value: unknown): string | undefined {
  return typeof value === "string" && value.length > 0 ? value : undefined;
}

function asDetails(value: unknown): Readonly<Record<string, unknown>> | undefined {
  return typeof value === "object" && value !== null && !Array.isArray(value)
    ? (value as Record<string, unknown>)
    : undefined;
}

/**
 * Build the normalized error for a non-OK response.
 *
 * `body` is whatever decoding produced — including `undefined` when the response had no
 * body or was not JSON at all. A 502 from a load balancer is HTML, and it must still
 * arrive as a `server` error rather than as a decode failure.
 */
export function mapErrorResponse(status: number, body: unknown): AppError {
  const envelope: ErrorEnvelope =
    typeof body === "object" && body !== null ? (body as ErrorEnvelope) : {};

  const code = asString(envelope.code);
  const classification =
    (code !== undefined ? BY_CODE[code] : undefined) ?? byStatus(status);
  const [kind, recovery] = classification;

  return new AppError(
    kind,
    recovery,
    asString(envelope.message) ?? `Request failed with status ${status}.`,
    {
      code,
      traceId: asString(envelope.trace_id),
      status,
      details: asDetails(envelope.details),
    },
  );
}

/**
 * Anything thrown below the response — a DNS failure, a dropped connection, a TLS
 * error. React Native's `fetch` rejects with a plain `TypeError` whose message differs
 * per platform, so this deliberately does not read it.
 *
 * An abort is the caller's own doing (a cancelled query, a timeout) and is turned into
 * its own error by the HTTP client before it reaches here.
 */
export function mapTransportFailure(cause: unknown): AppError {
  return networkUnavailable(cause);
}

/** A response that claimed to be JSON and was not. The contract broke, not the network. */
export function mapDecodeFailure(cause: unknown): AppError {
  return unknownFailure("The server's response could not be read.", cause);
}
