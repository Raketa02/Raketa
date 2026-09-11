/**
 * **What tone a Player Score is drawn in** — one ladder, in one place.
 *
 * The pill on the record's header and every metered row beneath it read the same two numbers.
 * Two ladders would eventually disagree, and the screen would then show a green bar under a
 * red pill for the same ratio — which is the defect
 * [7.5](../../../../docs/design-system.md#75-the-level-bar) and
 * [7.8](../../../../docs/design-system.md#78-the-confidence-ring) exist to prevent, arriving
 * one part of the document later.
 *
 * ## The lower step is not a drawing decision
 *
 * `SCORE_FLOOR` is the matcher's own `SCORE_MIN`: below it the engine applies a flat penalty
 * and prints `reliability_floor` as the reason. The record sheet exists so that **a player who
 * works their visible score back up can watch that penalty lift**, which is only true while the
 * colour changes at the number the engine acts on. A pill that turned red a point late would
 * tell somebody their penalty had not started on the day it had.
 *
 * It is a **step in an existing fill** rather than a new colour, which is
 * [15.2](../../../../docs/design-system.md#152-adding-a-colour)'s own licence and exactly what
 * `FIT_HIGH = 90` already is.
 *
 * ## Never colour alone
 *
 * The tone is a second cue and never the carrier: the figure is printed beside it, in words,
 * on every surface that draws one ([Part 13](../../../../docs/design-system.md#part-13--accessibility)).
 */

/**
 * Where the matcher starts holding somebody back — `SCORE_MIN`, and the only place this client
 * writes it down.
 */
export const SCORE_FLOOR = 70;

/** Where a record stops being ordinary and starts being good. */
export const SCORE_STRONG = 90;

/** The three steps, named for what they say rather than for the colour they take. */
export type ScoreTone = 'good' | 'neutral' | 'poor';

export function scoreTone(score: number): ScoreTone {
  if (score < SCORE_FLOOR) return 'poor';
  return score < SCORE_STRONG ? 'neutral' : 'good';
}
