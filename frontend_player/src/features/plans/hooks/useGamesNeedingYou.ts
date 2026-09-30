/**
 * **How many of your games need you** — the count on Home's column of the tab bar
 * ([#550](https://github.com/Raketa02/Raketa/issues/550),
 * [the mechanics §3](../../../../../docs/specs/games-and-fill-in/the-mechanics.md#3-where-everything-lives)).
 *
 * The cards the rail draws, counted: the same two reads, the same join and the same shelf, so the
 * badge cannot count a card Home does not show. Which of them need you is `needsYou`, over the
 * card's name and — for *Confirm the result*, the one name that cannot say — whether a score is
 * waiting on your agreement, which is `features/games`' fold and crosses as an answer. The shell
 * mounts this for the whole session; TanStack dedupes the two lists to the queries Home already
 * makes, so nothing is fetched that Home would not fetch.
 *
 * `undefined` is **nothing to draw**: no game needs you, the list has not landed, it failed, or the
 * reader is not known yet. The bar is told nothing about which — a spinner or a `?` on permanent
 * chrome is anxiety with no act behind it — which is `useChallengesWaiting`'s answer for the same
 * question one column over. A plan still in flight counts a card by what it knows without one,
 * which can only miss *Needs result*, and the count catches up when the plans land.
 */

import { useCurrentUser } from '@/features/auth/types';
import { awaitsYourAgreement, useGames } from '@/features/games/types';

import { belongsOnTheRail, gameCardName, needsYou } from '../domain/gameCard';

import { usePlans } from './usePlans';

export function useGamesNeedingYou(): number | undefined {
  const games = useGames();
  const plans = usePlans();
  const me = useCurrentUser().data?.id;

  if (games.data === undefined || me === undefined) return undefined;

  const waiting = games.data.filter(belongsOnTheRail).filter((game) => {
    const plan = plans.data?.find((one) => one.challengeId === game.challengeId);
    return needsYou(gameCardName(game, plan), awaitsYourAgreement(game, me));
  }).length;

  return waiting === 0 ? undefined : waiting;
}
