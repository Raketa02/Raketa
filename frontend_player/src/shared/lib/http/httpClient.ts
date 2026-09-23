/**
 * The single network entry point. **Exactly one place configures `fetch`** — ESLint
 * bans the global everywhere else, and this is the file the ban makes an exception for.
 *
 * It owns transport, never product: base URL, headers, the `Authorization` header, a
 * correlation id, `AbortSignal` propagation, response decoding, the timeout policy and
 * error normalization. It must not know what a Match, Booking, Court or Club is.
 *
 * This is also the only place the 401 -> refresh -> retry rotation lives. A feature, hook
 * or screen that implemented its own would be a second networking path, and the point of
 * the rotation is that a token expiring mid-flow is invisible to everything above here.
 *
 * **Nothing here ever logs a token, an `Authorization` header, a password or a full
 * payload** — including while debugging it. A redacted log is not a courtesy; a token in
 * a crash report is a live credential in a third party's database.
 */

import { getEnv } from '@/shared/config/env';
import {
  AppError,
  mapDecodeFailure,
  mapErrorResponse,
  mapTransportFailure,
  networkUnavailable,
  timedOut,
} from '@/shared/errors';

import { TIMEOUT_MS, type TimeoutClass } from './timeouts';

/** A credential and the rotation it belongs to. Supplied by the auth subsystem. */
export interface HttpCredential {
  readonly accessToken: string;
  /**
   * Which rotation this token came from. Sent back with a refresh request so a 401
   * answering an already-replaced token can be told from one answering the current
   * token — see `refreshCoordinator`.
   */
  readonly generation: number;
}

/** What a rotation leaves the request free to do. Mirrors `RefreshOutcome`. */
export type HttpRefreshOutcome = 'retry' | 'session-ended' | 'unavailable';

/**
 * How the HTTP client reaches credentials without importing the auth subsystem.
 *
 * The dependency genuinely runs both ways — `shared/lib/auth` calls this client to sign
 * in, and this client needs auth's access token — so one direction is inverted rather
 * than left as an import cycle. Auth registers itself during bootstrap; the client
 * never imports auth.
 *
 * Three members, because the rotation needs three things and no more: the credential to
 * send, a way to rotate it, and a way to say the transport has proved the session over.
 * Note what is *not* here — no token is ever passed in or out as a bare string, and
 * nothing above this interface can read one.
 */
export interface HttpCredentials {
  /** The credential for the next request, or `undefined` when there is no session. */
  readonly current: () => HttpCredential | undefined;
  /** Rotate, single-flight. `seen` is the generation the failing request carried. */
  readonly refresh: (seen: number) => Promise<HttpRefreshOutcome>;
  /** A freshly-rotated credential was rejected too. End the session, once. */
  readonly abandon: () => Promise<void>;
}

/**
 * Before `configureHttp` runs there is no session and nothing to rotate.
 *
 * `refresh` reports `unavailable` rather than `session-ended` on purpose: an
 * unconfigured client knows nothing about the session, and the one thing it must not do
 * is claim a session is over.
 */
const NO_CREDENTIALS: HttpCredentials = {
  current: () => undefined,
  refresh: () => Promise.resolve('unavailable'),
  abandon: () => Promise.resolve(),
};

let credentials: HttpCredentials = NO_CREDENTIALS;

/** Called once, by the auth subsystem, during bootstrap. */
export function configureHttp(next: HttpCredentials): void {
  credentials = next;
}

/** Test seam, and the sign-out path: forget the adapter without tearing the module down. */
export function resetHttp(): void {
  credentials = NO_CREDENTIALS;
}

export type HttpMethod = 'GET' | 'POST' | 'PUT' | 'PATCH' | 'DELETE';

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
  /**
   * What the caller calls this write, sent as `Idempotency-Key`.
   *
   * Transport, not product: the header is how a client says *this is the same request,
   * not a second one*, and which endpoints take one is the contract's business rather
   * than this module's. It is here for the same reason the `Authorization` header is —
   * a second place that set it would be a second networking path.
   *
   * **The key is the caller's to keep stable.** Rotating it between a failure and its
   * retry is what turns one write into two, and nothing here can tell those apart.
   */
  readonly idempotencyKey?: string;
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

export function buildUrl(path: string): string {
  return joinUrl(getEnv().apiUrl, path);
}

function joinUrl(base: string, path: string): string {
  return `${base.replace(/\/+$/, '')}${path.startsWith('/') ? path : `/${path}`}`;
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
    else callerSignal.addEventListener('abort', onCallerAbort);
  }

  return {
    signal: controller.signal,
    get didTimeOut() {
      return timedOutFlag;
    },
    dispose() {
      clearTimeout(timer);
      callerSignal?.removeEventListener('abort', onCallerAbort);
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

/** One trip to the socket and back, decoded but not yet judged. */
export interface Attempt {
  readonly status: number;
  readonly ok: boolean;
  readonly body: unknown;
  /**
   * The generation of the credential this attempt carried, or `undefined` when it
   * carried none — because the endpoint takes no token, or because there is no session.
   */
  readonly sentWith: number | undefined;
}

/**
 * One call to the socket, in the terms `fetch` takes.
 *
 * The two verbs above this — a JSON request and a file upload — differ in what they put
 * in the body and how long they are allowed to take, and in nothing else. So each builds
 * one of these and the correlation id, the `Authorization` header, the timeout wiring,
 * the decoding and the failure classification are written once. A third verb that needed
 * its own copy of those is the second networking path this module exists to prevent.
 */
export interface WireCall {
  readonly method: HttpMethod;
  readonly url: string;
  /** `undefined` when the request carries nothing — a GET, or a POST with no body. */
  readonly body: BodyInit | undefined;
  /** Sent as `Content-Type`. Absent whenever `body` is. */
  readonly contentType: string | undefined;
  readonly authenticated: boolean;
  /** Sent as `Idempotency-Key`. Absent on every call that does not name one. */
  readonly idempotencyKey?: string;
  readonly signal?: AbortSignal;
  readonly timeoutMs: number;
}

export async function sendOnce(call: WireCall): Promise<Attempt> {
  const headers: Record<string, string> = {
    Accept: 'application/json',
    'X-Request-ID': newCorrelationId(),
  };

  if (call.contentType !== undefined) headers['Content-Type'] = call.contentType;

  // Set on every attempt, including the replay a 401 rotation makes: the whole point of
  // the key is that the second attempt is not a second write, and dropping it there would
  // turn the rotation — which exists to be invisible — into a duplicate commit.
  if (call.idempotencyKey !== undefined) headers['Idempotency-Key'] = call.idempotencyKey;

  let sentWith: number | undefined;
  if (call.authenticated) {
    const credential = credentials.current();
    if (credential !== undefined) {
      headers.Authorization = `Bearer ${credential.accessToken}`;
      sentWith = credential.generation;
    }
  }

  const timeout = withTimeout(call.timeoutMs, call.signal);

  let response: Response;
  try {
    response = await fetch(call.url, {
      method: call.method,
      headers,
      body: call.body,
      signal: timeout.signal,
    });
  } catch (cause) {
    if (timeout.signal.aborted) {
      if (timeout.didTimeOut) throw timedOut(call.timeoutMs);
      // The caller cancelled. Propagate it unchanged — this is not a failure.
      throw cause;
    }
    throw mapTransportFailure(cause);
  } finally {
    timeout.dispose();
  }

  return {
    status: response.status,
    ok: response.ok,
    body: await decode(response),
    sentWith,
  };
}

/**
 * Send, rotating an expired token underneath the caller, and judge what came back.
 *
 * **This is the whole of the 401 rotation and there is exactly one of it.** `send` is
 * called again, unchanged, when a rotation succeeds — so whatever builds the call has to
 * be able to build it twice, which for a body means one that can be read twice.
 *
 * Every failure leaves here as an `AppError`, with one deliberate exception: a caller
 * cancellation re-throws the underlying `AbortError`, because a cancelled request is not
 * a failure and TanStack Query needs to recognise it as such.
 *
 * ## Replaying the request is safe, and only here
 *
 * The backend raises every 401 from the dependency that resolves the current player —
 * *before* the handler runs — so a 401'd request had no effect and sending it again
 * cannot repeat one. That is what separates this from a retry on a timeout or a 5xx,
 * where the request may well have been executed and a replay would double it; those are
 * governed by the Query client's policy, which never retries a mutation.
 *
 * The replay is bounded to requests that went out with an `Authorization` header. Login,
 * refresh, registration and logout declare `authenticated: false`, so a wrong password is
 * never answered by rotating a token, and the refresh call can never refresh itself.
 */
export async function sendWithRotation<T>(
  authenticated: boolean,
  send: () => Promise<Attempt>,
): Promise<T> {
  let attempt = await send();

  // `sentWith` undefined means the request carried no credential, so there is nothing to
  // rotate and the 401 is simply correct.
  if (attempt.status === 401 && attempt.sentWith !== undefined) {
    const outcome = await credentials.refresh(attempt.sentWith);

    if (outcome === 'unavailable') {
      // We could not find out whether the session is still valid, and the session has
      // deliberately *not* been touched. Surfacing the 401 here would be a lie with
      // consequences: its recovery is `requires-reauthentication`, so launch validation
      // and every screen would read a dropped connection as a session that ended.
      throw networkUnavailable();
    }

    if (outcome === 'retry' && credentials.current() !== undefined) {
      attempt = await send();

      if (attempt.status === 401) {
        // A credential minted seconds ago was rejected too. There is nothing left to
        // rotate, and asking again is the infinite `401 -> refresh -> retry -> 401` loop
        // that drains a battery and hammers the API. The session ends here, once.
        await credentials.abandon();
      }
    }
  } else if (attempt.status === 401 && authenticated) {
    // An authenticated request went out with **no credential at all** and was refused.
    //
    // The app believes it has a session and holds nothing to prove it. There is no token
    // to rotate, so the block above cannot help and the 401 would otherwise surface as
    // `requires-reauthentication` with the session machine untouched — leaving the player
    // on a retry that re-sends the same headerless request every time it is pressed.
    //
    // Whatever produced the mismatch, the honest reading is the same: this session is
    // over. Ending it lets the routing guard do what a retry cannot.
    await credentials.abandon();
  }

  if (!attempt.ok) throw mapErrorResponse(attempt.status, attempt.body);

  // A successful response that was not JSON is a broken contract, not a network fault.
  if (typeof attempt.body === 'string') throw mapDecodeFailure(attempt.body);

  return attempt.body as T;
}

/** Perform a JSON request and return its decoded body. */
export async function httpRequest<T>(request: HttpRequest): Promise<T> {
  // Everything that can fail for a reason that is NOT the network is done first, on
  // purpose. A `ConfigError` from an unvalidated environment, or a body that cannot be
  // serialized, is a bug in this build — and reporting it to the player as "check your
  // connection" would send them to restart their router over a broken app.
  const url = buildUrl(request.path);
  const payload = request.body === undefined ? undefined : JSON.stringify(request.body);

  return sendWithRotation<T>(request.authenticated, () =>
    sendOnce({
      method: request.method,
      url,
      body: payload,
      contentType: payload === undefined ? undefined : 'application/json',
      authenticated: request.authenticated,
      idempotencyKey: request.idempotencyKey,
      signal: request.signal,
      timeoutMs: TIMEOUT_MS[request.timeout ?? 'request'],
    }),
  );
}

/** A read from the features host. Path only; the host and everything else are this module's. */
export interface FeaturesHostRequest {
  /** Rooted at the features host — `/local/featurevisor-player.json`. */
  readonly path: string;
  /** TanStack Query supplies one. Forwarded so a cancelled query stops the read. */
  readonly signal?: AbortSignal;
}

/**
 * **A GET from the features host** — the module's third verb, and the only request this app
 * makes to a host that is not the API.
 *
 * The feature-flag datafile is served from `EXPO_PUBLIC_FEATURES_URL`
 * ([ADR-0180](../../../../../docs/adr/0180-a-feature-is-turned-on-by-a-pull-request-and-decided-on-the-device.md)
 * §4, §6), and it comes through here for every reason an API response does: the timeout, the
 * correlation id, the cancellation and the error model are written once, and a feature that
 * fetched its own document would be the second networking path this module exists to prevent.
 *
 * **A verb rather than a flag on `httpRequest`, because of what it must never send.** That host
 * is somebody's Mac on the LAN today and a public bucket tomorrow, and a bearer token sent to
 * either is a credential handed to a server that has no use for it. Here that is not a field a
 * caller could set wrong: the call is built unauthenticated, so the rotation above has nothing to
 * rotate and a 401 is simply a failure.
 *
 * **A background read.** Nobody is looking at a spinner for a datafile — the app runs on the last
 * one it had until this answers — so it takes the class for work nobody waits on.
 */
export async function httpGetFromFeaturesHost<T>(request: FeaturesHostRequest): Promise<T> {
  const url = joinUrl(getEnv().featuresUrl, request.path);

  return sendWithRotation<T>(false, () =>
    sendOnce({
      method: 'GET',
      url,
      body: undefined,
      contentType: undefined,
      authenticated: false,
      signal: request.signal,
      timeoutMs: TIMEOUT_MS.background,
    }),
  );
}

/**
 * What one **authenticated stream** attempt goes out with — a URL, the headers, and which
 * rotation the credential in them came from.
 *
 * `undefined` where there is no session: there is nothing to authorise an attempt with, and a
 * stream opened without a credential is a `401` this module would then have to explain.
 */
export interface StreamAttempt {
  readonly url: string;
  readonly headers: Readonly<Record<string, string>>;
  /** Handed back to {@link rotateStreamCredential} when the attempt is refused. */
  readonly generation: number;
}

/**
 * **Authorise one attempt at an open stream.**
 *
 * The app has one long-lived read that is not a `fetch` — the conversation's live channel, which
 * is Server-Sent Events over `XMLHttpRequest` behind `shared/lib/platform`'s `LiveStreamPort`
 * ([ADR-0147](../../../../../docs/adr/0147-the-live-channel-carries-a-nudge-and-the-sequence-is-what-cannot-be-swapped.md)
 * §4). It cannot go through {@link httpRequest}: there is no response to decode, no timeout to
 * apply, and the whole point of it is that it does not end.
 *
 * **What it may not have is a second `Authorization` header.** That is the one thing this module
 * exists to own, so the header is minted here and the port is handed it whole — it forwards the
 * bag to the transport and reads nothing out of it. Two integers and a string cross the seam; no
 * token is passed as a value anybody above could name.
 *
 * **A fresh bag per attempt, and that is the load-bearing half.** The stream is closed by the
 * server at the access token's `exp`, roughly every fifteen minutes (ADR-0147 §6), so a channel
 * that captured its headers once and reconnected with them would reconnect with the credential
 * that had just expired — for ever. Each attempt asks again.
 */
export function streamAttempt(path: string): StreamAttempt | undefined {
  const credential = credentials.current();
  if (credential === undefined) return undefined;

  return {
    url: buildUrl(path),
    headers: {
      Authorization: `Bearer ${credential.accessToken}`,
      'X-Request-ID': newCorrelationId(),
    },
    generation: credential.generation,
  };
}

/**
 * Rotate after a stream attempt was refused as unauthenticated, and say whether another attempt
 * is worth making.
 *
 * `credentials.refresh` and nothing else, so a stream reconnecting through an expired token takes
 * the **same single-flight rotation** every request takes — a second one would be the second
 * networking path in the one shape that is hardest to notice, because it only runs a quarter of
 * an hour after anybody looked.
 *
 * **It never calls `abandon`, and that is deliberate.** A rejected replay is what tears a session
 * down in {@link sendWithRotation}, and there the request that discovered it is one the player is
 * waiting on. A stream is not: it is a latency optimisation over an authoritative read path that
 * is running on the same screen and will reach the same conclusion through the path that is
 * allowed to act on it. So the honest answer here is `false` — *stop attempting* — and the
 * session's fate belongs to the requests the player can see.
 */
export async function rotateStreamCredential(seen: number): Promise<boolean> {
  const outcome = await credentials.refresh(seen);
  return outcome === 'retry' && credentials.current() !== undefined;
}

/** Re-exported so a caller can narrow without reaching past this module. */
export { AppError };
