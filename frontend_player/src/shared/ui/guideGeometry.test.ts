/**
 * The guide's arithmetic (design-system 9.4): where the spotlight's hole is cut, which side of it
 * the bubble stands on, and where the bubble's arrow points. Numbers in, numbers out — the
 * component only draws them.
 */

import { guideLayout } from './guideGeometry';
import { theme } from './theme';

const WINDOW = { width: 390, height: 844 };
const PAD = theme.space.xs;
const GAP = theme.space.md;
const GUTTER = theme.size.gutter;
const ARROW = theme.size.popoverArrow;

/** The level figure on *Your rating*, near the top-left of the dark card. */
const LEVEL = { x: 33, y: 150, width: 120, height: 70 };

describe('the guide’s layout', () => {
  it('cuts the hole around the target, grown on every side', () => {
    const layout = guideLayout(LEVEL, WINDOW);

    expect(layout?.hole).toEqual({
      x: LEVEL.x - PAD,
      y: LEVEL.y - PAD,
      width: LEVEL.width + 2 * PAD,
      height: LEVEL.height + 2 * PAD,
    });
  });

  it('keeps the hole inside the window when the target touches an edge', () => {
    const layout = guideLayout({ x: 0, y: 2, width: 390, height: 40 }, WINDOW);

    expect(layout?.hole).toEqual({ x: 0, y: 0, width: 390, height: 2 + 40 + PAD });
  });

  it('stands the bubble under a target in the upper half, the content’s width across', () => {
    const layout = guideLayout(LEVEL, WINDOW);

    expect(layout?.bubble).toEqual({
      below: true,
      top: LEVEL.y + LEVEL.height + PAD + GAP,
      left: GUTTER,
      width: WINDOW.width - 2 * GUTTER,
    });
  });

  it('stands the bubble over a target in the lower half, so it never runs off the bottom', () => {
    const low = { x: 33, y: 600, width: 120, height: 70 };

    const layout = guideLayout(low, WINDOW);

    expect(layout?.bubble).toEqual({
      below: false,
      bottom: WINDOW.height - (low.y - PAD) + GAP,
      left: GUTTER,
      width: WINDOW.width - 2 * GUTTER,
    });
  });

  it('points the arrow at the middle of the hole', () => {
    const layout = guideLayout(LEVEL, WINDOW);

    const middle = LEVEL.x + LEVEL.width / 2;
    expect(layout?.arrowLeft).toBe(middle - GUTTER - ARROW / 2);
  });

  it('keeps the arrow off the bubble’s rounded corners for a target at the very edge', () => {
    const ring = { x: 370, y: 150, width: 20, height: 20 };

    const layout = guideLayout(ring, WINDOW);

    const width = WINDOW.width - 2 * GUTTER;
    expect(layout?.arrowLeft).toBe(width - theme.radius.popover - ARROW);
  });

  it('has no layout for a target it could not measure', () => {
    // The test renderer never answers a measurement, and a view not yet laid out answers zeros:
    // either way there is nothing to cut a hole around, and the bubble stands in the middle.
    expect(guideLayout(undefined, WINDOW)).toBeUndefined();
    expect(guideLayout({ x: 0, y: 0, width: 0, height: 0 }, WINDOW)).toBeUndefined();
  });
});
