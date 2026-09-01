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
 */

import { Redirect, useLocalSearchParams } from 'expo-router';

import { PoolScreen, parsePoolRouteParams } from '@/features/play/types';

export default function PoolRoute() {
  const params = parsePoolRouteParams(useLocalSearchParams());

  if (params === undefined) return <Redirect href="/play" />;

  return <PoolScreen arrivalSearchId={params.search} arrivalSeat={params.seat} />;
}
