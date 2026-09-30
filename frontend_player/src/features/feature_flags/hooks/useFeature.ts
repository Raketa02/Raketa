/**
 * **A flag followed, for chrome that outlives every screen** — the tab bar's read of
 * `classic_play` ([#550](https://github.com/Raketa02/Raketa/issues/550)).
 *
 * A gated *screen* reads its flag once, when it mounts (`useFeatureOnMount`, ADR-0180 §7), so
 * nobody has a screen pulled out from under them. The bar is not a screen: it is mounted once,
 * with the signed-in app, **before either datafile has been read** — the saved one is an
 * AsyncStorage read that answers a tick later, the fresh one a network read after that — and it
 * stays mounted for the session. Read once, it would answer the code default on every launch and a
 * tester's Classic play would never reach the bar. So this answers again whenever a datafile lands:
 * at launch, and at every return to the foreground — which is ADR-0180's *a toggle reaches a
 * running app at its next cold start or foreground*, and no sooner. What changes is which columns
 * the bar draws; the screen under it is never swapped.
 *
 * **It observes the two reads and runs neither.** `useFeatureDatafile` owns them — when they run,
 * how often, what a failure keeps — so these observers are disabled: they are told when the cache
 * changes and never fetch, so a second observer adds no request and no refetch on focus. The player
 * is read from the cache and not observed, as the gate reads it, because an observer on the
 * player's own read would refetch `/users/me` when the bar mounts.
 */

import { useQuery, useQueryClient } from '@tanstack/react-query';

import { currentUserQuery } from '@/features/auth/types';
import { getEnv } from '@/shared/config/env';

import type { FeatureKey } from '../domain/featureFlags';
import { isFeatureEnabled } from '../use-cases/isFeatureEnabled';

import { freshDatafileQuery, savedDatafileQuery } from './datafileQueries';
import { flagContextOf } from './useFeatureOnMount';

export function useFeature(feature: FeatureKey): boolean {
  const client = useQueryClient();
  const { environment } = getEnv();

  const fresh = useQuery({ ...freshDatafileQuery(environment), enabled: false }).data;
  const cached = useQuery({ ...savedDatafileQuery(environment), enabled: false }).data;
  const player = client.getQueryData(currentUserQuery().queryKey);

  return isFeatureEnabled(feature, {
    fresh,
    cached,
    context: player === undefined ? undefined : flagContextOf(player),
  });
}
