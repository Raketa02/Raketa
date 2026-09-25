/**
 * Starting and ending a session — the transitions, as system operations.
 *
 * Sign-out is **not** a `router.replace`. Route replacement clears nothing: it leaves
 * the previous player's cached profile, bookings and matches sitting in memory for
 * whoever signs in next on the same device. That is a data leak, and step 4 below is a
 * privacy control rather than tidiness. See docs/architecture.md Part 5.
 *
 * The redirect is a *consequence* of the status change, not part of it: the guard in
 * `(app)/_layout.tsx` reacts to `unauthenticated`. That is what keeps every path out of
 * a session — a rejected refresh, a chosen sign-out, a failed launch validation — going
 * through one sequence instead of three.
 */

import { forgetPhonePreferences } from '@/shared/lib/preferences';
import { queryClient } from '@/shared/lib/query-client';

import { setSessionStatus } from './authSession';
import type { SignOutReason, Tokens } from './auth.types';
import { clear, save } from './tokenManager';

/**
 * Persist credentials and open the session.
 *
 * Tokens are written **before** the status flips. The other order renders the
 * authenticated tree against a token manager that has not been told about the
 * credentials yet, and the first request of the new session goes out unauthenticated.
 */
export async function beginSession(tokens: Tokens): Promise<void> {
  await save(tokens);
  setSessionStatus('authenticated');
}

/**
 * Close the session and leave nothing behind.
 *
 * The server-side revoke is deliberately *not* here: it speaks the wire, so it belongs
 * to the auth feature's sign-out use-case, which calls it first and then calls this. It
 * is also best-effort — a revoke that fails offline must not strand a player in an app
 * they asked to leave, so local credentials are destroyed either way.
 *
 * Safe to call twice, and it has to be: several failing requests can each conclude the
 * session is over. The status machine ignores a repeat transition, so the second caller
 * clears already-clear state and notifies nobody.
 */
export async function endSession(reason: SignOutReason): Promise<void> {
  void reason; // Recorded by the caller; the sequence is identical either way.

  // 1. Credentials first — in memory and on disk — so nothing in flight can be retried
  //    with a token that is supposed to be gone.
  await clear();

  // 2. The status change, and it may not wait for anything.
  //
  //    **This runs inside a query more often than not.** The ordinary way a session ends
  //    is a 401 arriving in a `queryFn`, going to the refresh coordinator, and coming back
  //    rejected — so the teardown executes while the query that triggered it is still in
  //    flight, and step 3 cancels that very query. Awaiting the cancellation here would be
  //    waiting for this function's own caller to return, which it cannot do until this
  //    returns.
  //
  //    The state that left behind was worse than either end of the transition: no
  //    credentials, but a status still saying `authenticated`. Every later request then
  //    goes out with no `Authorization` header and is refused — and the rotation cannot
  //    even classify that 401, because there is no credential for it to be about. The
  //    player is shown a retry for a session that no longer exists, and pressing it
  //    re-runs the same headerless request forever.
  setSessionStatus('unauthenticated');

  // 3. Stop work still running against the old session, then drop the cache — the privacy
  //    step, and the reason sign-out is not a `router.replace`. Ordered against each other
  //    so an in-flight response cannot repopulate what was just cleared, and deliberately
  //    **not awaited**, for the reason in step 2. The `catch` is what guarantees the clear
  //    still happens when a cancellation rejects.
  void queryClient
    .cancelQueries()
    .catch(() => undefined)
    .then(() => queryClient.clear());

  // 4. Forget what the phone kept for this person — the Play segment, the last sport and, later,
  //    the last profile (ADR-0188 §3). The same privacy step as 3, one store over: the next person to
  //    sign in on this phone starts from the defaults. Awaited, unlike 3, because it waits on no
  //    query and so cannot be waiting on this function's own caller; it never rejects.
  await forgetPhonePreferences();
}
