/**
 * What a build says about a code it has never seen — **one sentence, everywhere**.
 *
 * Old app versions live on real phones for months, so every closed vocabulary the platform
 * serves has a value this build may not know. ADR-0106 §6 settled what happens then, and
 * [`the-words.md`](../../../../docs/specs/matchmaking/the-words.md) §3 made it testable:
 *
 * > *A code renders a named gap wherever the screen states a count or a total its row
 * > belongs to; everywhere else it is dropped.*
 *
 * So a why-fit term row, the not-counted block, a modifier row, an unfilled seat and a
 * challenge's standing all draw this sentence — the column has to add up, the seat is
 * *stated* as unfilled, and the standing **is** the whole line. A card's reason line, a
 * liveness tag and an inclusion tag are dropped instead: the card shows three reasons out of
 * eight and always did.
 *
 * **It names neither the code nor the vocabulary.** A raw `SOCIAL_VIBE` is a wire token in a
 * player's face, and *"an unknown evidence kind"* is a sentence about our schema. One string
 * rather than five, because a per-placement wording is five sentences that must all stay true
 * of one condition.
 *
 * **This is deliberately not the shape `evidencePresentation.ts` takes.** There an
 * unreadable direction *"draws no mark at all, rather than a default one"*, because the mark
 * is decoration over a row whose content came from the server. Here the code often **is** the
 * content.
 */

/** The gap's words. Cite this constant; never re-word it at a call site. */
export const OUT_OF_DATE_GAP = 'This app is too old to read this one — update Raketa.';

/**
 * The words for a code, or the gap when this build has none.
 *
 * For the placements where a gap is owed. Where a drop is owed instead, the caller filters
 * on `undefined` — a helper that turned an absent sentence into an empty one would make the
 * two placements look alike, and they are the whole of §3's rule.
 */
export function orOutOfDate(words: string | undefined): string {
  return words ?? OUT_OF_DATE_GAP;
}
