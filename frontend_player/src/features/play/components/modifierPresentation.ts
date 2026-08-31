/**
 * The four adjustments the engine makes after the eight terms are summed.
 *
 * **All four print.** *"A modifier that could move a score without owing a sentence would be
 * Liveness wearing stage 4's clothes"* — so there is no silent adjustment in this vocabulary,
 * and day one the block is empty for nearly everybody
 * ([`the-words.md`](../../../../../docs/specs/matchmaking/the-words.md) §9).
 *
 * **The block's figure is `fit − Σcontributions`, and no row prints a running total.**
 * `record_rows.py` forbids summing the list, and the words below must not tempt anyone into
 * one: each is a sentence about a single adjustment, and the heading is the only place a
 * figure appears.
 */

import type { ModifierCode } from '../domain/vocabulary';

const LINE: Readonly<Record<ModifierCode, string>> = {
  CALIBRATION_VALUE: 'Playing them would sharpen your rating',
  FAMILIARITY: "You've played them before",
  WELCOMING_RECORD: 'Good with players who are new',
  // The floor breach is stated here and **only** here: the reliability reason line prints the
  // score and never the breach, because one dock printed twice reads as two.
  RELIABILITY_FLOOR_BREACH: 'Their record sits under the bar',
};

export function modifierLine(code: ModifierCode): string {
  return LINE[code];
}

/** What the block of adjustments is called, above the rows. */
export const MODIFIERS_HEADING = 'Then the engine adjusted it';

/** What the eight terms' own sub-total is called, under them. */
export const TERM_SUBTOTAL_LABEL = 'The eight terms';

/**
 * The derived figure the block is headed by.
 *
 * `appliedFigure` is `fit − Σcontributions`, **already written**: it is computed once by
 * whoever draws the block — never by re-adding these rows — and its sign is part of the
 * figure, not of this sentence.
 */
export function adjustmentsTotal(appliedFigure: string): string {
  return `${appliedFigure} from adjustments`;
}
