/**
 * The pool route — where every remedy the court states sends the player.
 *
 * A sibling of the builder rather than a screen behind it in the file tree, and pushed over it
 * at runtime: the court **pops** back, which is what lets the pending seat replacement be
 * route-local and need no clearing rule
 * ([#228](https://github.com/Raketa02/Raketa/issues/228) §6).
 *
 * **Both params are untrusted.** The search becomes `ForecastRequest.search_id` and a Query
 * key, and the seat decides whether an add **replaces** somebody — so neither is read before it
 * is checked. A link that does not survive that has no list to draw and no seat to fill, which
 * is not a pool but Play's own start.
 *
 * **Closed to a bare link while `find_a_game` is off, never to a search under way**
 * ([ADR-0180](../../../../../../docs/adr/0180-a-feature-is-turned-on-by-a-pull-request-and-decided-on-the-device.md)
 * §7) — the builder's rule, for the builder's reasons. It matters twice over here, because this
 * one route serves two journeys: Find a game's builder pushes it, and so does the builder under a
 * challenge's fill-the-seat, which is not behind the flag. Both open it on a search the player
 * already ran, so both are let through; only a link with no search behind it lands on Play's
 * root. The flag is read once, when the route mounts, like every gate; the record cannot come or
 * go under it, because the act that minted the search wrote it before the pool could be pushed.
 */

import { Redirect, useLocalSearchParams } from 'expo-router';

import { useFeatureOnMount } from '@/features/feature_flags/types';
import { PoolScreen, parsePoolRouteParams, useSearchWasRun } from '@/features/play/types';

export default function PoolRoute() {
  const params = parsePoolRouteParams(useLocalSearchParams());
  const findAGame = useFeatureOnMount('find_a_game');
  const searchWasRun = useSearchWasRun(params?.search);

  if (params === undefined) return <Redirect href="/play" />;
  if (!findAGame && !searchWasRun) return <Redirect href="/play" />;

  return <PoolScreen arrivalSearchId={params.search} arrivalSeat={params.seat} />;
}
