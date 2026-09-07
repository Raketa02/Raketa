/**
 * The entry gate, as a hook.
 *
 * **The three reads are fired in parallel**, which is not a performance preference: they
 * answer different questions — is a *run* unfinished, does a *rating* exist, does a *Player
 * profile* exist — and sequencing them would make every cold launch pay for the round trips
 * one after the other before anything renders.
 *
 * None of them is part of `SessionStatus`. Making "has a rating" a session state would block
 * every cold launch on a network request, which is the opposite of what the bootstrap
 * sequence exists to avoid, and it would be a fourth state nothing else needs.
 *
 * **The third read is the player themselves**, and it is deliberately not a fourth endpoint:
 * `has_player_profile` is served on `GET /users/me`, which the app already asks for, already
 * keys, and already seeds from bootstrap when a stored session was validated. So on a warm
 * launch the profile branch costs nothing at all, and on a cold one it costs a request the
 * app was going to make anyway.
 *
 * **All three must answer before the gate does.** A launch that can read ratings but not the
 * player has no safe default — routing into the app is exactly the outcome the fourth branch
 * exists to prevent — so a failure on any of them is the same *unavailable* it already was
 * for the other two ([ADR-0090](../../../../../docs/adr/0090-onboarding-per-player-checkpoint.md)).
 */

import { useQuery } from '@tanstack/react-query';
import { useCallback } from 'react';

import { useCurrentUser } from '@/features/auth/types';
import { useSessionStatus } from '@/shared/lib/auth';
import type { AppError } from '@/shared/errors';

import { entryDestination, type EntryDestination } from '../domain/entryDecision';
import { useDeferredRuns } from '../store/deferredRuns.store';
import { findRunInProgress } from '../use-cases/findRunInProgress';
import { listRatings } from '../use-cases/listRatings';

import { onboardingKeys } from './onboardingKeys';

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
   * The gate could not be read. There is no safe default: sending an unrated player into
   * the app skips onboarding, and sending a rated one into onboarding re-rates them. So
   * the player is told, and — where there is anything to retry — offered the retry.
   */
  | { readonly kind: 'unavailable'; readonly reason: EntryUnavailable; readonly retry: () => void }
  | EntryDestination;

export function useEntryDecision(): EntryDecision {
  const status = useSessionStatus();
  // An unauthenticated launch must not fire authenticated requests that can only 401 —
  // and a 401 at launch is exactly what would make the token rotation chase a session
  // that never existed.
  const enabled = status === 'authenticated';
  // Not server data and never mirrored from it: the run really is unfinished, and this
  // is the player's decision to leave it that way until the next launch.
  const deferredRunIds = useDeferredRuns((state) => state.deferred);

  // Whose read this is, rather than a read of this gate's own: the auth feature owns the
  // authenticated player, and a second query against the same route under a second key
  // would be two requests answering one question and two chances to disagree.
  const user = useCurrentUser();

  const ratings = useQuery({
    queryKey: onboardingKeys.ratings(),
    queryFn: ({ signal }) => listRatings({ signal }),
    enabled,
  });

  const run = useQuery({
    queryKey: onboardingKeys.runInProgress(),
    // `?? null` is load-bearing. TanStack Query reserves `undefined` for "nothing
    // cached" and rejects it as data, so a query that answered "no run in progress" by
    // returning `undefined` would be recorded as a failed fetch — and the gate would sit
    // pending forever for the commonest player there is. `null` is the value that means
    // *asked, and there is none*.
    queryFn: ({ signal }) => findRunInProgress({ signal }).then((found) => found ?? null),
    enabled,
  });

  const refetchRatings = ratings.refetch;
  const refetchRun = run.refetch;
  const refetchUser = user.refetch;
  const retry = useCallback(() => {
    void refetchRatings();
    void refetchRun();
    void refetchUser();
  }, [refetchRatings, refetchRun, refetchUser]);

  const error = (ratings.error ?? run.error ?? user.error) as AppError | null;
  if (error !== null) return { kind: 'unavailable', reason: { kind: 'failed', error }, retry };

  // Offline, with nothing cached to decide from. `networkMode: 'online'` *pauses* a
  // query rather than failing it, so without this branch a launch on a dead connection
  // renders nothing at all — for as long as the connection stays dead. Saying so is the
  // difference between an app that is waiting and an app that looks broken.
  //
  // It is stated as **paused**, not converted into a `networkUnavailable()`. A synthesised
  // error would be a claim that something was tried and failed, and the screen would then
  // offer a *Try again* for a query that resumes itself — which is the one control on that
  // screen that would do nothing.
  const paused =
    ratings.fetchStatus === 'paused' ||
    run.fetchStatus === 'paused' ||
    user.fetchStatus === 'paused';
  if (paused && !(ratings.isSuccess && run.isSuccess && user.isSuccess)) {
    return { kind: 'unavailable', reason: { kind: 'offline' }, retry };
  }

  // `isSuccess`, not a truthiness check on the data: an empty ratings list and a `null`
  // run are both real answers, and both are falsy.
  if (!ratings.isSuccess || !run.isSuccess || !user.isSuccess) return { kind: 'pending' };

  // **A read this mount is in the middle of replacing is not an answer.**
  //
  // The gate's three queries are unobserved for the whole of onboarding, and an
  // invalidated query with no observers does not refetch — it is marked stale and waits
  // for a mount. So the mount that ends onboarding finds all three still holding the
  // launch's answers, and Query hands those back as `success` while the replacement is in
  // flight. The launch's answer is *"no ratings"*, and acting on it redirects into
  // `(onboarding)` — which unmounts this layout, and unmounting cancels the refetch
  // through the `signal` every one of these queries passes to `fetch`. The stale copy is
  // then never replaced, so the next attempt reads it again: a player who has finished
  // onboarding is sent back to welcome every time, for as long as the entry lives — which
  // is what was happening on a device while every suite here stayed green, because
  // `expo-router/testing-library` installs fake timers and Query's five-minute `gcTime`
  // therefore expires the entry between the two mounts. The test below seeds it instead.
  //
  // The bound is `isFetchedAfterMount`, and it is what keeps this from being the opposite
  // bug. Waiting on *any* fetch would blank the authenticated tree every time a foreground
  // refetch ran; waiting only until each read has answered **once since this gate mounted**
  // costs the round trip the gate was already making and nothing after it.
  //
  // A paused query is deliberately not covered: it is not fetching, so a launch with a
  // cached answer and no connection still routes from what it holds rather than rendering
  // nothing until the connection returns.
  const beingReplaced =
    (ratings.isFetching && !ratings.isFetchedAfterMount) ||
    (run.isFetching && !run.isFetchedAfterMount) ||
    (user.isFetching && !user.isFetchedAfterMount);
  if (beingReplaced) return { kind: 'pending' };

  return entryDestination({
    ratings: ratings.data,
    runInProgress: run.data ?? undefined,
    deferredRunIds,
    hasPlayerProfile: user.data.hasPlayerProfile,
  });
}
