/**
 * **Where the skeleton's band stands** (PRD #867, [#870](https://github.com/Raketa02/Raketa/issues/870);
 * design system 5.6) — pure numbers, since Jest has no layout. One band crosses the whole ground at
 * once: every shape draws its own piece of it, placed by where the shape stands on the ground, so a
 * shape anywhere shows the band exactly where the screen-wide band would be.
 */

import {
  SWEEP_BAND,
  bandCentreAt,
  bandSheet,
  shapeOffset,
  sweepGeometry,
  sweepShift,
} from './skeletonSweep';
import { theme } from './theme';

/** The user's A32: 384 × 854 points. */
const SCREEN = { width: 384, height: 854 };
const G = sweepGeometry(SCREEN);
const TILT = (theme.motion.skeleton.tilt * Math.PI) / 180;

/**
 * Where a shape draws the band's centre, on the ground, at its own top edge: its own place, plus the
 * sheet's place inside it, plus the centre's place inside the sheet.
 */
function drawnCentre(
  shape: { readonly x: number; readonly y: number; readonly height: number },
  progress: number,
): number {
  const sheet = bandSheet(shape.height, G);
  return shape.x + sweepShift(progress, G) + shapeOffset(shape, shape.height, G) + sheet.centreTop;
}

/** The band's two edges on the ground, at a height: its centre, half its width across either side. */
function edgesAt(progress: number, y: number): { readonly left: number; readonly right: number } {
  const centre = bandCentreAt(progress, y, G);
  const half = G.band / 2 / Math.cos(TILT);
  return { left: centre - half, right: centre + half };
}

describe('the band', () => {
  it('is half the screen wide across its stripes — Shimmer’s dropoff over its width ratio', () => {
    expect(SWEEP_BAND).toBe(0.5);
    expect(G.band).toBe(SCREEN.width / 2);
  });

  it('leans by the theme’s tilt: higher up, further right', () => {
    const top = bandCentreAt(0.5, 0, G);
    const foot = bandCentreAt(0.5, SCREEN.height, G);

    expect(top - foot).toBeCloseTo(SCREEN.height * Math.tan(TILT), 6);
  });
});

describe('one sweep', () => {
  it('starts with the band wholly off the screen’s left edge, at every height', () => {
    for (const y of [0, SCREEN.height / 2, SCREEN.height]) {
      expect(edgesAt(0, y).right).toBeLessThanOrEqual(1e-9);
    }
    // Only just: its right edge touches the top-left corner.
    expect(edgesAt(0, 0).right).toBeCloseTo(0, 6);
  });

  it('ends with the band wholly off the right edge, at every height — no stretch with none on screen', () => {
    for (const y of [0, SCREEN.height / 2, SCREEN.height]) {
      expect(edgesAt(1, y).left).toBeGreaterThanOrEqual(SCREEN.width - 1e-9);
    }
    expect(edgesAt(1, SCREEN.height).left).toBeCloseTo(SCREEN.width, 6);
  });

  it('moves at one speed: equal steps of the clock move the band equal distances', () => {
    const steps = [0, 0.25, 0.5, 0.75, 1].map((progress) => sweepShift(progress, G));
    const moves = steps.slice(1).map((at, index) => at - steps[index]!);

    for (const move of moves) expect(move).toBeCloseTo(moves[0]!, 9);
    expect(moves[0]!).toBeGreaterThan(0);
  });
});

describe('every shape shows the one band', () => {
  const SHAPES = [
    { x: 15, y: 0, height: 31 },
    { x: 15, y: 40, height: 130 },
    { x: 63, y: 240, height: 13 },
    { x: 300, y: 600, height: 38 },
  ];

  it('draws the band’s centre where the screen-wide band has it, whatever the shape’s place', () => {
    for (const progress of [0, 0.3, 0.62, 1]) {
      for (const shape of SHAPES) {
        expect(drawnCentre(shape, progress)).toBeCloseTo(bandCentreAt(progress, shape.y, G), 6);
      }
    }
  });

  it('draws a sheet that holds the band across the shape’s whole height, and no wider', () => {
    const sheet = bandSheet(38, G);
    const horizontal = G.band / Math.cos(TILT);

    // The centre stands half a band in from the sheet's left at its foot, and leans right going up.
    expect(sheet.centreTop).toBeCloseTo(horizontal / 2 + 38 * Math.tan(TILT), 6);
    expect(sheet.width).toBeCloseTo(horizontal + 38 * Math.tan(TILT), 6);
    // The gradient runs across the stripes, one band wide.
    const across = Math.hypot(sheet.to.x - sheet.from.x, sheet.to.y - sheet.from.y);
    expect(across).toBeCloseTo(G.band, 6);
  });
});
