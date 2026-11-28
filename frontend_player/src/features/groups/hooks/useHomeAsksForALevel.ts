/**
 * **Whether Home asks for a level** — `homeAsksForALevel` over the two reads it needs
 * ([ADR-0200](../../../../../docs/adr/0200-a-level-is-asked-where-play-begins.md) §7,
 * [#731](https://github.com/Rakieta02/Rakieta/issues/731)).
 *
 * **The ratings first, and the groups only for a player rated in nothing**: a rated player — the
 * common Home — is asked nothing by the card, so asking which groups she is in would be a read for
 * a question that is already answered. The ratings read is onboarding's, under its key, so the
 * card and every group's chip share one answer.
 *
 * `undefined` until both have answered, and on a failed read: the card is a nudge, never a wall,
 * and a Home that cannot say whether to nudge says nothing.
 *
 * **Home's own read is no part of it** (#816, ADR-0205 §4): a friend's ask for a level waits in
 * Needs your answer and never stands in the card's place, so the card no longer waits on whether
 * one does.
 */

import { onboardingKeys, useSkillRatings } from '@/features/onboarding/types';
import { readHasFinished, useQueryCacheAnswer } from '@/shared/lib/query-client';

import { homeAsksForALevel, levelCardReadsFinished } from '../domain/groupPage';

import { groupKeys } from './groupKeys';
import { useMyGroups } from './useGroups';

export function useHomeAsksForALevel(): boolean | undefined {
  const ratings = useSkillRatings();
  const ratedInNothing = ratings.data === undefined ? undefined : ratings.data.length === 0;
  const groups = useMyGroups({ enabled: ratedInNothing === true });

  if (ratedInNothing === false) return false;
  if (ratedInNothing === undefined || groups.data === undefined) return undefined;
  return homeAsksForALevel(
    groups.data.length,
    (ratings.data ?? []).map((rating) => rating.sport),
  );
}

/**
 * **Whether the reads the card answers from have finished** (#871) — `levelCardReadsFinished` over
 * the ratings and your groups, each landed, refused, held for a connection, or failed once and
 * retrying (`readHasFinished`). Read off the cache, so it draws again only as it turns.
 */
export function useLevelCardFinished(): boolean {
  return useQueryCacheAnswer((client) => {
    const ratings = client.getQueryState<readonly unknown[]>(onboardingKeys.ratings());
    return levelCardReadsFinished({
      ratingsFinished: readHasFinished(ratings),
      ratedInNothing: ratings?.data === undefined ? undefined : ratings.data.length === 0,
      groupsFinished: readHasFinished(client.getQueryState(groupKeys.mine())),
    });
  });
}
