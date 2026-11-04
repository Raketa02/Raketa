/**
 * Every Skill rating this player holds — what a group's sport chip lists, and whether the door
 * where play begins is drawn at all (ADR-0200 §2, §4).
 *
 * An unrated player is an **empty collection with a 200**, not an error: absence of a rating
 * is the normal state of a new account — onboarding asks for none (#730) — and every screen
 * reading it would otherwise have to recover from a failure to draw the commonest case.
 */

import { listRatings as fetchRatings } from '../api/onboardingApi';
import type { SkillRating } from '../domain/SkillRating';
import { toSkillRatings } from '../mappers/onboardingMappers';

export interface ListRatingsOptions {
  readonly signal?: AbortSignal;
}

export function listRatings({ signal }: ListRatingsOptions = {}): Promise<readonly SkillRating[]> {
  return fetchRatings({ signal }).then(toSkillRatings);
}
