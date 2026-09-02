/**
 * What a search says while it runs, and what the why-fit sheet says at the top.
 *
 * §B14 draws the searching screens with an inventory of terms — *"Level fit, predicted
 * balance, reliability, when your weeks overlap, distance, vibe, fresh faces — the same seven
 * terms"* — and that list is **stale three ways at once**: it includes *fresh faces*, which is
 * a modifier; it omits `INTENT_ALIGNMENT`, third-largest in both modes; and *"band width"* is
 * not a term at all
 * ([`the-words.md`](../../../../../docs/specs/matchmaking/the-words.md) §16).
 *
 * > **Drop the inventory. Keep the count.**
 *
 * [#233](https://github.com/Raketa02/Raketa/issues/233) §5's ruling reaches here unchanged —
 * *"any replacement summary is a weight claim in prose with no gate behind it"* — and it
 * reaches the sheet's header the same way.
 *
 * **The count is the response's**, `PoolDescription.players_in_range`. #223 moved it off the
 * prototype's 650 ms timer, which printed a number before the answer existed, so nothing here
 * takes a number that is not already an answer.
 *
 * That is now a **shape** rather than a rule a caller obeys
 * ([#269](https://github.com/Raketa02/Raketa/issues/269)): the count arrives as
 * `number | undefined` and comes back absent, so a latch drawn while the request is still in
 * flight has a headline and nothing to print beside it. There is no number to invent, because
 * the only place one could come from is a response that does not exist yet.
 */

import { counted } from '@/shared/formatting/counted';

import type { SearchMode } from '../domain/vocabulary';

import { isDoubles } from './builderPresentation';

/**
 * A searching screen's two lines: what is happening, and how many people it is happening to.
 *
 * **The second is absent until there is an answer.** A wait states what it is doing from the
 * moment it starts; what it is doing it to is a fact, and a fact this screen does not have
 * until the response lands.
 */
export interface SearchingStatus {
  readonly headline: string;
  /** Absent for as long as the response is. */
  readonly count?: string;
}

/** The pool's own ranking pass, which is the one that names the sport it is ranking for. */
export function poolRankingStatus(pool: {
  /** `undefined` while the search is still running — see {@link SearchingStatus}. */
  readonly playersInRange: number | undefined;
  readonly sportName: string;
}): SearchingStatus {
  return {
    headline: 'Ranking everybody you could play…',
    count:
      pool.playersInRange === undefined
        ? undefined
        : `${pool.playersInRange} in range for ${pool.sportName}`,
  };
}

/**
 * The engine seating a court. The sport is already on the screen, so the count stands alone.
 *
 * **The headline takes the seat count**, because *four* is a word about a Sport rather than
 * about a number the copy invents — `builderPresentation`'s rule, read here off the same
 * helper. Said flat, a squash player would have watched the engine look for the evenest four
 * on a court with two seats on it.
 */
export function engineFillStatus(pool: {
  /** `undefined` while the fill is still running — see {@link SearchingStatus}. */
  readonly playersInRange: number | undefined;
  /** The court's own, from `Court`'s coordinates. */
  readonly seats: number;
}): SearchingStatus {
  return {
    headline: `Looking for the evenest ${isDoubles(pool.seats) ? 'four' : 'match'}…`,
    count: pool.playersInRange === undefined ? undefined : `${pool.playersInRange} in range`,
  };
}

/**
 * *"tuned for a … game"* — the sheet header's mode clause, and one of only three places mode
 * reaches at all.
 *
 * **Absent where `SearchEnvelope.mode` is null**, which is exactly the deck: deriving
 * `NO_PREFERENCE → FOR_FUN` on this side would be the engine's own resolution rule rewritten
 * in TypeScript, refused by name in #233 §6. The row above it may still say what kind of
 * evening was priced — that reads `my_mode` off the evidence — and on the deck the two
 * correctly disagree.
 */
const TUNED_FOR: Readonly<Record<SearchMode, string>> = {
  COMPETITIVE: 'tuned for a competitive game',
  FOR_FUN: 'tuned for a fun game',
};

/**
 * The why-fit sheet's header: how many terms are live, what they were tuned for, and the one
 * sentence that says what the whole sheet is worth.
 *
 * `liveTerms` is **derived from the rows the sheet is drawing**, never from a constant: a
 * candidate with three terms stood down has five, and a header claiming eight would be
 * describing a different sheet.
 *
 * *"Weights persuade; you decide"* survives from §F1 rule 7 and is booked here by name.
 */
export function whyFitHeader(header: {
  readonly liveTerms: number;
  readonly mode: SearchMode | null;
}): string {
  const terms = counted(header.liveTerms, 'weighted term', 'weighted terms');
  const tuned = header.mode === null ? '' : `, ${TUNED_FOR[header.mode]}`;
  return `${terms}${tuned}. Weights persuade; you decide.`;
}
