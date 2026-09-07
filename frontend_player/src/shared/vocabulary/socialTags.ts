/**
 * The **Social tag** vocabulary, as this build knows it.
 *
 * A tag is an **id and a client's copy**. The id is the platform's, permanent and
 * persisted on profiles; the words a player reads are this app's and live in
 * `socialTagPresentation` beside this file. That split is the contract's
 * (`GET /player-profile/options` serves ids and grouping only), and it is what lets a
 * label be re-written without touching a single stored profile.
 *
 * ## Why the ids are listed here at all
 *
 * The picker renders **what it is served**, in the order it is served — group order and
 * tag order within a group are both part of the contract, and nothing here sorts. What
 * this list decides is narrower: which ids this build can *draw*. An id with no label is a
 * chip with no words on it, so a served id this build has never heard of is dropped rather
 * than guessed at — the same answer `toSport` gives a sport a phone has not updated for,
 * and for the same reason: the generated union says it cannot happen, and a phone that has
 * not been updated in eight months says otherwise.
 *
 * The other direction — an id this build knows and the platform no longer serves — is not
 * this file's problem. Retiring a tag means dropping it from the response while continuing
 * to honour it on the profiles that hold it, so a retired id simply never arrives here.
 *
 * ## Why it is in `shared/`
 *
 * It was `player_profile/domain/SocialTag.ts` while the tag picker was its only reader.
 * Play is the **third** caller — the two tag terms of Fit each carry tag ids, and their
 * reason lines resolve them through the same labels — which is `recoveryMessage.ts`'s own
 * stated trigger for a promotion, invoked by name in
 * [`the-words.md`](../../../../docs/specs/matchmaking/the-words.md) §1. What Play must not
 * do is re-type this list: two tables of nineteen ids drift the release after somebody
 * edits one of them.
 *
 * What stayed behind in `player_profile` is the shape of the **served vocabulary** — a
 * group with its tags in render order — because that is the profile options response's
 * shape and no other feature reads it.
 */

/**
 * Every tag id this build can draw, in the vocabulary's own order.
 *
 * The order is documentation only. What a player sees is the served order — this is a
 * membership test wearing an array, and the array is what makes the type below.
 */
export const SOCIAL_TAG_IDS = [
  'STAYS_FOR_A_DRINK',
  'STRAIGHT_HOME_AFTER',
  'TALKS_THROUGH_THE_MATCH',
  'SETTLES_UP_ON_THE_SPOT',
  'BOOKS_THE_NEXT_ONE',
  'SHARES_A_LIFT',
  'PLAYS_TO_WIN',
  'LAUGHS_OFF_MISTAKES',
  'ENCOURAGES_A_PARTNER',
  'GENEROUS_ON_LINE_CALLS',
  'QUIET_AND_FOCUSED',
  'WARMS_UP_PROPERLY',
  'HERE_TO_IMPROVE',
  'HERE_TO_COMPETE',
  'HERE_FOR_THE_EXERCISE',
  'HERE_TO_MEET_PLAYERS',
  'HERE_FOR_A_REGULAR_GAME',
  'HERE_TO_GET_BACK_INTO_IT',
  'OPEN_TO_MEET_SOMEONE',
] as const;

export type SocialTagId = (typeof SOCIAL_TAG_IDS)[number];

/** The three groups the nineteen are rendered under. Each is about the game and nothing else. */
export const SOCIAL_TAG_GROUP_IDS = [
  'AFTER_THE_MATCH',
  'ON_THE_COURT',
  'WHY_YOU_ARE_HERE',
] as const;

export type SocialTagGroupId = (typeof SOCIAL_TAG_GROUP_IDS)[number];
