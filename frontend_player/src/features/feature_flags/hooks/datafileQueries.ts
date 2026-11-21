/**
 * **The two datafile reads** — each one's key, its read and its lifetime, as one thing, so the
 * hook that runs them and the gate that looks them up cannot disagree about either.
 *
 * Neither is ever *waited on*. Nothing renders a spinner for a feature flag: a gate reads whatever
 * is in hand when it mounts (`useFeatureOnMount`), and what is in hand improves underneath it.
 */

import { queryOptions } from '@tanstack/react-query';

import type { AppEnvironment } from '@/shared/config/env';
import type { AppError } from '@/shared/errors';

import type { Datafile } from '../domain/featureFlags';
import { refreshDatafile } from '../use-cases/refreshDatafile';
import { savedDatafile } from '../use-cases/savedDatafile';

import { featureFlagKeys } from './featureFlagKeys';

/**
 * **This session's datafile** — fetched at launch, and again **every** time the app returns to the
 * foreground (ADR-0206 §6), which is how a merged toggle reaches a running app.
 *
 * - `staleTime: Infinity` with `refetchOnWindowFocus: 'always'` is that sentence in Query's terms:
 *   nothing but a return to the front refetches it — not a second observer, not a remount — and
 *   every return does. A 30-second window like the app default would drop the foreground after a
 *   short trip to another app, which is exactly the trip a developer toggling a feature flag
 *   makes.
 * - **`retry: false`**, against the app default. A failed read already has its answer in hand —
 *   the saved datafile, or the code defaults — and its next attempt is already scheduled: the next
 *   foreground. Retrying on a timer spends a player's data on a read nobody is waiting for, on the
 *   one path where a later answer changes nothing until a screen mounts again. A refusal
 *   (`refreshDatafile`) is terminal anyway.
 * - A failure keeps the last good `data`, which is Query's own behaviour and ADR-0206 §10's rule:
 *   a datafile refused mid-session leaves the one fetched earlier in use.
 */
export function freshDatafileQuery(environment: AppEnvironment) {
  return queryOptions<Datafile, AppError>({
    queryKey: featureFlagKeys.fresh(environment),
    queryFn: ({ signal }) => refreshDatafile(environment, { signal }),
    staleTime: Infinity,
    refetchOnWindowFocus: 'always',
    retry: false,
  });
}

/**
 * **The saved datafile** — read from the device once per session, at launch.
 *
 * `networkMode: 'always'` because it is not a network read: under the app default it would be
 * *paused* while offline, which is precisely when it is the only datafile the app can have. It is
 * never re-read — the fresh datafile outranks it from the moment one arrives, and the one saved by
 * that arrival is next launch's.
 */
export function savedDatafileQuery(environment: AppEnvironment) {
  return queryOptions<Datafile | null, AppError>({
    queryKey: featureFlagKeys.saved(environment),
    queryFn: () => savedDatafile(environment),
    networkMode: 'always',
    staleTime: Infinity,
    refetchOnWindowFocus: false,
    refetchOnReconnect: false,
    retry: false,
  });
}
