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
import { networkUnavailable, type AppError } from '@/shared/errors';

import { entryDestination, type EntryDestination } from '../domain/entryDecision';
import { useDeferredRuns } from '../store/deferredRuns.store';
import { findRunInProgress } from '../use-cases/findRunInProgress';
import { listRatings } from '../use-cases/listRatings';

import { onboardingKeys } from './onboardingKeys';

export type EntryDecision =
  /** Still asking. The caller renders nothing — not a spinner, and never a route tree. */
  | { readonly kind: 'pending' }
  /**
   * The gate could not be read. There is no safe default: sending an unrated player into
   * the app skips onboarding, and sending a rated one into onboarding re-rates them. So
   * the player is told, and offered the retry.
   */
  | { readonly kind: 'unavailable'; readonly error: AppError; readonly retry: () => void }
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
  if (error !== null) return { kind: 'unavailable', error, retry };

  // Offline, with nothing cached to decide from. `networkMode: 'online'` *pauses* a
  // query rather than failing it, so without this branch a launch on a dead connection
  // renders nothing at all — for as long as the connection stays dead. Saying so is the
  // difference between an app that is waiting and an app that looks broken.
  const paused =
    ratings.fetchStatus === 'paused' ||
    run.fetchStatus === 'paused' ||
    user.fetchStatus === 'paused';
  if (paused && !(ratings.isSuccess && run.isSuccess && user.isSuccess)) {
    return { kind: 'unavailable', error: networkUnavailable(), retry };
  }

  // `isSuccess`, not a truthiness check on the data: an empty ratings list and a `null`
  // run are both real answers, and both are falsy.
  if (!ratings.isSuccess || !run.isSuccess || !user.isSuccess) return { kind: 'pending' };

  return entryDestination({
    ratings: ratings.data,
    runInProgress: run.data ?? undefined,
    deferredRunIds,
    hasPlayerProfile: user.data.hasPlayerProfile,
  });
}
