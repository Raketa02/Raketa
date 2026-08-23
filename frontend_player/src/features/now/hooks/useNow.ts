/**
 * The composed screen, and the three of `ADR-0054`'s four asks that are Query's.
 *
 * Every option below is one of the four, or the refusal of a fifth:
 *
 * | Option | Which ask |
 * | --- | --- |
 * | the first mount with nothing cached | **arrival** — a cold open |
 * | `refetchOnWindowFocus: 'always'` | **arrival** — the app foregrounding |
 * | `refetch()`, through `RefreshControl` | **pull** |
 * | invalidating `nowKeys` | **an action** |
 * | `staleTime: Infinity` + `refetchOnMount: false` | *not* an ask — popping back off a route |
 * | `refetchOnReconnect: false` | *not* an ask — signal returning is not the player asking |
 *
 * **`'always'`, not `true`.** `true` still respects `staleTime`, and this query's
 * staleness is deliberately infinite — so a plain `true` would make foregrounding
 * a no-op and the first screen of a session the least trustworthy one, which is
 * the exact failure `ADR-0054` writes the arrival rule to prevent.
 *
 * **`staleTime: Infinity` is not a claim that the answer stays true.** It is how
 * *nothing but the four asks* refetches. The screen never admits staleness anyway
 * (`ADR-0038` Rule IV, kept by `ADR-0054`): it either shows what is true or shows
 * that it is fetching.
 *
 * **`gcTime: Infinity` is what makes the row above it mean anything.** The app's
 * default is five minutes, and under it a player who spends six minutes elsewhere
 * in the app comes back to a *shimmer* — the cold-open treatment, on a screen that
 * was never cold. `ADR-0054` shows the shimmer for one reason: *there is nothing
 * here yet*. Keeping the composed screen for the life of the process is what keeps
 * that sentence true, and it restores nothing across a launch, because nothing is
 * written anywhere: the process ending is the whole of the eviction policy, and
 * signing out clears the cache outright.
 */

import { useQuery } from '@tanstack/react-query';

import type { AppError } from '@/shared/errors';

import type { ComposedScreen } from '../domain/ComposedScreen';
import type { SportFilter } from '../mappers/codes';
import { composeNow } from '../use-cases/composeNow';

import { nowKeys } from './nowKeys';

export function useNow(sport: SportFilter) {
  return useQuery<ComposedScreen, AppError>({
    queryKey: nowKeys.screen(sport),
    queryFn: ({ signal }) => composeNow({ sport, signal }),
    staleTime: Infinity,
    gcTime: Infinity,
    refetchOnMount: false,
    refetchOnWindowFocus: 'always',
    refetchOnReconnect: false,
  });
}
