/**
 * **The competitive card's Social tag row** — which of a candidate's tags the searcher also
 * chose, and what the card is allowed to say when none of them is.
 *
 * The tags themselves are a fact about the candidate alone and cross on `player_card`. What
 * this file decides is the **second** register on that row: which tags are *yours too*, and
 * which of three different silences the absence of an answer is
 * ([#311](https://github.com/Raketa02/Raketa/issues/311)).
 *
 * ## *You too* is on the wire, and is never recomputed from a profile read
 *
 * `PlayingStyleEvidence` and `SocialVibeEvidence` each spread `TagRelationships` flat, and
 * `matched[]` is *"two Social tag ids the product claims fit together"* — shared, by
 * definition. The union of `matched` across the two terms is the whole answer, and reading the
 * searcher's own profile to intersect it here would be a client recomputing a judgement the
 * engine already published, against a profile that may have changed since the search ran.
 *
 * **Only `matched` tints.** `complementary` and `clashing` are a different relationship — two
 * tags the product claims fit together *because they differ* — and they reach the card as
 * reason sentences and as its one concern. A card that tinted them would be saying *you too*
 * about a tag the searcher does not have.
 *
 * ## The absence has three spellings, and only two of them are the ticket's
 *
 * - **Compared, and nothing matched.** They genuinely share nothing, and the card says so in
 *   amber. This is a claim, and it is the only one of the three that is.
 * - **Not compared** — both tag terms stood down, which is `NOTHING_FROM_YOU` or
 *   `NOTHING_FROM_THEM`: one side published no tags in that column. The platform **does not
 *   know**, so the tags draw as facts about the candidate and nothing is said about the
 *   overlap. *Hidden, never blank*, which is the discipline the reason list and the meta line
 *   already take.
 * - **Compared, matched, and this build cannot name what matched.** `matched` is narrowed at
 *   the mapper against the same nineteen ids the labels come from, so an old build sees an
 *   empty list where the platform found an overlap. `matchedInFull` is what keeps that gap in
 *   place, and this row draws it exactly as the second case: the tags, untinted, and **no**
 *   amber line. Saying *No tags in common* there would be this build making a claim out of its
 *   own ignorance, which is the one thing §3's drop must never turn into.
 *
 * **The claim needs both columns; a match needs only one.** That asymmetry is the whole of the
 * rule and it is deliberate. `PLAYING_STYLE` and `SOCIAL_VIBE` are two columns of one matrix,
 * and the ticket's condition is *both* of them: a `matched` list is a **positive** fact and one
 * column is enough to state it, where *No tags in common* is a claim about everything and a
 * half-compared candidate has not earned it. Reasoning that a stood-down column could not have
 * contributed anyway is probably true and is not worth being wrong about — the cost of the
 * conservative reading is untinted tags, and the cost of the other is the card saying something
 * false with a straight face.
 *
 * ## What is not here
 *
 * **No words.** The row is codes and a bit; the sentences are `playerCardPresentation`'s and
 * the chips are `SocialTagOverlap`'s. And **no ordering** — the tags draw in the order the server
 * served them, so a shared tag does not jump the queue: the row is *what they published*, and
 * re-ordering it by what the reader has in common would be a different list.
 */

import type { SocialTagId } from '@/shared/vocabulary/socialTags';

import type { Candidate } from './candidate';
import { isTagEvidence, type TagRelationships } from './evidence';

/**
 * How many tags the row draws, which is **the profile step's own ceiling read from this side**.
 *
 * The Social tags step takes 2 to 6, so a candidate cannot publish a seventh and this cap
 * removes nothing today. It is here because the card's layout is written against six: a served
 * seventh would be a contract change, and it should reach the reader as a shorter row rather
 * than as a card that grew a line nobody designed.
 */
export const SOCIAL_TAG_ROW_CAP = 6;

/** One tag the candidate published, and whether the searcher chose it too. */
export interface SharedTag {
  readonly id: SocialTagId;
  readonly shared: boolean;
}

/**
 * What the row draws — four answers, and each is a different thing to say.
 *
 * A discriminated union rather than a list plus flags, because the amber line is not a tag and
 * *we do not know* is not *there is nothing*. A component switching over this cannot draw the
 * claim in the case that has not earned it.
 */
export type SocialTagOverlap =
  /** Compared, and at least one match this build can name. `shared` marks which. */
  | { readonly kind: 'shared'; readonly tags: readonly SharedTag[] }
  /** Compared, and nothing matched — **the amber line, in the row's place.** */
  | { readonly kind: 'none-in-common' }
  /** Not compared, or matched beyond this build's vocabulary — their tags, and no claim. */
  | { readonly kind: 'unknown'; readonly tags: readonly SocialTagId[] }
  /** Nothing to draw at all: no comparison, and no tags this build can name. */
  | { readonly kind: 'hidden' };

/** Both columns of the matrix. The amber claim needs an answer from each of them. */
const TAG_TERMS = ['PLAYING_STYLE', 'SOCIAL_VIBE'] as const;

export function socialTagOverlap(candidate: Candidate): SocialTagOverlap {
  const compared = tagEvidenceOf(candidate);
  const tags = candidate.card.socialTags.slice(0, SOCIAL_TAG_ROW_CAP);

  const matched = new Set(compared.flatMap((evidence) => evidence.matched));
  if (matched.size > 0) {
    return { kind: 'shared', tags: tags.map((id) => ({ id, shared: matched.has(id) })) };
  }

  // Nothing matched, and only now does it matter how much was asked. Both columns must have
  // fired and both must be fully readable, or the silence is one of the two kinds this row is
  // not allowed to speak over. See the module note.
  const answeredInFull =
    compared.length === TAG_TERMS.length && compared.every((evidence) => evidence.matchedInFull);
  return answeredInFull ? { kind: 'none-in-common' } : untinted(tags);
}

/** Their tags with no claim over them, or nothing where there are none to draw. */
function untinted(tags: readonly SocialTagId[]): SocialTagOverlap {
  return tags.length === 0 ? { kind: 'hidden' } : { kind: 'unknown', tags };
}

/**
 * Every tag comparison this build could **read**, which is not the same as every one served.
 *
 * A term with `evidence: null` is a variant this build has never seen: it fired, and what it
 * says is unavailable. Counting it as a comparison would let an unreadable row license the
 * amber claim, which is the third spelling arriving through a different door.
 */
function tagEvidenceOf(candidate: Candidate): readonly TagRelationships[] {
  return candidate.terms.flatMap((term) => (isTagEvidence(term.evidence) ? term.evidence : []));
}
