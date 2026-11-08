/**
 * **Fitting a picture into the hero's room** — the arithmetic sign-in's deck (#786) and sign-up's
 * podium (#788) share: the room between the wordmark and the headline is whatever those two leave
 * (`StageHero`), so it is **measured** (`useMeasuredRoom`), and each picture is drawn at one size of
 * its own and scaled whole into it, never past one ([#786](https://github.com/Raketa02/Raketa/issues/786),
 * [#788](https://github.com/Raketa02/Raketa/issues/788); design system 12.2).
 *
 * No React in any of it, for `stageDeckGeometry`'s reason: a picture that crops on a small phone is a
 * rule about numbers, testable as numbers.
 */

/** A width and a height, in points. */
export interface Size {
  readonly width: number;
  readonly height: number;
}

/** The scale that fits `box` into `room` — the binding direction's, never past one. */
export function scaleInto(room: Size, box: Size): number {
  return Math.min(1, room.width / box.width, room.height / box.height);
}
