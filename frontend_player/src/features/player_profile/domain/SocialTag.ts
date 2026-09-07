/**
 * The **served** Social tag vocabulary — the shape `GET /player-profile/options` answers in.
 *
 * The ids themselves, and the words this app gives them, are
 * [`@/shared/vocabulary/socialTags`](../../../shared/vocabulary/socialTags.ts) and
 * `socialTagPresentation` beside it: Play reads the same nineteen ids off a player card, and
 * a second table of them is one release away from disagreeing with this one. What stays here
 * is the *response's* shape, because nothing outside this feature reads it.
 *
 * The picker renders **what it is served**, in the order it is served — group order and tag
 * order within a group are both part of the contract, and nothing here sorts.
 */

import type { SocialTagGroupId, SocialTagId } from '@/shared/vocabulary/socialTags';

/** One group of the vocabulary, with its tags in the order they are to be rendered. */
export interface SocialTagGroup {
  readonly group: SocialTagGroupId;
  readonly tagIds: readonly SocialTagId[];
}

/**
 * The whole vocabulary, in served order.
 *
 * A list rather than a map: the order is the contract, and a map's key order is not a
 * promise anybody made.
 */
export type SocialTagVocabulary = readonly SocialTagGroup[];
