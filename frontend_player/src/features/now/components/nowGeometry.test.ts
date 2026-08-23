/**
 * Now's geometry, at the four widths the delta was measured at.
 *
 * `deltas/native-kit.md` was built on the real kit and measured at 320, 375, 393
 * and 430 pt, so those are the widths asserted here — the point of every rule below
 * is that it holds *at every width*, which one number cannot show.
 */

import { theme } from '@/shared/ui';

import {
  GUTTER,
  STRIP_GAP,
  STRIP_PEEK,
  contentWidth,
  railCardWidth,
  stripSnapInterval,
} from './nowGeometry';

/** The widths the prototype was built and measured at. */
const WIDTHS = [320, 375, 393, 430];

describe('content width', () => {
  it('is screen width − 30 at every width', () => {
    for (const width of WIDTHS) {
      expect(contentWidth(width)).toBe(width - 30);
    }
  });

  it('is uncapped and never centred', () => {
    // §329's 362 is `392 − 30`, and the 392 is the width of the *picture of a phone*
    // the prototype draws itself inside. Capping would put paper margins on a 430pt
    // phone to preserve a measurement of a stage prop.
    expect(contentWidth(430)).toBeGreaterThan(362);
    expect(contentWidth(430) - contentWidth(393)).toBe(430 - 393);
  });

  it('reads its one number from the theme, which already states the rule', () => {
    expect(GUTTER).toBe(theme.space.lg);
  });
});

describe('the strip', () => {
  it('peeks by the same amount at every width', () => {
    // The peek does not depend on the card width at all, which is why it survives a
    // 320pt phone untouched while a ratio-sized rail does not.
    const peeks = WIDTHS.map((width) => width - (GUTTER + contentWidth(width) + STRIP_GAP));

    expect(new Set(peeks)).toEqual(new Set([STRIP_PEEK]));
  });

  it('peeks by gutter − gap, and by nothing else', () => {
    expect(STRIP_PEEK).toBe(GUTTER - STRIP_GAP);
    // Six, where the delta's table computes five from the prototype's ungridded gap
    // of 10. This app normalised that gap onto its 3pt grid as `space.sm` when
    // ADR-0012 was written, and `design-system.md` Part 8 already fixes the Strip's
    // gap at 9 — so the consequence of *this app's* gap is 6. Reported on #86.
    expect(STRIP_PEEK).toBe(6);
  });

  it('does not apply the rail’s ratio', () => {
    // `size.railCardRatio` is correct for `.mrail`, which `UI` §D5 says in as many
    // words is *not used by Now*. Applied to the strip it shows a quarter of the
    // next card's **contents**, which reads as two cards rather than as a peek.
    for (const width of WIDTHS) {
      expect(stripSnapInterval(width)).toBe(contentWidth(width) + STRIP_GAP);
      expect(stripSnapInterval(width)).not.toBe(railCardWidth(width) + STRIP_GAP);
    }
  });
});

describe('a shelf’s rail', () => {
  it('does take the ratio, because a shelf is the component it was written for', () => {
    for (const width of WIDTHS) {
      expect(railCardWidth(width)).toBe(Math.round(contentWidth(width) * theme.size.railCardRatio));
      expect(railCardWidth(width)).toBeLessThan(contentWidth(width));
    }
  });
});
