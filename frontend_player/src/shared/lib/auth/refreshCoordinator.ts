/**
 * Single-flight token rotation, and the classification of a refresh that failed.
 *
 * The HTTP client owns *when* to rotate — a 401 on an authenticated request, once. This
 * module owns *how*: one exchange in flight at a time, an atomic write of both halves,
 * and the one distinction that decides whether a player keeps their session.
 *
 * ## Why one flight
 *
 * A screen has several requests in the air at once and they 401 together. Naively each
 * starts its own refresh: the first rotates the pair, the rest present a refresh token
 * the server has just retired, and the app signs the player out in the middle of a
 * working session. So the first caller creates the promise and every other caller awaits
 * that same one (docs/architecture.md Part 5).
 *
 * Single-flight alone is not enough, because 401s do not arrive together on a slow
 * connection — they arrive strung out over seconds. A straggler answering a token that
 * was already replaced would find no flight in progress and start a second rotation. So
 * a caller says which **generation** its request was sent with, and a 401 about a
 * superseded credential is answered with "retry", not with another rotation.
 *
 * ## Rejected is not unreachable
 *
 * | What happened                          | What it means                        |
 * |----------------------------------------|--------------------------------------|
 * | The server **rejected** the refresh     | The session is over. Tear it down.   |
 * | The refresh **never reached** a server  | We learned nothing. Keep everything. |
 *
 * The second row is the lift, the train, the tunnel. Destroying a valid session because
 * a request timed out costs the player their password and is the easy mistake to make
 * here — so anything that is not an authentication rejection preserves the session.
 *
 * **Nothing in this file logs.** The values passing through it are credentials.
 */

import { AppError } from '@/shared/errors';

import { endSession } from './session';
import type { Tokens } from './auth.types';
import { getGeneration, getRefreshToken, save } from './tokenManager';

/**
 * What the caller of a rotation may do next.
 *
 * Deliberately not `boolean`: "did it work" collapses the two failures into one, and
 * they demand opposite behaviour from the request that triggered them.
 */
export type RefreshOutcome =
  /** Current credentials are in place. Replay the request with them. */
  | 'retry'
  /** The server rejected our credentials. The session has already been torn down. */
  | 'session-ended'
  /** The rotation could not be completed. Credentials are untouched; do not replay. */
  | 'unavailable';

/**
 * The wire half of a rotation: a refresh token in, a new pair out, rejecting with an
 * `AppError` the way every other request does.
 *
 * Injected rather than imported. The path and its generated types belong to the auth
 * feature's `api/` layer — the only layer allowed to read `src/generated/` — and
 * `shared/` may never import a feature. This is the same inversion `configureHttp` and
 * the bootstrap sequence's `restoreSession` step already use: the feature registers, and
 * `shared/` never reaches up. The *policy* still lives here and only here.
 */
export type RefreshExchange = (refreshToken: string) => Promise<Tokens>;

let exchange: RefreshExchange | undefined;

/** Called once, during bootstrap, with the auth feature's wire adapter. */
export function configureRefresh(next: RefreshExchange): void {
  exchange = next;
}

/** Test seam, and the sign-out path: forget the adapter without tearing the module down. */
export function resetRefresh(): void {
  exchange = undefined;
  inFlight = undefined;
}

let inFlight: Promise<RefreshOutcome> | undefined;

/**
 * Rotate the session, once, however many callers ask at the same moment.
 *
 * `seen` is the generation the failing request carried. When the mirror has moved past
 * it, someone else has already rotated (or the session has ended) and this 401 is stale:
 * the answer is to retry against whatever is current, not to rotate again.
 */
export function refreshSession(seen: number): Promise<RefreshOutcome> {
  if (getGeneration() !== seen) return Promise.resolve('retry');

  if (inFlight === undefined) {
    inFlight = runRefresh();
    // Cleared on settle so the *next* genuine expiry can rotate again. `runRefresh`
    // resolves rather than rejects, so this never leaves an unhandled rejection.
    void inFlight.finally(() => {
      inFlight = undefined;
    });
  }

  return inFlight;
}

async function runRefresh(): Promise<RefreshOutcome> {
  const refreshToken = getRefreshToken();

  // No refresh token is not a failure to classify — there is simply no session to
  // rotate, and the 401 that got us here was correct.
  if (refreshToken === undefined || exchange === undefined) {
    await endSession('session-invalidated');
    return 'session-ended';
  }

  const startedAt = getGeneration();

  let tokens: Tokens;
  try {
    tokens = await exchange(refreshToken);
  } catch (error) {
    if (error instanceof AppError && error.invalidatesSession) {
      // The auth server said no: expired, revoked, or not recognised. This is the only
      // answer that ends a session.
      await endSession('session-invalidated');
      return 'session-ended';
    }

    // Unreachable, timed out, or the server itself broke. None of those say anything
    // about whether this session is valid, so nothing is destroyed.
    return 'unavailable';
  }

  // The session moved while we were waiting — the player signed out, or another path
  // cleared the credentials. Writing now would resurrect a session the app has already
  // left, leaving a live token on a device showing a sign-in screen.
  if (getGeneration() !== startedAt) return 'session-ended';

  // One write, both halves. A pair split across two writes is a session that cannot
  // recover from being interrupted between them.
  await save(tokens);
  return 'retry';
}
