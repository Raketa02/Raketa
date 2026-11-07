/**
 * **Whether Home asks for a level** — `homeAsksForALevel` over the two reads it needs
 * ([ADR-0200](../../../../../docs/adr/0200-a-level-is-asked-where-play-begins.md) §7,
 * [#731](https://github.com/Raketa02/Raketa/issues/731)).
 *
 * **The ratings first, and the groups only for a player rated in nothing**: a rated player — the
 * common Home — is asked nothing by the card, so asking which groups she is in would be a read for
 * a question that is already answered. The ratings read is onboarding's, under its key, so the
 * card and every group's chip share one answer.
 *
 * `undefined` until both have answered, and on a failed read: the card is a nudge, never a wall,
 * and a Home that cannot say whether to nudge says nothing.
 *
 * **And a friend's ask for a level stands in its place** (#765, Q129): Home's own read says whether
 * ASKED FOR A LEVEL holds a card (`proposals`' `useHomeLevelAsks`), and until it has answered the
 * card is not drawn either — so the two are never drawn and then swapped. A Home read refused, or
 * waiting for a connection, holds none, and the card is free to say why nothing is happening.
 */

import { useSkillRatings } from '@/features/onboarding/types';
import { useHomeLevelAsks } from '@/features/proposals/types';

import { homeAsksForALevel } from '../domain/groupPage';

import { useMyGroups } from './useGroups';

export function useHomeAsksForALevel(): boolean | undefined {
  const ratings = useSkillRatings();
  const ratedInNothing = ratings.data === undefined ? undefined : ratings.data.length === 0;
  const groups = useMyGroups({ enabled: ratedInNothing === true });
  const asked = useHomeLevelAsks();

  if (ratedInNothing === false) return false;
  if (ratedInNothing === undefined || groups.data === undefined || asked === undefined) {
    return undefined;
  }
  return homeAsksForALevel(
    groups.data.length,
    (ratings.data ?? []).map((rating) => rating.sport),
    asked.length,
  );
}
