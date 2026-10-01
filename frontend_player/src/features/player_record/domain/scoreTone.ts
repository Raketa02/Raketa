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

/**
 * Where a record below the floor stops being a wobble and starts being a risk — the one step the
 * score tag adds to the ladder above, and **only below the floor**.
 */
export const SCORE_RISKY = 50;

/**
 * **The score tag's four bands** — the ladder above with its bottom step cut in two, for the one
 * surface that tints the figure itself: the score tag on Members' rows.
 *
 * - `strong` (90–100) — shows up, answers, confirms: the best partners.
 * - `ordinary` (70–89) — nothing to flag.
 * - `wobbly` (50–69) — late answers, a dropout: worth a look before approving or inviting.
 * - `risky` (0–49) — no-shows on the record.
 *
 * **A refinement of `scoreTone`, never a second ladder**: the two steps it shares are read off
 * the same two constants, so `strong` is always `good`, `ordinary` always `neutral`, and both of
 * the new bands are `poor`. A tag cannot turn amber where a meter on the record stays neutral.
 */
export type ScoreBand = 'strong' | 'ordinary' | 'wobbly' | 'risky';

export function scoreBand(score: number): ScoreBand {
  const tone = scoreTone(score);
  if (tone === 'good') return 'strong';
  if (tone === 'neutral') return 'ordinary';
  return score < SCORE_RISKY ? 'risky' : 'wobbly';
}
