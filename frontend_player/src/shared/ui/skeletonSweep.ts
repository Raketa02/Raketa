/**
 * **Where the skeleton's band stands** (design system 5.6; PRD #867,
 * [#870](https://github.com/Rakieta02/Rakieta/issues/870)) — `Skeleton`'s numbers, pure, so they are
 * tested as numbers: Jest has no layout.
 *
 * **One band crosses every shape on a screen at once.** It is a stripe of light leaning
 * `motion.skeleton.tilt` degrees off upright — higher up, further right — that crosses the ground
 * (the screen's skeleton is measured against one `SkeletonGround`) from left to right once a sweep.
 * Each shape draws only its own piece of it: a **sheet**, as tall as the shape and just wide enough
 * to hold the band across that height, carrying the gradient. The sheet moves sideways by two
 * numbers added together:
 *
 * - **`sweepShift`**, the one moving part — the same for every shape on the ground, a function of the
 *   clock alone, so a `transform` on the UI thread and nothing else;
 * - **`shapeOffset`**, the shape's own — where it stands on the ground, read once from its layout.
 *
 * So every shape shows the band where the screen-wide band would be (`bandCentreAt`), and the shapes
 * need nothing from each other but the clock.
 *
 * **The band's width is Shimmer's** (Facebook's `shimmer-android`, read from its source,
 * `Shimmer.java` and `ShimmerDrawable.java`): a `LINEAR` gradient as wide as the frame
 * (`widthRatio = 1f`) whose light runs from 0,25 to 0,75 of it (`dropoff = 0.5f`, `intensity = 0f`)
 * — half the frame, here half the ground (the screen's width), measured across its stripes. Its tilt and its 1000 ms are
 * the theme's, from the same source. **Its travel is not Shimmer's**: that runs the band's centre
 * from half a frame and more past the left edge to as far past the right, so a part of every cycle
 * has no band on screen. The loading shimmer log asks for *no pause* (Q24), so here the band enters
 * as it leaves: it starts with its right edge on the ground's top-left corner and ends with its left
 * edge on the bottom-right one, every row of the ground crossed in every cycle.
 */

import { theme } from './theme';

/** The band's width as a share of the ground's, across its stripes — Shimmer's `dropoff` (see above). */
export const SWEEP_BAND = 0.5;

/** The ground the band crosses — its own size, the screen's width below a screen's header. */
export interface SweepScreen {
  readonly width: number;
  readonly height: number;
}

/** The band on one screen: everything a shape needs to draw its piece of it. */
export interface SweepGeometry {
  /** The band's width across its stripes, in points. */
  readonly band: number;
  readonly cos: number;
  readonly sin: number;
  readonly tan: number;
  /** How far the band's centre moves across its stripes in one sweep. */
  readonly travel: number;
}

export function sweepGeometry(
  screen: SweepScreen,
  tilt: number = theme.motion.skeleton.tilt,
): SweepGeometry {
  const lean = (tilt * Math.PI) / 180;
  const cos = Math.cos(lean);
  const sin = Math.sin(lean);
  const band = screen.width * SWEEP_BAND;
  // Across the stripes, the screen spans 0 (its top-left corner) to its bottom-right corner's
  // reach; the band travels from wholly before the one to wholly past the other.
  return {
    band,
    cos,
    sin,
    tan: sin / cos,
    travel: screen.width * cos + screen.height * sin + band,
  };
}

/** Where the band's centre stands across its stripes, `progress` (0–1) into a sweep. */
function across(progress: number, g: SweepGeometry): number {
  'worklet';
  return -g.band / 2 + progress * g.travel;
}

/**
 * **The one moving part**: how far every shape's sheet moves sideways, `progress` into a sweep. The
 * same for every shape on the ground — the band's travel across its stripes, turned into a sideways
 * move.
 */
export function sweepShift(progress: number, g: SweepGeometry): number {
  'worklet';
  return across(progress, g) / g.cos;
}

/** **The band's centre on the ground**, sideways, at a height — where every shape must show it. */
export function bandCentreAt(progress: number, y: number, g: SweepGeometry): number {
  return (across(progress, g) - y * g.sin) / g.cos;
}

/** A shape's sheet: its width, where the band's centre crosses its top, and its gradient's ends. */
export interface BandSheet {
  readonly width: number;
  /** Sideways from the sheet's left edge, where the band's centre crosses its top. */
  readonly centreTop: number;
  /** The gradient's two ends, in the sheet's points — one band apart, across the stripes. */
  readonly from: { readonly x: number; readonly y: number };
  readonly to: { readonly x: number; readonly y: number };
}

/**
 * **The sheet a shape of this height draws the band on.** The band's centre crosses the sheet's foot
 * half a band in from its left and leans right going up, so the sheet is the band's sideways width
 * plus the lean over the shape's height — the band whole across the shape, and nothing to draw past
 * it: beyond the gradient's ends the sheet is the shape's own tone.
 */
export function bandSheet(height: number, g: SweepGeometry): BandSheet {
  const sideways = g.band / g.cos;
  const centreTop = sideways / 2 + height * g.tan;
  const half = g.band / 2;
  return {
    width: sideways + height * g.tan,
    centreTop,
    from: { x: centreTop - half * g.cos, y: -half * g.sin },
    to: { x: centreTop + half * g.cos, y: half * g.sin },
  };
}

/**
 * **A shape's own part of the move** — where its sheet stands, sideways, at the start of a sweep —
 * read once from where the shape stands on the ground and how tall it is.
 */
export function shapeOffset(
  at: { readonly x: number; readonly y: number },
  height: number,
  g: SweepGeometry,
): number {
  return -at.y * g.tan - at.x - bandSheet(height, g).centreTop;
}
