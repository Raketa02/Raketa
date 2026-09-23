/**
 * **The rule behind the competitive card's Social tag row** — which of a candidate's tags the
 * searcher also chose, and what the card is allowed to say when none of them is.
 *
 * The four answers themselves are `shared/vocabulary/socialTagOverlap`'s, because the record
 * sheet draws the same row from its own read ([#373](https://github.com/Raketa02/Raketa/issues/373)).
 * What is here is the half that could only ever be Play's: reading one of those answers off a
 * **candidate row** — a search result carrying the engine's own `matched[]`
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
 * ## The claim needs both columns; a match needs only one
 *
 * That asymmetry is the whole of the rule and it is deliberate. `PLAYING_STYLE` and
 * `SOCIAL_VIBE` are two columns of one matrix, and the amber line's condition is *both* of
 * them: a `matched` list is a **positive** fact and one column is enough to state it, where
 * *No tags in common* is a claim about everything and a half-compared candidate has not earned
 * it. Reasoning that a stood-down column could not have contributed anyway is probably true
 * and is not worth being wrong about — the cost of the conservative reading is untinted tags,
 * and the cost of the other is the card saying something false with a straight face.
 *
 * `matched` is narrowed at the mapper against the same nineteen ids the labels come from, so
 * an old build sees an empty list where the platform found an overlap. `matchedInFull` is what
 * keeps that gap in place, and it lands as the union's *unknown* rather than as its claim —
 * the third spelling the shared module's note sets out.
 *
 * ## What is not here
 *
 * **No words.** The row is codes and a bit; the sentences are
 * `shared/vocabulary/socialTagPresentation`'s, and the clauses a listener gets are
 * `components/playerCardPresentation`'s. And **no ordering by default** — the tags draw in the
 * order the server served them, so a shared tag does not jump the queue: the row is *what they
 * published*, and re-ordering it by what the reader has in common would be a different list.
 * The deck card takes the other side of that trade for one surface
 * ([ADR-0169](../../../../../docs/adr/0169-the-deck-lives-on-players-and-a-swipe-is-an-answer.md)
 * §7): six tags wrap over a photograph and the volt *· you too* is the thing a player decides
 * on, so it asks for the shared ones **first** — and the ordering runs **before the cap**, so
 * the shared tag is never the one a seventh would cut off. That is `domain/deckTags`' rule,
 * applied here because the cap is here.
 */

import type { SocialTagId } from '@/shared/vocabulary/socialTags';
import {
  SOCIAL_TAG_ROW_CAP,
  type SharedTag,
  type SocialTagOverlap,
} from '@/shared/vocabulary/socialTagOverlap';

import type { Candidate } from './candidate';
import { sharedFirst } from './deckTags';
import { isTagEvidence, type TagRelationships } from './evidence';

/**
 * The row's four answers — **`shared/vocabulary`'s**, and re-exported here so a caller of the
 * rule reads the value it returns from the file that returns it.
 *
 * The one name, and not the three. `SharedTag` and `SOCIAL_TAG_ROW_CAP` are read from the
 * shared module directly by whoever needs them, because a re-export nothing imports is a
 * second public name for a thing that already has one.
 */
export type { SocialTagOverlap } from '@/shared/vocabulary/socialTagOverlap';

/** Both columns of the matrix. The amber claim needs an answer from each of them. */
const TAG_TERMS = ['PLAYING_STYLE', 'SOCIAL_VIBE'] as const;

/** In whose order the row is drawn: the person's own, or the shared tags first (the deck's). */
export type TagOrder = 'served' | 'shared-first';

export function socialTagOverlap(
  candidate: Candidate,
  order: TagOrder = 'served',
): SocialTagOverlap {
  const compared = tagEvidenceOf(candidate);
  const tags = candidate.card.socialTags.slice(0, SOCIAL_TAG_ROW_CAP);

  const matched = new Set(compared.flatMap((evidence) => evidence.matched));
  if (matched.size > 0) {
    // Marked over the whole list and ordered before the cap, so the shared ones survive it.
    const marked: readonly SharedTag[] = candidate.card.socialTags.map((id) => ({
      id,
      shared: matched.has(id),
    }));
    const ordered = order === 'shared-first' ? sharedFirst(marked) : marked;
    return { kind: 'shared', tags: ordered.slice(0, SOCIAL_TAG_ROW_CAP) };
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
