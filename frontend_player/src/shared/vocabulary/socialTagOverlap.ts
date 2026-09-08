/**
 * **What a Social tag row draws** — which of somebody's tags the reader also chose, and which
 * of three silences the absence of an answer is
 * ([#311](https://github.com/Raketa02/Raketa/issues/311)).
 *
 * The tags themselves are a fact about one person and cross on their card. This is the
 * **second** register over them: *you too*, or one of three different ways of saying nothing.
 *
 * ## Why this is `shared/` and not `play/domain/`
 *
 * The row began as the competitive candidate card's, and the shape of its answer began beside
 * the rule that computes one. The record sheet draws the same row
 * ([#373](https://github.com/Raketa02/Raketa/issues/373)), so the row is one component in
 * `shared/ui` and the value it takes had to come below both features with it — a component
 * beneath every feature cannot read a type that lives inside one, and copying the union would
 * be two lists of four answers drifting apart.
 *
 * **The rule stayed behind.** `features/play/domain/socialTagOverlap` computes one of these
 * from a candidate row, which is Play's own shape — served by a search, carrying the engine's
 * `matched[]`. Play computes the overlap and hands the value down; the record sheet will be
 * served its own. That is the split `shared/README.md`'s test asks for: a second feature would
 * have written this union exactly and could not have written that rule at all.
 *
 * ## The absence has three spellings, and only one of them is a claim
 *
 * - **Compared, and nothing matched.** They genuinely share nothing, and the row says so in
 *   amber. This is the only one of the three that asserts anything.
 * - **Not compared.** One side published no tags in a column, so the platform **does not
 *   know**: the tags draw as facts about their owner and nothing is said about the overlap.
 *   *Hidden, never blank*, which is the discipline the reason list and the meta line take.
 * - **Compared, matched, and this build cannot name what matched.** An old build sees an empty
 *   list where the platform found an overlap. It draws exactly as the second case, because
 *   saying *No tags in common* there would be a build making a claim out of its own ignorance
 *   ([`the-words.md`](../../../../docs/specs/matchmaking/the-words.md) §3).
 *
 * A discriminated union rather than a list plus flags, because the amber line is not a tag and
 * *we do not know* is not *there is nothing*. A component switching over this cannot draw the
 * claim in the case that has not earned it, and that is the whole reason the union exists.
 */

import type { SocialTagId } from './socialTags';

/**
 * How many tags a row draws, which is **the profile step's own ceiling read from the other
 * side**.
 *
 * The Social tags step takes 2 to 6, so nobody can publish a seventh and this cap removes
 * nothing today. It is here because the row's layout is written against six: a served seventh
 * would be a contract change, and it should reach the reader as a shorter row rather than as a
 * card that grew a line nobody designed.
 */
export const SOCIAL_TAG_ROW_CAP = 6;

/** One tag somebody published, and whether the reader chose it too. */
export interface SharedTag {
  readonly id: SocialTagId;
  readonly shared: boolean;
}

/** What the row draws — four answers, and each is a different thing to say. */
export type SocialTagOverlap =
  /** Compared, and at least one match this build can name. `shared` marks which. */
  | { readonly kind: 'shared'; readonly tags: readonly SharedTag[] }
  /** Compared, and nothing matched — **the amber line, in the row's place.** */
  | { readonly kind: 'none-in-common' }
  /** Not compared, or matched beyond this build's vocabulary — their tags, and no claim. */
  | { readonly kind: 'unknown'; readonly tags: readonly SocialTagId[] }
  /** Nothing to draw at all: no comparison, and no tags this build can name. */
  | { readonly kind: 'hidden' };
