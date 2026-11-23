/**
 * **The drawn splash's ground, computed** — the two colours the theme fences as the splash's alone
 * ([ADR-0209](../../../../docs/adr/0209-a-drawn-splash-opens-the-app-and-startup-runs-behind-it.md),
 * [Part 16](../../docs/design-system.md#part-16--amendments-after-locking) 2026-11-23).
 *
 * `yesGround.test.ts`'s shape: the figures are derived rather than typed, so a nudge to either
 * colour goes red here rather than in somebody's eyes — the brief's two values are the theme's to
 * spell, and these ratios pin them. What will sit on the ground is the lockup's — the word in white
 * and the dot in `volt` (#855) — so those are the ratios that matter.
 */

import { contrast, hueAngle, hueDistance, parse } from '@/test-support/contrast';

import { theme } from './theme';

const ratio = (a: string, b: string) => contrast(parse(a).rgb, parse(b).rgb);

/** WCAG 2.1's AAA for text. */
const AAA = 7;

describe('the drawn splash’s ground', () => {
  const CENTRE = theme.color.splashGroundCentre;
  const EDGE = theme.color.splashGroundEdge;

  it('is a pair of its own: neither is night nor the yes screen’s', () => {
    expect([CENTRE, EDGE]).not.toContain(theme.color.night);
    expect([CENTRE, EDGE]).not.toContain(theme.color.yesGroundCentre);
    expect([CENTRE, EDGE]).not.toContain(theme.color.yesGroundEdge);
  });

  it('is night’s family, and the edge is the centre gone darker rather than a second hue', () => {
    const centre = hueAngle(parse(CENTRE).rgb);
    expect(hueDistance(centre, hueAngle(parse(EDGE).rgb))).toBeLessThan(2);
    expect(hueDistance(centre, hueAngle(parse(theme.color.night).rgb))).toBeLessThan(5);
  });

  it('carries a white word past AAA on both ends of the glow', () => {
    expect(ratio(theme.color.surface, CENTRE)).toBe(10.37);
    expect(ratio(theme.color.surface, EDGE)).toBe(14.92);
    expect(ratio(theme.color.surface, CENTRE)).toBeGreaterThanOrEqual(AAA);
  });

  it('carries the volt dot past AAA on both ends of the glow', () => {
    expect(ratio(theme.color.volt, CENTRE)).toBe(8.27);
    expect(ratio(theme.color.volt, EDGE)).toBe(11.9);
    expect(ratio(theme.color.volt, CENTRE)).toBeGreaterThanOrEqual(AAA);
  });
});
