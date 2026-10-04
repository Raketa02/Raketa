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
 * app was going to make anyway. **The name rides on the same read** — the gate's first
 * destination ([ADR-0171](../../../../../docs/adr/0171-a-player-has-a-name-and-a-nickname-and-the-name-is-what-is-said.md)
 * §3) costs nothing more than the fourth did.
 *
 * **Except for an account that does not act as a player.** Its profiles are the gate's first read
 * (ADR-0185 §3), and they ride on the player read too — so the moment that read answers *only an
 * administrator*, or *no profile at all*, the gate answers the administrator area or *Start
 * playing*'s first step and waits for nothing else. The two player reads are not even asked for
 * once the player read says so: an account that has not asked to play owes the gate no rating and
 * no run.
 *
 * **And the profile the phone remembers** (ADR-0185 §3, ADR-0188 §2,
 * [#518](https://github.com/Raketa02/Raketa/issues/518)). An account that runs a club's groups opens
 * in the profile it wore last, so for it the gate reads that — a local read, never the network — and
 * decides nothing before it has. Every other launch is not held for it; the read is made anyway, so
 * an account that gains a club while the gate is mounted finds it already settled, and the app it is
 * drawing is never blanked for it.
 *
 * **Otherwise all three must answer before the gate does.** A launch that can read ratings but not the
 * player has no safe default — routing into the app is exactly the outcome the fourth branch
 * exists to prevent — so a failure on any of them is the same *unavailable* it already was
 * for the other two ([ADR-0090](../../../../../docs/adr/0090-onboarding-per-player-checkpoint.md)).
 */

import { useQuery } from '@tanstack/react-query';
import { useCallback, useRef } from 'react';

import { namedInFull, useCurrentUser, useLastProfile } from '@/features/auth/types';
import { useSessionStatus } from '@/shared/lib/auth';
import type { AppError } from '@/shared/errors';

import {
  entryDestination,
  profileDestination,
  type EntryDestination,
} from '../domain/entryDecision';
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
  // **The profile the phone remembers** (ADR-0188 §2) — a local read, and the gate waits for it for
  // an account that runs a club's groups: one that wore its administrator profile last must never
  // draw the player's app first. An account that runs none has nothing else to have worn, so its
  // launch never waits — but the read is still made for it, so that an account gaining a club under
  // a mounted gate (an invitation accepted over the app) finds it long settled, rather than sending
  // the gate back to *pending* and unmounting the app it is drawing.
  const runsAClub = (user.data?.profiles.administers.length ?? 0) > 0;
  const last = useLastProfile(user.data?.id, enabled);
  const lastUnread = runsAClub && !last.settled;
  // Read off the player once it has answered; until then nothing is known, and the two player
  // reads go out beside it as they always have — but never for an account that does not play.
  const byProfile =
    user.data === undefined || lastUnread
      ? undefined
      : profileDestination(user.data.profiles, last.choice);
  const playerReadsEnabled =
    enabled && byProfile === undefined && (user.data?.profiles.actsAsPlayer ?? true);

  const ratings = useQuery({
    queryKey: onboardingKeys.ratings(),
    queryFn: ({ signal }) => listRatings({ signal }),
    enabled: playerReadsEnabled,
  });

  const run = useQuery({
    queryKey: onboardingKeys.runInProgress(),
    // `?? null` is load-bearing. TanStack Query reserves `undefined` for "nothing
    // cached" and rejects it as data, so a query that answered "no run in progress" by
    // returning `undefined` would be recorded as a failed fetch — and the gate would sit
    // pending forever for the commonest player there is. `null` is the value that means
    // *asked, and there is none*.
    queryFn: ({ signal }) => findRunInProgress({ signal }).then((found) => found ?? null),
    enabled: playerReadsEnabled,
  });

  // **Which reads this mount set out to replace: the ones that were stale when it began.**
  // Taken once, on the first render, because *stale at mount* is a fact about the mount and
  // not about the render — it is read below, where it bounds what counts as pending. A
  // read that was fresh when the gate mounted was not sent for by the gate, and no later
  // refetch of it is this mount's business.
  const staleAtMount = useRef({
    ratings: ratings.isStale,
    run: run.isStale,
    user: user.isStale,
  }).current;

  const refetchRatings = ratings.refetch;
  const refetchRun = run.refetch;
  const refetchUser = user.refetch;
  const retry = useCallback(() => {
    void refetchRatings();
    void refetchRun();
    void refetchUser();
  }, [refetchRatings, refetchRun, refetchUser]);

  // **The profiles first** (ADR-0185 §3): an account that does not act as a player is routed by
  // the player read alone, the moment it answers — unless this mount is replacing that read, for
  // the reason `beingReplaced` below gives.
  const userBeingReplaced = staleAtMount.user && user.isFetching && !user.isFetchedAfterMount;
  if (byProfile !== undefined && !userBeingReplaced) return byProfile;
  // Nothing is decided for an account with two profiles until the phone has said which it wore.
  if (lastUnread) return { kind: 'pending' };

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
  // The bound is **stale when this gate mounted, and not yet answered since** — both halves,
  // and each is what keeps this from being the opposite bug. Waiting on *any* fetch would
  // blank the authenticated tree every time a foreground refetch ran. Waiting on
  // `isFetchedAfterMount` alone was the first cut, and it blanked the tree once per launch on
  // a device while every suite stayed green: bootstrap **seeds** the player into the cache,
  // so this gate's own read of them was fresh at mount and never fetched — the flag stayed
  // false — and thirty seconds later the first screen to mount `useCurrentUser()` refetched
  // the stale seed, which this gate took for its own replacement and answered `pending`,
  // unmounting the shell for the length of the round trip and remounting it on a fresh
  // stack, which opened on whatever that stack's first route was. Waiting only on the reads
  // this mount actually sent for costs the round trip the gate was already making and
  // nothing after it.
  //
  // A paused query is deliberately not covered: it is not fetching, so a launch with a
  // cached answer and no connection still routes from what it holds rather than rendering
  // nothing until the connection returns.
  const beingReplaced =
    (staleAtMount.ratings && ratings.isFetching && !ratings.isFetchedAfterMount) ||
    (staleAtMount.run && run.isFetching && !run.isFetchedAfterMount) ||
    userBeingReplaced;
  if (beingReplaced) return { kind: 'pending' };

  return entryDestination({
    // A name *and* a nickname (ADR-0185 §4): an account an Invitation opened holds the club's
    // name and no handle, and the naming is still owed once it plays.
    namedInFull: namedInFull(user.data),
    ratings: ratings.data,
    runInProgress: run.data ?? undefined,
    deferredRunIds,
    hasPlayerProfile: user.data.hasPlayerProfile,
    profiles: user.data.profiles,
    ...(last.choice === undefined ? {} : { lastProfile: last.choice }),
  });
}
