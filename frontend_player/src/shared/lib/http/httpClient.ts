/**
 * The single network entry point. **Exactly one place configures `fetch`** — ESLint
 * bans the global everywhere else, and this is the file the ban makes an exception for.
 *
 * It owns transport, never product: base URL, headers, the `Authorization` header, a
 * correlation id, `AbortSignal` propagation, response decoding, the timeout policy and
 * error normalization. It must not know what a Match, Booking, Court or Club is.
 *
 * This is also the only place the 401 -> refresh -> retry rotation will live (#22). The
 * seam it needs is already here: `configureHttp` injects the credential adapter, so the
 * rotation becomes a change to `send` rather than a change to every call site.
 *
 * **Nothing here ever logs a token, an `Authorization` header, a password or a full
 * payload** — including while debugging it. A redacted log is not a courtesy; a token in
 * a crash report is a live credential in a third party's database.
 */

import { getEnv } from "@/shared/config/env";
import {
  AppError,
  mapDecodeFailure,
  mapErrorResponse,
  mapTransportFailure,
  timedOut,
} from "@/shared/errors";

import { TIMEOUT_MS, type TimeoutClass } from "./timeouts";

/**
 * How the HTTP client reaches credentials without importing the auth subsystem.
 *
 * The dependency genuinely runs both ways — `shared/lib/auth` calls this client to sign
 * in, and this client needs auth's access token — so one direction is inverted rather
 * than left as an import cycle. Auth registers itself during bootstrap; the client
 * never imports auth.
 */
export interface HttpCredentials {
  /** The current access token, or `undefined` when there is no session. */
  readonly getAccessToken: () => string | undefined;
}

const NO_CREDENTIALS: HttpCredentials = { getAccessToken: () => undefined };

let credentials: HttpCredentials = NO_CREDENTIALS;

/** Called once, by the auth subsystem, during bootstrap. */
export function configureHttp(next: HttpCredentials): void {
  credentials = next;
}

/** Test seam, and the sign-out path: forget the adapter without tearing the module down. */
export function resetHttp(): void {
  credentials = NO_CREDENTIALS;
}

export type HttpMethod = "GET" | "POST" | "PUT" | "PATCH" | "DELETE";

export interface HttpRequest {
  readonly method: HttpMethod;
  /** Path only, rooted at the API host — `/api/v1/auth/login`. */
  readonly path: string;
  /** Serialized as JSON. Never logged. */
  readonly body?: unknown;
  /**
   * Whether to attach the access token.
   *
   * Explicit rather than inferred: login, refresh and registration are the endpoints
   * that must *not* carry a stale token, and "the endpoints that happen to have no
   * token right now" is a different set from "the endpoints that take none".
   */
  readonly authenticated: boolean;
  /** TanStack Query supplies one. Forwarded so a screen change stops the work. */
  readonly signal?: AbortSignal;
  readonly timeout?: TimeoutClass;
}

/**
 * A correlation id per request, in the narrow alphabet the backend accepts
 * (`[A-Za-z0-9._-]{1,64}`); anything else it discards and replaces with its own.
 *
 * `Math.random` is right here and would be wrong for a credential: this is an opaque
 * handle for tying a phone's failure to a server log, not a secret.
 */
let requestCounter = 0;
function newCorrelationId(): string {
  requestCounter += 1;
  const random = Math.random().toString(36).slice(2, 10);
  return `p-${random}-${requestCounter.toString(36)}`;
}

function buildUrl(path: string): string {
  const base = getEnv().apiUrl.replace(/\/+$/, "");
  return `${base}${path.startsWith("/") ? path : `/${path}`}`;
}

/**
 * One controller that aborts when *either* the caller's signal fires or the timeout
 * elapses, plus the means to tell those two apart afterwards.
 *
 * They must not be confused. A caller abort is a cancelled query and should propagate
 * as a cancellation; a timeout is a failure the player may retry. `AbortSignal.any` is
 * not dependable across Hermes versions, so the wiring is explicit.
 */
function withTimeout(timeoutMs: number, callerSignal?: AbortSignal) {
  const controller = new AbortController();
  let timedOutFlag = false;

  const timer = setTimeout(() => {
    timedOutFlag = true;
    controller.abort();
  }, timeoutMs);

  const onCallerAbort = () => controller.abort();
  if (callerSignal !== undefined) {
    if (callerSignal.aborted) controller.abort();
    else callerSignal.addEventListener("abort", onCallerAbort);
  }

  return {
    signal: controller.signal,
    get didTimeOut() {
      return timedOutFlag;
    },
    dispose() {
      clearTimeout(timer);
      callerSignal?.removeEventListener("abort", onCallerAbort);
    },
  };
}

/**
 * Decode a response body, tolerating the ones that have none.
 *
 * A 204 is the documented shape of several endpoints, and `res.json()` on an empty body
 * throws — so "no content" is decided before parsing rather than rescued after it.
 */
async function decode(response: Response): Promise<unknown> {
  if (response.status === 204) return undefined;

  const text = await response.text();
  if (text.length === 0) return undefined;

  try {
    return JSON.parse(text) as unknown;
  } catch {
    // Not JSON. For an error response this is fine — an edge proxy's 502 is HTML, and
    // the status still classifies it. For a success it is a broken contract, and the
    // caller finds out below.
    return text;
  }
}

/**
 * Perform a request and return its decoded body.
 *
 * Every failure leaves here as an `AppError`, with one deliberate exception: a caller
 * cancellation re-throws the underlying `AbortError`, because a cancelled request is not
 * a failure and TanStack Query needs to recognise it as such.
 */
export async function httpRequest<T>(request: HttpRequest): Promise<T> {
  // Everything that can fail for a reason that is NOT the network is done before the
  // try, on purpose. A `ConfigError` from an unvalidated environment, or a body that
  // cannot be serialized, is a bug in this build — and reporting it to the player as
  // "check your connection" would send them to restart their router over a broken app.
  const url = buildUrl(request.path);
  const payload = request.body === undefined ? undefined : JSON.stringify(request.body);

  const headers: Record<string, string> = {
    Accept: "application/json",
    "X-Request-ID": newCorrelationId(),
  };

  if (request.body !== undefined) headers["Content-Type"] = "application/json";

  if (request.authenticated) {
    const token = credentials.getAccessToken();
    if (token !== undefined) headers.Authorization = `Bearer ${token}`;
  }

  const timeoutMs = TIMEOUT_MS[request.timeout ?? "request"];
  const timeout = withTimeout(timeoutMs, request.signal);

  let response: Response;
  try {
    response = await fetch(url, {
      method: request.method,
      headers,
      body: payload,
      signal: timeout.signal,
    });
  } catch (cause) {
    if (timeout.signal.aborted) {
      if (timeout.didTimeOut) throw timedOut(timeoutMs);
      // The caller cancelled. Propagate it unchanged — this is not a failure.
      throw cause;
    }
    throw mapTransportFailure(cause);
  } finally {
    timeout.dispose();
  }

  const body = await decode(response);

  if (!response.ok) throw mapErrorResponse(response.status, body);

  // A successful response that was not JSON is a broken contract, not a network fault.
  if (typeof body === "string") throw mapDecodeFailure(body);

  return body as T;
}

/** Re-exported so a caller can narrow without reaching past this module. */
export { AppError };
