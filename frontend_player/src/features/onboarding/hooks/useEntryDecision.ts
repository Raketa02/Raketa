/**
 * The entry gate, as a hook.
 *
 * **It reads the player and nothing else** ([ADR-0200](../../../../../docs/adr/0200-a-level-is-asked-where-play-begins.md)
 * §1, [#730](https://github.com/Raketa02/Raketa/issues/730)). It used to fire three reads in
 * parallel — the ratings, the unfinished run, and the player — because two of its destinations
 * turned on a rating and a run. Onboarding is a nickname and a profile now, and both facts route
 * nowhere, so both reads went with their destinations: a cold launch waits on one request, and the
 * group tabs read the ratings for themselves where a level is asked.
 *
 * The read is the player themselves, `GET /users/me`, which the app already asks for, already
 * keys, and already seeds from bootstrap when a stored session was validated — so on a warm launch
 * the gate costs nothing at all. **The nickname, the Player profile and the profiles ride on it**
 * (ADR-0199 §3, ADR-0185 §2). None of it is part of `SessionStatus`: making *has a Player profile*
 * a session state would block every cold launch on a network request, which is the opposite of
 * what the bootstrap sequence exists to avoid.
 *
 * **And the profile the phone remembers** (ADR-0185 §3, ADR-0188 §2,
 * [#518](https://github.com/Raketa02/Raketa/issues/518)). An account that runs a club's groups opens
 * in the profile it wore last, so for it the gate reads that — a local read, never the network — and
 * decides nothing before it has. Every other launch is not held for it; the read is made anyway, so
 * an account that gains a club while the gate is mounted finds it already settled, and the app it is
 * drawing is never blanked for it.
 *
 * **A failure has no safe default** — routing into the app is exactly the outcome the profile
 * branch exists to prevent — so it is *unavailable* ([ADR-0090](../../../../../docs/adr/0090-onboarding-per-player-checkpoint.md)).
 */

import { useCallback, useRef } from 'react';

import { named, useCurrentUser, useLastProfile } from '@/features/auth/types';
import { useSessionStatus } from '@/shared/lib/auth';
import type { AppError } from '@/shared/errors';

import { entryDestination, type EntryDestination } from '../domain/entryDecision';

/**
 * **Why the gate could not be read** — two states, and they are not the same sentence.
 *
 * `networkMode: 'online'` *pauses* a query rather than failing it. A paused query attempted
 * nothing, produced no `AppError`, and **resumes itself** the moment the connection is back —
 * so synthesising a failure for it, as this hook did, rendered *"We couldn't reach Raketa.
 * Check your connection and try again"* over a launch where nothing had been tried and there
 * was nothing to try again. Three screens in this app already said the true thing at their own
 * paused queries; this was the one site that converted the state into an error and said the
 * false one.
 */
export type EntryUnavailable =
  /** A read genuinely failed. There is something to say about it, and something to retry. */
  | { readonly kind: 'failed'; readonly error: AppError }
  /** Nothing was attempted. It will run itself on reconnect, and the sentence promises that. */
  | { readonly kind: 'offline' };

export type EntryDecision =
  /** Still asking. The caller renders nothing — not a spinner, and never a route tree. */
  | { readonly kind: 'pending' }
  /**
   * The gate could not be read. There is no safe default: sending a player with no profile
   * into the app skips the profile steps, and sending a set-up one into them asks them again.
   * So the player is told, and — where there is anything to retry — offered the retry.
   */
  | { readonly kind: 'unavailable'; readonly reason: EntryUnavailable; readonly retry: () => void }
  | EntryDestination;

export function useEntryDecision(): EntryDecision {
  const status = useSessionStatus();
  // An unauthenticated launch must not fire authenticated requests that can only 401 —
  // and a 401 at launch is exactly what would make the token rotation chase a session
  // that never existed.
  const enabled = status === 'authenticated';

  // Whose read this is, rather than a read of this gate's own: the auth feature owns the
  // authenticated player, and a second query against the same route under a second key
  // would be two requests answering one question and two chances to disagree.
  const user = useCurrentUser();
  // **The profile the phone remembers** (ADR-0188 §2) — a local read, and the gate waits for it for
  // an account that runs a club's groups: one that wore its administrator profile last must never
  // draw the player's app first. An account that runs none has nothing else to have worn, so its
  // launch never waits — but the read is still made for it, so that an account gaining a club under
  // a mounted gate (an invitation accepted over the app) finds it long settled, rather than sending
  // the gate back to *pending* and unmounting the app it is drawing.
  const runsAClub = (user.data?.profiles.administers.length ?? 0) > 0;
  const last = useLastProfile(user.data?.id, enabled);
  const lastUnread = runsAClub && !last.settled;

  // **Whether this mount set out to replace the player read: was it stale when it began.**
  // Taken once, on the first render, because *stale at mount* is a fact about the mount and
  // not about the render — it bounds what counts as pending below.
  const staleAtMount = useRef(user.isStale).current;

  const refetchUser = user.refetch;
  const retry = useCallback(() => {
    void refetchUser();
  }, [refetchUser]);

  // Nothing is decided for an account with two profiles until the phone has said which it wore.
  if (lastUnread) return { kind: 'pending' };

  if (user.error !== null) {
    return {
      kind: 'unavailable',
      reason: { kind: 'failed', error: user.error as AppError },
      retry,
    };
  }

  // Offline, with nothing cached to decide from. `networkMode: 'online'` *pauses* a
  // query rather than failing it, so without this branch a launch on a dead connection
  // renders nothing at all — for as long as the connection stays dead. It is stated as
  // **paused**, not converted into a `networkUnavailable()`: a synthesised error would claim
  // something was tried and failed, and offer a *Try again* for a query that resumes itself.
  if (user.fetchStatus === 'paused' && !user.isSuccess) {
    return { kind: 'unavailable', reason: { kind: 'offline' }, retry };
  }

  // `isSuccess`, not a truthiness check on the data.
  if (!user.isSuccess) return { kind: 'pending' };

  // **A read this mount is in the middle of replacing is not an answer.**
  //
  // The gate's read is unobserved for the whole of onboarding, and an invalidated query with no
  // observers does not refetch — it is marked stale and waits for a mount. So the mount that ends
  // the profile steps can find it still holding the launch's answer, and Query hands that back as
  // `success` while the replacement is in flight; acting on it would redirect back into the steps,
  // which unmounts this layout and cancels the refetch through its `signal`, so the stale copy is
  // never replaced. The bound is **stale when this gate mounted, and not yet answered since** —
  // both halves: waiting on *any* fetch would blank the authenticated tree on every foreground
  // refetch, and waiting on `isFetchedAfterMount` alone blanked it once per launch on a device,
  // because bootstrap seeds the player and a fresh seed is never fetched by this mount. A paused
  // query is not covered: a launch with a cached answer and no connection routes from what it holds.
  const beingReplaced = staleAtMount && user.isFetching && !user.isFetchedAfterMount;
  if (beingReplaced) return { kind: 'pending' };

  return entryDestination({
    // A nickname (ADR-0199 §3): an account an Invitation opened holds none either, and the
    // naming is still owed once it plays.
    named: named(user.data),
    hasPlayerProfile: user.data.hasPlayerProfile,
    profiles: user.data.profiles,
    ...(last.choice === undefined ? {} : { lastProfile: last.choice }),
  });
}
