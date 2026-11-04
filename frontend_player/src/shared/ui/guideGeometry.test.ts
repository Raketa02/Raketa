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
      side: 'below',
      top: LEVEL.y + LEVEL.height + PAD + GAP,
      left: GUTTER,
      width: WINDOW.width - 2 * GUTTER,
    });
  });

  it('stands the bubble over a target in the lower half, so it never runs off the bottom', () => {
    const low = { x: 33, y: 600, width: 120, height: 70 };

    const layout = guideLayout(low, WINDOW);

    expect(layout?.bubble).toEqual({
      side: 'above',
      bottom: WINDOW.height - (low.y - PAD) + GAP,
      left: GUTTER,
      width: WINDOW.width - 2 * GUTTER,
    });
  });

  it('points the arrow at the middle of the hole', () => {
    const layout = guideLayout(LEVEL, WINDOW);

    const middle = LEVEL.x + LEVEL.width / 2;
    expect(layout?.arrow).toBe(middle - GUTTER - ARROW / 2);
  });

  it('points the arrow at what the step names inside the hole — the figure’s ⓘ mark', () => {
    // The level's head stretches across its column, and its middle is empty dark card; the mark
    // beside the eyebrow is what the bubble is about.
    const mark = { x: 120, y: 152, width: 20, height: 20 };

    const layout = guideLayout(LEVEL, WINDOW, mark);

    expect(layout?.arrow).toBe(mark.x + mark.width / 2 - GUTTER - ARROW / 2);
  });

  it('points the arrow at the hole’s middle when what it names has not been laid out', () => {
    const layout = guideLayout(LEVEL, WINDOW, { x: 0, y: 0, width: 0, height: 0 });

    expect(layout?.arrow).toBe(LEVEL.x + LEVEL.width / 2 - GUTTER - ARROW / 2);
  });

  it('keeps the arrow off the bubble’s rounded corners for a target at the very edge', () => {
    const ring = { x: 370, y: 150, width: 20, height: 20 };

    const layout = guideLayout(ring, WINDOW);

    const width = WINDOW.width - 2 * GUTTER;
    expect(layout?.arrow).toBe(width - theme.radius.popover - ARROW);
  });

  describe('beside its mark, when the step asks', () => {
    /** The level on a 430pt phone: its head and number, the ⓘ at the head's right end. */
    const WIDE = { width: 430, height: 932 };
    const LEVEL_FIGURE = { x: 30, y: 150, width: 111, height: 64 };
    const LEVEL_MARK = { x: 121, y: 150, width: 20, height: 20 };

    it('stands to the right of the hole, out to the gutter, its arrow level with the mark', () => {
      const layout = guideLayout(LEVEL_FIGURE, WIDE, LEVEL_MARK, true);

      const holeRight = LEVEL_FIGURE.x + LEVEL_FIGURE.width + PAD;
      const left = holeRight + GAP;
      expect(layout?.bubble).toEqual({
        side: 'right',
        top: expect.any(Number),
        left,
        width: WIDE.width - GUTTER - left,
      });
      // The arrow's middle, from the window's top, is the mark's.
      const top = layout?.bubble.side === 'right' ? layout.bubble.top : NaN;
      expect(top + (layout?.arrow ?? NaN) + ARROW / 2).toBe(LEVEL_MARK.y + LEVEL_MARK.height / 2);
    });

    it('stands under the hole when the room beside is narrower than a bubble can be', () => {
      // A 320pt phone: what is left right of the level is under `guideBesideMin`.
      const narrow = { width: 320, height: 568 };

      const layout = guideLayout(LEVEL_FIGURE, narrow, LEVEL_MARK, true);

      expect(layout?.bubble.side).toBe('below');
    });

    it('stands under the hole when its mark did not measure', () => {
      const layout = guideLayout(LEVEL_FIGURE, WIDE, { x: 0, y: 0, width: 0, height: 0 }, true);

      expect(layout?.bubble.side).toBe('below');
    });
  });

  it('has no layout for a target it could not measure', () => {
    // The test renderer never answers a measurement, and a view not yet laid out answers zeros:
    // either way there is nothing to cut a hole around, and the bubble stands in the middle.
    expect(guideLayout(undefined, WINDOW)).toBeUndefined();
    expect(guideLayout({ x: 0, y: 0, width: 0, height: 0 }, WINDOW)).toBeUndefined();
  });
});
