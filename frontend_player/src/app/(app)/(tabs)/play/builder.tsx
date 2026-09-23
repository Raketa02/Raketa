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
 *
 * **Closed while `find_a_game` is off**
 * ([ADR-0180](../../../../../../docs/adr/0180-a-feature-is-turned-on-by-a-pull-request-and-decided-on-the-device.md)
 * §7): Find a game is not there to have started a search, so whatever reached this route — a
 * stale link, a push from before the toggle — lands on Play's root instead of half of a flow.
 * Read once, when the route mounts, like every gate. Fill-the-seat's builder is not this route;
 * it is `chats/challenge/[challengeId]/fill`, and nothing there reads the flag.
 */

import { Redirect, useLocalSearchParams } from 'expo-router';

import { useFeatureOnMount } from '@/features/feature_flags/types';
import { BuilderScreen, parseBuilderRouteParams } from '@/features/play/types';

export default function BuilderRoute() {
  const params = parseBuilderRouteParams(useLocalSearchParams());
  const findAGame = useFeatureOnMount('find_a_game');

  if (params === undefined || !findAGame) return <Redirect href="/play" />;

  return <BuilderScreen arrivalSearchId={params.search} />;
}
