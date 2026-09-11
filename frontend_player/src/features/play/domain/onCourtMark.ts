/**
 * Whether a card's photo panel wears the **ON COURT** mark
 * ([#313](https://github.com/Raketa02/Raketa/issues/313)).
 *
 * One line of arithmetic, and it is in `domain/` for `atStake`'s reason:
 * [`the-play-components.md`](../../../../../docs/specs/matchmaking/the-play-components.md) §7
 * puts what somebody could be **wrong** about here rather than in a component, and there are
 * two things to be wrong about.
 *
 * ## The two absences are one answer, and that is the rule
 *
 * *Checked and flagged* and *nobody looked* draw **identically**, and a component holding
 * `review === 'allowed'` at one site and `review !== 'flagged'` at another would be one
 * refactor away from telling a searcher that a stranger's photograph had been doubted. That
 * is a moderation outcome about a third party, and
 * [ADR-0138](../../../../../docs/adr/0138-the-verdict-crosses-on-a-card-and-never-checked-is-its-own-answer.md)
 * publishes **only the positive**: the decision crosses so that a pass can be marked, and the
 * absence is where every other answer meets.
 *
 * The mapper has already folded a third case in — a verdict spelled in a way this build has
 * never seen arrives here as no verdict at all — so this predicate sees three states and not
 * four, and marks one of them.
 *
 * ## A poster has nothing to have passed
 *
 * The mark is a fact about **a photograph**, and a player with none is drawn the generated
 * court poster instead (`PlayerPhoto`). The wire omits `photo_id`, `photo_url` and `review`
 * together, so a verdict with no photograph beside it is a state the contract does not
 * produce — and the rule asks anyway, because the alternative is a component that draws a mark
 * over a poster on the day the contract changes its mind, with nothing anywhere saying it must
 * not.
 */

import type { PlayerCard } from './candidate';

/**
 * The two fields the mark is decided from — **the card's own pair, spelled once**.
 *
 * A `Pick` off `PlayerCard` rather than a fresh object type, and it is exported because two
 * readers want exactly this pair and a second inline declaration of it is the clump this
 * names: the rule below takes one, and `CandidateFactsInput.photo` is one — *the surface that
 * draws a photo panel hands over its subject's photograph*. Widening either of the two fields
 * on the card widens both readers, which is what a hand-written twin would have stopped doing
 * the first time they disagreed.
 */
export type MarkablePhoto = Pick<PlayerCard, 'photoUrl' | 'photoReview'>;

/**
 * The card's two photo fields, and nothing else.
 *
 * Named rather than positional, and the card's own pair rather than two booleans: both facts
 * are already on `PlayerCard` in exactly this shape, and a caller that had to work out *is
 * there a photograph* before asking is a caller that can get it wrong on its own.
 */
export function wearsOnCourtMark(photo: MarkablePhoto): boolean {
  return photo.photoUrl !== undefined && photo.photoReview === 'allowed';
}
