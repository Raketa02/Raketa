/**
 * Now's geometry on the native kit.
 *
 * `docs/specs/now/deltas/native-kit.md` governs this file and settles two things
 * the source UI documents got wrong by measuring the harness instead of the app.
 *
 * **Content width is `screen width − 30`, at every width, uncapped and never
 * centred.** The 362 in the production spec is not a design value: it is
 * `392 − 30`, and 392 is the width of the *picture of a phone* the prototype draws
 * itself inside. `ADR-0012` Part 0.1 already ruled that frame to be harness, and
 * `theme.space.lg` already says the replacement rule verbatim — *"THE HORIZONTAL
 * PAGE GUTTER. Content width = screen width − 30."* Capping would put paper
 * margins on a 430pt phone to preserve a measurement of a stage prop.
 *
 * **The strip's peek is `gutter − gap`, and `size.railCardRatio` must not be
 * applied to it.** The ratio is correct for `.mrail`, the component it was written
 * for, and `UI` §D5 says in as many words that `.mrail` is *"not used by Now"*.
 * Applied here it would produce a card 94pt narrower than the column at 430,
 * showing a quarter of the *next card's contents* — which reads as two cards, not
 * as a peek. Now's strip is `.hstrip`: a child that is the full content width, in
 * a strip bled to the frame edge, so the peek does not depend on the card width at
 * all and survives 320pt untouched.
 *
 * **The peek is 6pt here and the delta's table says 5.** The delta computes
 * `15 − 10` from the prototype's CSS gap; this app's design system normalised that
 * gap onto the 3pt grid as `space.sm` = 9 when `ADR-0012` was written, and
 * `design-system.md` Part 8 already fixes the Strip's gap at 9. The delta's own
 * instruction is that the peek *"is a consequence of the gutter and the gap rather
 * than a number of its own"* — which is exactly what is implemented; the
 * consequence of **this app's** gap is 6. Reported on `Raketa02/Raketa#86` rather
 * than resolved by putting an off-grid 10 into a locked design system.
 *
 * **The 320pt overflow is accepted, not clamped.** The fullest card's action row
 * falls below the fold on the narrowest phone, and clamping the fact list would
 * delete the line that tells a player she can still get out. Now is a status
 * surface before a search box: on this screen reading is the primary act.
 */

import { theme } from '@/shared/ui';

/** The gutter, both sides. One number, and the only one content width depends on. */
export const GUTTER = theme.size.gutter;

/** The gap between strip children, per `design-system.md` Part 8. */
export const STRIP_GAP = theme.space.sm;

/**
 * How much of the next card shows, at every screen width.
 *
 * A consequence of the gutter and the gap, never a constant of its own — which is
 * why it does not move between a 320pt phone and a 430pt one, and why nothing here
 * reads a card width.
 */
export const STRIP_PEEK = GUTTER - STRIP_GAP;

/** `screen width − 30`. Uncapped, so the column grows with the phone. */
export function contentWidth(screenWidth: number): number {
  return screenWidth - GUTTER * 2;
}

/** One flick moves one card: the child plus the gap that follows it. */
export function stripSnapInterval(screenWidth: number): number {
  return contentWidth(screenWidth) + STRIP_GAP;
}

/**
 * A **shelf** card's width — `size.railCardRatio` of the column.
 *
 * The rail's own geometry (`design-system.md` §7.7), correct for the component it
 * was written for: a quarter of the next card showing is what says *there are
 * more*. What the delta forbids is applying this ratio to the **strip** above,
 * whose child is the whole column; a shelf is a rail and takes the rail's number.
 */
export function railCardWidth(screenWidth: number): number {
  return Math.round(contentWidth(screenWidth) * theme.size.railCardRatio);
}
