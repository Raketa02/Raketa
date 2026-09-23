/**
 * Which of a candidate's reasons a surface says, and what it says when none of them survive.
 *
 * `the-play-screens.md` §10 narrows it to one sentence — **a reason line never restates a
 * value the card already renders** — and that makes the filter a property of the *surface*
 * rather than of the vocabulary: the three cards render different things, so the spec's
 * single filter is wrong on two of them
 * ([`the-words.md`](../../../../../docs/specs/matchmaking/the-words.md) §5).
 *
 * ## The order inverts
 *
 * §B10 took the top three and *then* filtered, which is what makes a card's "three reasons"
 * sometimes one, and is the direct cause of its `[GAP: no fallback string]`. **Filter first,
 * then take three.**
 *
 * ## Why this is a rule and not a table
 *
 * Every line below is something somebody could be wrong about — which is the test
 * [`the-play-components.md`](../../../../../docs/specs/matchmaking/the-play-components.md) §7
 * applies to decide between `domain/` and `components/`. It chooses **codes**, never
 * sentences: the words for what it picks are `reasonPresentation`'s and
 * `livenessPresentation`'s.
 */

import type { ScoredTerm } from './evidence';
import type { LivenessReason, Term } from './vocabulary';

/**
 * Three, and the cap is the client's.
 *
 * The wire sends every term that fired, ranked by contribution, and says so: *"the cap is the
 * client's."* Four reasons on a card is a layout change, not a contract one.
 */
export const REASON_CAP = 3;

/**
 * The why-fit sheet draws **everything, on purpose**, so it filters nothing.
 *
 * A summary block there would break §10 *"on the one screen whose job is showing values"*
 * ([#233](https://github.com/Raketa02/Raketa/issues/233) §7).
 */
export const WHYFIT_DRAWS: readonly Term[] = [];

/**
 * What a surface says under the fit pill.
 *
 * Three arms and not an array, because *hidden* and *nothing to say* are different states and
 * §G5's blank line is the bug being fixed.
 */
export type ReasonSelection =
  | { readonly kind: 'terms'; readonly terms: readonly ScoredTerm[] }
  | { readonly kind: 'liveness'; readonly reason: LivenessReason }
  | { readonly kind: 'hidden' };

export interface ReasonInput {
  /**
   * The terms this surface renders a value for, and therefore will not restate in a line.
   *
   * Passed in rather than looked up, so that the set is declared beside the component that
   * draws it — the one place it cannot go stale silently. The three card sets are **exported
   * by the three cards** for that reason; the sheet's empty one is below, because the sheet
   * filters nothing and *that* is a statement about this rule rather than about a component.
   */
  readonly drawn: readonly Term[];
  /** Every term that fired, **ranked by contribution**. Nothing here sorts. */
  readonly terms: readonly ScoredTerm[];
  /** The terms the engine is concerned about, ranked by points forgone. */
  readonly concerns: readonly Term[];
  /** Why this person moved, ranked by how far. */
  readonly livenessReasons: readonly LivenessReason[];
  /**
   * Whether this term's evidence **says** anything — the copy's answer, not this rule's.
   *
   * Three of the eight renderers legitimately decline: a declared mismatch of intent, and a
   * tag term whose only firing pairs clash, are claims about a shortfall, and a clash is a
   * graded claim the engine is the only thing entitled to make
   * ([`the-words.md`](../../../../../docs/specs/matchmaking/the-words.md) §6.2). A term that
   * survives the filter and then renders nothing is a **line the card cannot draw**, so it
   * cannot be one of the three: counting it prints two reasons where three were promised, and
   * at the limit prints §G5's blank row — the bug this whole selection exists to fix.
   *
   * It is a parameter rather than a table here because *what a sentence can say* is
   * `reasonPresentation`'s and this file holds no words. The caller passes
   * `(row) => reasonLine(row.evidence, pair) !== undefined`.
   */
  readonly saysSomething: (term: ScoredTerm) => boolean;
}

/**
 * `INTENT_ALIGNMENT` is never filtered.
 *
 * After the drops it *is* the first reason on the competitive card — third-largest term in
 * both modes — and a dedicated row for it would delete the sentence it duplicates
 * ([#230](https://github.com/Raketa02/Raketa/issues/230) §1). Stated here rather than left to
 * every surface to remember to leave out of its own set.
 */
const NEVER_FILTERED: Term = 'INTENT_ALIGNMENT';

export function selectReasons(input: ReasonInput): ReasonSelection {
  const said = input.terms
    // A row whose term this build has no name for is **not filtered out here** — it is
    // filtered by `saysSomething` below, along with every other row that cannot be written as
    // a sentence. Its evidence may be perfectly readable, and a reason line never names its
    // term: it is a sentence over the payload, so the row still answers *why this person*.
    .filter(
      (row) => row.term === NEVER_FILTERED || row.term === null || !input.drawn.includes(row.term),
    )
    // A concerned term is removed from the reason list: one term saying "✓ X" and "! X" on
    // one card is §10's rule broken at its own root, and the sheet still shows the term with
    // its concern marked in place. The slot goes to the next survivor.
    .filter((row) => row.term === null || !input.concerns.includes(row.term))
    // And so does a term whose evidence is not a reason at all — see `saysSomething`.
    .filter(input.saysSomething)
    .slice(0, REASON_CAP);

  if (said.length > 0) return { kind: 'terms', terms: said };

  // The fallback is the top liveness code, not the fourth-ranked term: the row's question is
  // *why this person*, and that is what a liveness code answers. Nothing new crosses the wire
  // — the sheet already renders these a level down, under *What else moved you here*.
  const [movedThemHere] = input.livenessReasons;
  if (movedThemHere !== undefined) return { kind: 'liveness', reason: movedThemHere };

  return { kind: 'hidden' };
}

/**
 * How many concerns a **card** shows. One — and the cap is the client's, not the engine's.
 *
 * `concerns[]` arrives ranked by points forgone and uncapped on purpose:
 * [`the-play-screens.md`](../../../../../docs/specs/matchmaking/the-play-screens.md) §1 says
 * capping it in the engine *"would throw away exactly the rows that explain a low Fit on the
 * screen built to explain it"*. So the sheet shows all of them and a card shows the top one.
 */
export const CONCERN_CAP = 1;

/**
 * The concern a card draws, or nothing.
 *
 * Two things can drop the top one, and both are the same shape as the reason list's. A
 * concern is keyed by `term` alone, so it is **joined back to the row that fired** — a term
 * the engine is concerned about but which did not fire has no evidence, and a sentence over
 * no evidence is not writable. And the two tag terms can be a concern with **nothing
 * clashing**, their measured zero, where §7 refuses to let the client call it a clash. Either
 * way the card draws the next concern down rather than a blank row, exactly as the reason
 * list does, and the sheet still marks the term in place.
 *
 * It returns the **row**, not a sentence: this file holds no words, and `concernLine` is a
 * sentence over the evidence the row carries.
 */
export function selectConcern(input: {
  readonly terms: readonly ScoredTerm[];
  readonly concerns: readonly Term[];
  /** `(row) => concernLine(row.evidence) !== undefined`, for the reason `saysSomething` is. */
  readonly saysSomething: (term: ScoredTerm) => boolean;
}): readonly ScoredTerm[] {
  return input.concerns
    .map((term) => input.terms.find((row) => row.term !== null && row.term === term))
    .filter((row): row is ScoredTerm => row !== undefined)
    .filter(input.saysSomething)
    .slice(0, CONCERN_CAP);
}
