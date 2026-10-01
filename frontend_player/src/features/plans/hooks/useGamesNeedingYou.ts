/**
 * **How many of your games need you** — the count on Home's column of the tab bar
 * ([#550](https://github.com/Raketa02/Raketa/issues/550),
 * [the mechanics §3](../../../../../docs/specs/games-and-fill-in/the-mechanics.md#3-where-everything-lives)).
 *
 * The two reads the rail makes, handed to `gamesNeedingYou` — the rule is the domain's, and this
 * hook only supplies the lists, the reader, and `features/games`' answer to whether a score waits
 * on that reader. The shell mounts it for the session; TanStack dedupes the two lists to the
 * queries Home already makes.
 *
 * `undefined` is **nothing to draw**: no game needs you, the list has not landed, it failed, or the
 * reader is not known yet. The bar is told nothing about which — a spinner or a `?` on permanent
 * chrome is anxiety with no act behind it — which is `useChallengesWaiting`'s answer for the same
 * question one column over. A plan list still in flight counts a card by what it knows without
 * one, which can only miss *Needs result*, and the count catches up when the plans land.
 *
 * **`drawnElsewhere` is the Games a booking's card stands for** (#556): the rail leaves them out of
 * its own cards, so the count leaves them out too — Home's own badge counts those, and one game is
 * not two things that need you.
 */

import { useCurrentUser } from '@/features/auth/types';
import { awaitsYourAgreement, useGames } from '@/features/games/types';

import { gamesNeedingYou } from '../domain/gameCard';

import { usePlans } from './usePlans';

export function useGamesNeedingYou(
  drawnElsewhere: ReadonlySet<string> = NONE_ELSEWHERE,
): number | undefined {
  const games = useGames();
  const plans = usePlans();
  const me = useCurrentUser().data?.id;

  if (games.data === undefined || me === undefined) return undefined;

  const ours = games.data.filter((game) => !drawnElsewhere.has(game.gameId));
  const waiting = gamesNeedingYou(ours, plans.data, (game) => awaitsYourAgreement(game, me));
  return waiting === 0 ? undefined : waiting;
}

/** Nothing drawn elsewhere: one empty set rather than one per call. */
const NONE_ELSEWHERE: ReadonlySet<string> = new Set();
