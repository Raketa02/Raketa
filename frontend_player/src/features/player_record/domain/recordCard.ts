/**
 * **The one division the record card makes** ([#385](https://github.com/Raketa02/Raketa/issues/385)).
 *
 * The rule about which rows it may print went with the strands it filtered
 * ([#660](https://github.com/Raketa02/Raketa/issues/660)): the card is Player reliability's four
 * counts now, served as counts, and every one of them is drawn. What is left is variety's share.
 *
 * ## The share is this client's, and it is the only arithmetic on the sheet
 *
 * Opponent variety crosses as **two counts and no percentage**, deliberately: the counts above it
 * print their raw pairs because nine of nine and forty of forty are different claims, so
 * publishing a bare share would break the rule the card makes about itself.
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

import type { OpponentVariety } from './playerRecord';

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
