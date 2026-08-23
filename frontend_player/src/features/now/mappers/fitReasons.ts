/**
 * The ten reasons behind the fit badge, and the two lines that stand in for it.
 *
 * The badge always prints a number, so a card is never mute about why it is
 * suggested; up to three of these answer *why this one*. The wire carries a term
 * **code** and a typed fact payload and never a weight and never a sentence —
 * retuning the engine is a server change, and rewording a reason is this app's.
 *
 * **Coverage is never one of these.** It is not a number the player sees, in any
 * form: `ADR-0037` is explicit that an uncertain estimate becomes *words in a
 * reason line* and never a second gauge on the card.
 *
 * **An entry is a function of the whole reason**, not of the code alone.
 * `FitReasonResponse` carries the code today; `Raketa02/Raketa#75` puts the
 * typed facts beside it — the aimed-at level, which side a skill mismatch fell
 * on — and a function already shaped to receive them widens without touching
 * ten call sites.
 */

import type { AssertTrue, FitReason, IsClosedUnion, TermCode } from './codes';

export type FitReasonEntry = (reason: FitReason) => string;

/**
 * Total over the ten terms the engine can emit.
 *
 * Ten and not seven: the shipped engine split *time and travel*, added
 * `match_viability` and `ladder_qualification`, and turned a modifier into
 * `familiarity`. The enum lists the terms that **exist**, so there is no longer
 * a code this client could hold a row for and never receive.
 */
export const FIT_REASON_COPY: Readonly<Record<TermCode, FitReasonEntry>> = {
  skill_overlap: () => 'Your level overlaps the level this match is aimed at.',
  predicted_balance: () => 'The sides should come out even.',
  time_fit: () => 'It is at a time you play.',
  match_viability: () => 'This one looks likely to actually happen.',
  group_reliability: () => 'This group turns up.',
  travel: () => 'It is close to you.',
  ladder_qualification: () => 'It counts towards your ladder.',
  price: () => 'It is within what you usually pay.',
  match_type: () => 'It is the format you play.',
  familiarity: () => 'You have played these players before.',
};

/** Fails to compile if `TermCode` ever arrives as a bare string. */
export type TermCodeIsClosed = AssertTrue<IsClosedUnion<TermCode>>;

/**
 * What the card says where the badge's claim would be, for a player the platform
 * cannot place at this sport.
 *
 * `ADR-0037`: skill overlap is the largest term at 24 of 100 points and is the
 * one thing missing for such a viewer, so printing 91 to her would be
 * flattery through absence. The score still ranks her list — only the claim is
 * withheld.
 */
export const FIT_BADGE_WITHHELD = 'No fit yet — we cannot place you at this sport.';

/**
 * What an unsure estimate says instead of a confidence percentage.
 *
 * A warning, never a number: a second gauge on the card would be the thing
 * `ADR-0037` refuses, and coverage is never displayed at all.
 */
export const FIT_UNSURE_WARNING = 'Early days for this match — this is a rough guess.';

/** The sentence for one reason, or `undefined` for a term this build has never heard of. */
export function fitReasonSentence(reason: FitReason): string | undefined {
  const entry: FitReasonEntry | undefined = (
    FIT_REASON_COPY as Readonly<Record<string, FitReasonEntry | undefined>>
  )[reason.code];
  return entry === undefined ? undefined : entry(reason);
}
