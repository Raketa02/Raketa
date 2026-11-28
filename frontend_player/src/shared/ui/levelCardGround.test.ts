/**
 * **The Same level card's ground, computed** — the dark card of Home's *Same competitive level
 * players* row, which the theme fences as that card's alone, and every ratio its comment states
 * ([#802](https://github.com/Rakieta02/Rakieta/issues/802), [Part 16](../../../docs/design-system.md#part-16--amendments-after-locking)
 * 2026-11-14).
 *
 * The app's sixth dark surface, so this is 2.5's row for it: what sits on it — white, volt, the game
 * cards' three forecast inks, and the on-dark tiny text — derived rather than typed, so a nudge to
 * any colour goes red here rather than in somebody's eyes. `stageGround.test.ts`'s shape.
 */

import { composite, contrast, hueAngle, hueDistance, parse } from '@/test-support/contrast';

import { theme } from './theme';

const ratio = (a: string, b: string) => contrast(parse(a).rgb, parse(b).rgb);

/** A translucent colour as it lands on an opaque one. */
const over = (translucent: string, ground: string) => {
  const { rgb, alpha } = parse(translucent);
  return composite(rgb, alpha, parse(ground).rgb);
};

/** WCAG 2.1: AA for text at 4,5:1, and 3:1 for large text and for a mark (1.4.3, 1.4.11). */
const AA = 4.5;
const LARGE = 3;

describe('the Same level card’s ground', () => {
  const GROUND = theme.color.levelCardGround;

  it('is night’s family, as every dark ground before it is', () => {
    const ground = hueAngle(parse(GROUND).rgb);
    expect(Math.round(ground)).toBe(198);
    expect(hueDistance(ground, hueAngle(parse(theme.color.night).rgb))).toBeLessThan(5);
  });

  it('carries the names, the mark and the volt fill as its comment says', () => {
    expect(ratio(theme.color.surface, GROUND)).toBeCloseTo(15.76, 1);
    expect(ratio(theme.color.volt, GROUND)).toBeCloseTo(12.57, 1);
  });

  /**
   * **The reason this ground exists**: the game cards' three inks are the figure's colours, and on
   * `night` the green falls under large text's 3:1. The figure is `num.xl`, 22pt — large text.
   */
  it('carries the game cards’ forecast inks at large text’s 3:1, where night cannot', () => {
    expect(ratio(theme.color.gameGreen, theme.color.night)).toBeLessThan(LARGE);
    expect(ratio(theme.color.gameGreen, GROUND)).toBeCloseTo(3.41, 1);
    expect(ratio(theme.color.gameAmber, GROUND)).toBeCloseTo(8.94, 1);
    expect(ratio(theme.color.gameRed, GROUND)).toBeCloseTo(3.48, 1);
    for (const ink of [theme.color.gameGreen, theme.color.gameAmber, theme.color.gameRed]) {
      expect(ratio(ink, GROUND)).toBeGreaterThanOrEqual(LARGE);
    }
  });

  it('carries the levels, the gap, the sport and the bands in onDarkTiny at AA', () => {
    const tiny = over(theme.color.onDarkTiny, GROUND);
    expect(contrast(tiny, parse(GROUND).rgb)).toBeCloseTo(7.97, 1);
    expect(contrast(tiny, parse(GROUND).rgb)).toBeGreaterThanOrEqual(AA);
  });
});
