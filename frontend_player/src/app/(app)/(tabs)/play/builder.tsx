/**
 * **The builder** — the second Play screen, and the one a finished search lands on.
 *
 * A sibling of `play/index.tsx` rather than a screen behind it: Find a game stays underneath,
 * so the platform's own back gesture comes back out of the court, and the bar's active column
 * is read off the first path segment and stays on ⚡Play throughout.
 *
 * **The origin search arrives as a param and is untrusted.** It becomes
 * `ForecastRequest.search_id` and a Query key, so it is validated before anything reads it — a
 * link that does not survive that has no origin at all, which is not a builder but Play's own
 * start.
 */

import { Redirect, useLocalSearchParams } from 'expo-router';

import { BuilderScreen, parseBuilderRouteParams } from '@/features/play/types';

export default function BuilderRoute() {
  const params = parseBuilderRouteParams(useLocalSearchParams());

  if (params === undefined) return <Redirect href="/play" />;

  return <BuilderScreen arrivalSearchId={params.search} />;
}
