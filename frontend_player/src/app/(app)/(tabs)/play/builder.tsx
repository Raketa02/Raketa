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
 * **Closed to a bare link while `classic_play` is off, never to a search under way**
 * ([ADR-0180](../../../../../../docs/adr/0180-a-feature-is-turned-on-by-a-pull-request-and-decided-on-the-device.md)
 * §7). With the flag off Play's root is not Find a game, so nothing there can start a search — and
 * a link to this route with no search behind it lands on Play's root rather than on an empty court.
 * A search the player already ran is let through: the toggle reached them mid-journey, and a
 * gated screen is never pulled out from under anybody (PRD #476 story 21). The flag is read once,
 * when the route mounts, like every gate. Fill-the-seat's builder is not this route; it is
 * `chats/challenge/[challengeId]/fill`, and nothing there reads the flag.
 */

import { Redirect, useLocalSearchParams } from 'expo-router';

import { useFeatureOnMount } from '@/features/feature_flags/types';
import { BuilderScreen, parseBuilderRouteParams, useSearchWasRun } from '@/features/play/types';

export default function BuilderRoute() {
  const params = parseBuilderRouteParams(useLocalSearchParams());
  const classicPlay = useFeatureOnMount('classic_play');
  const searchWasRun = useSearchWasRun(params?.search);

  if (params === undefined) return <Redirect href="/play" />;
  if (!classicPlay && !searchWasRun) return <Redirect href="/play" />;

  return <BuilderScreen arrivalSearchId={params.search} />;
}
