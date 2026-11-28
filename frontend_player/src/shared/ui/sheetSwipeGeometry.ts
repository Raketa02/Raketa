/**
 * **The sheet's swipe down** (9.1 as amended by [#816](https://github.com/Rakieta02/Rakieta/issues/816)):
 * three rules, and no React in any of them.
 *
 * Kept apart from `BottomSheet` for `swipeRowGeometry`'s reason: a rule about numbers can be tested
 * as numbers. A rule that lives only inside a `PanResponder` callback can be reached only by
 * driving touches at a rendered tree.
 *
 * - **Which touch is a swipe.** The head holds the close control, so it never claims a touch when
 *   the finger lands, nor on the first point of movement. It claims once the finger has gone
 *   {@link theme.size.sheetSwipe.intent} down **and** further down than across.
 * - **Where the sheet sits.** It follows the finger down exactly, and never rises above where it
 *   stands: a sheet pulled up is a sheet already at its height.
 * - **Whether a release closes it.** Pulled {@link theme.size.sheetSwipe.close} or further, or
 *   flicked down at {@link theme.size.sheetSwipe.fling}, it closes. Otherwise it springs back. A
 *   flick back up never closes it, however far it was pulled first: the player changed their mind.
 *   **A speed counts only from a finger still moving** — one that moved within
 *   {@link theme.size.sheetSwipe.flingWindow} of lifting — because `PanResponder`'s `vy` is the last
 *   move's and never decays: a fast pull that stopped and held would otherwise lift as a flick.
 */

import { theme } from './theme';

/** A finger's travel since the touch began, in points: `PanResponder`'s own `dx` and `dy`. */
export interface SheetTravel {
  readonly dx: number;
  readonly dy: number;
}

/**
 * A finger as it lifts: how far down it has travelled, how fast its last move was going (`vy`), and
 * how long it has been `still` since that move, in milliseconds.
 */
export interface SheetRelease {
  readonly dy: number;
  readonly vy: number;
  readonly still: number;
}

const { intent: INTENT, close: CLOSE, fling: FLING, flingWindow: WINDOW } = theme.size.sheetSwipe;

/** Whether this move makes the touch a swipe down on the sheet's head. A tie goes across. */
export function claimsTheSheetSwipe({ dx, dy }: SheetTravel): boolean {
  return dy >= INTENT && dy > Math.abs(dx);
}

/** How far below its place the sheet sits for a finger `dy` down. */
export function sheetDrop(dy: number): number {
  return Math.max(0, dy);
}

/** Whether the sheet closes when the finger lifts. */
export function closesOnRelease({ dy, vy, still }: SheetRelease): boolean {
  const moving = still <= WINDOW ? vy : 0;
  return moving >= FLING || (dy >= CLOSE && moving > -FLING);
}
