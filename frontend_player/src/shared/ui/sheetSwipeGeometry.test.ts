/**
 * The sheet's swipe down, held to the numbers (9.1 as amended by #816).
 *
 * **Which touch is a swipe** is the rule that matters most. The head holds the close control, and
 * a tap on it has to stay a tap. So the head claims a touch only once it has gone a fingertip
 * down, and further down than across. **Where the sheet sits** under the finger, and **whether a
 * release closes it**, are the other two rules.
 */

import { claimsTheSheetSwipe, closesOnRelease, sheetDrop } from './sheetSwipeGeometry';
import { theme } from './theme';

const { intent: INTENT, close: CLOSE, fling: FLING, flingWindow: WINDOW } = theme.size.sheetSwipe;

describe('which touch is a swipe down', () => {
  it('claims a move down once it has travelled the intent distance', () => {
    expect(claimsTheSheetSwipe({ dx: 0, dy: INTENT })).toBe(true);
    expect(claimsTheSheetSwipe({ dx: 4, dy: INTENT + 30 })).toBe(true);
  });

  it('claims nothing short of it, so a tap on the close stays a tap', () => {
    expect(claimsTheSheetSwipe({ dx: 0, dy: INTENT - 1 })).toBe(false);
    expect(claimsTheSheetSwipe({ dx: 0, dy: 0 })).toBe(false);
  });

  it('never claims a move up, or one more across than down', () => {
    expect(claimsTheSheetSwipe({ dx: 0, dy: -40 })).toBe(false);
    expect(claimsTheSheetSwipe({ dx: 30, dy: 30 })).toBe(false);
    expect(claimsTheSheetSwipe({ dx: -30, dy: 29 })).toBe(false);
    expect(claimsTheSheetSwipe({ dx: 29, dy: 30 })).toBe(true);
  });
});

describe('where the sheet sits under the finger', () => {
  it('follows the finger down, and never rises above where it stands', () => {
    expect(sheetDrop(40)).toBe(40);
    expect(sheetDrop(0)).toBe(0);
    expect(sheetDrop(-25)).toBe(0);
  });
});

describe('whether a release closes it', () => {
  it('closes once the sheet has been pulled the close distance', () => {
    expect(closesOnRelease({ dy: CLOSE, vy: 0, still: 0 })).toBe(true);
    expect(closesOnRelease({ dy: CLOSE - 1, vy: 0, still: 0 })).toBe(false);
  });

  it('closes on a flick down, however short', () => {
    expect(closesOnRelease({ dy: INTENT, vy: FLING, still: 0 })).toBe(true);
    expect(closesOnRelease({ dy: INTENT, vy: FLING - 0.01, still: 0 })).toBe(false);
  });

  it('never closes on a flick back up', () => {
    expect(closesOnRelease({ dy: CLOSE + 10, vy: -FLING, still: 0 })).toBe(false);
  });

  /**
   * `PanResponder`'s `vy` is the last move's and never decays, so a finger that pulled fast, then
   * stopped and held, still lifts with it. A speed counts only from a finger still moving.
   */
  it('reads no flick from a finger that stopped before it lifted', () => {
    expect(closesOnRelease({ dy: INTENT, vy: FLING * 2, still: WINDOW })).toBe(true);
    expect(closesOnRelease({ dy: INTENT, vy: FLING * 2, still: WINDOW + 1 })).toBe(false);
    // And a stopped pull back up is a pull that rests where it is: past the distance, it closes.
    expect(closesOnRelease({ dy: CLOSE + 10, vy: -FLING, still: WINDOW + 1 })).toBe(true);
  });
});
