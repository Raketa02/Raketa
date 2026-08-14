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

import { queryClient } from "@/shared/lib/query-client";

import { setSessionStatus } from "./authSession";
import type { SignOutReason, Tokens } from "./auth.types";
import { clear, save } from "./tokenManager";

/**
 * Persist credentials and open the session.
 *
 * Tokens are written **before** the status flips. The other order renders the
 * authenticated tree against a token manager that has not been told about the
 * credentials yet, and the first request of the new session goes out unauthenticated.
 */
export async function beginSession(tokens: Tokens): Promise<void> {
  await save(tokens);
  setSessionStatus("authenticated");
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

  // 2. Stop work that is still running against the old session before dropping the
  //    cache, or an in-flight response repopulates what was just cleared.
  await queryClient.cancelQueries();

  // 3. The privacy step.
  queryClient.clear();

  // 4. The status change, which the routing guard turns into a redirect.
  setSessionStatus("unauthenticated");
}
