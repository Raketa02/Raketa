/**
 * Every Skill rating this player holds — the gate's "is this player rated at anything?"
 * and, later, the done screen's list.
 *
 * An unrated player is an **empty collection with a 200**, not an error: absence of a
 * rating is the normal state of a new account, and the gate would otherwise have to
 * recover from a failure to decide where to send someone.
 */

import { listRatings as fetchRatings } from "../api/onboardingApi";
import type { SkillRating } from "../domain/SkillRating";
import { toSkillRatings } from "../mappers/onboardingMappers";

export interface ListRatingsOptions {
  readonly signal?: AbortSignal;
}

export function listRatings({
  signal,
}: ListRatingsOptions = {}): Promise<readonly SkillRating[]> {
  return fetchRatings({ signal }).then(toSkillRatings);
}
