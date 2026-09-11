/**
 * **The two rules behind the record card** — which rows it may print, and the one division it
 * makes ([#385](https://github.com/Raketa02/Raketa/issues/385)).
 *
 * ## The heading is a promise about authorship, and it is kept here
 *
 * *Counted by the system, not written by people* is the rule the card enforces rather than a
 * label on it. Five of the six strands are ratios the platform observed; `SPORTSMANSHIP` is
 * what other players typed, and it has a block of its own under a heading that says so. The
 * contract already states that row never crosses in this list — but a heading that is only true
 * while a remote service keeps its word is a heading that goes quietly false, so the one row
 * that would break it is dropped here and the promise is kept by construction.
 *
 * **The row could not be drawn honestly even if the heading permitted it.** Every row on this
 * card prints a raw pair, and stars are an average out of five rather than a count of
 * opportunities that went one way — there is no *`4,8` of what*. That is the same fact the
 * decisions record states from the other end when it keeps the figure out of the pill: *a star
 * average is not a ratio out of a hundred, so it cannot be a strand in a weighted mean over
 * ratios.*
 *
 * **Nothing else is filtered, and that is the other half of the rule.** `KEEPS_PLANS` and
 * `SETTLES_UP` have no provider on this platform today, and both are ratios the system counts
 * that would enter the published blend: the day either lights up it draws. Taking the whole
 * absent half would have made the pill and the rows disagree the moment it did, silently, on a
 * card whose entire argument is that the figure above is the mean of the figures below — where
 * dropping a strand the pill was never allowed to contain cannot.
 *
 * ## The share is this client's, and it is the only arithmetic on the sheet
 *
 * Opponent variety crosses as **two counts and no percentage**, deliberately: the card argues
 * three rows above that a perfect record over nine games and one over forty are different
 * claims, so publishing a bare share would break the rule the card had just made about itself.
 * The division is one line and it is here rather than in the drawing, because a figure computed
 * where it is printed is a figure the next surface computes again.
 *
 * **And the ceiling is here too, because a doubles game is played against three people.** The
 * pair counts *everybody who was on a court with them, partner included* over the games they
 * were on the court for, so ten doubles evenings against twenty-five people is a division that
 * comes out at 250 — arithmetically fine and unreadable as a share. The definition's own worked
 * example is a singles one (*two games against two people is at 100 %*), which is where the
 * ceiling comes from: 100 already means *as widely as this gets*, and a reader learns nothing
 * from 250 that they did not learn from 100. Nothing is hidden by it either — the raw pair is
 * printed beside the figure, which is the whole reason the pair is printed.
 *
 * It is clamped **here rather than where it is drawn**, on `Meter`'s own argument for clamping
 * its share: a value must land in the same place everywhere, and a clamp per caller is how one
 * number ends up drawn two ways.
 *
 * The rounding is **not** here. Every percentage in this app is written by one formatter, and a
 * rule that rounded before handing the number over would be that formatter's decision taken
 * twice.
 */

import type { OpponentVariety, StrandRow } from './playerRecord';

/**
 * The rows the card draws, in the order they were served — see the module note for the one
 * that is not among them.
 */
export function countedRows(strands: readonly StrandRow[]): readonly StrandRow[] {
  return strands.filter((row) => row.strand !== 'SPORTSMANSHIP');
}

/** What the share means at its top. */
const WIDEST = 100;

/**
 * The share, out of a hundred and unrounded.
 *
 * **There is no cap any more, and its removal is the point.** The denominator was a count of
 * *games*, which is only divisible in singles: a doubles evening put three people on the court
 * and published `3 of 1`, so this clamped at a hundred and drew a full bar over a pair that read
 * as nonsense. The wire now counts **times on a court**, the backend refuses a pair where the
 * numerator exceeds it, and a clamp here would only hide the next such defect.
 *
 * `timesOnCourt` is never nought: the whole field is **omitted** where no counted game has ever
 * been recorded, which is the absence this sheet spells everywhere and never a `0 of 0`.
 */
export function varietyShare(variety: OpponentVariety): number {
  return (variety.distinctOpponents / variety.timesOnCourt) * WIDEST;
}
