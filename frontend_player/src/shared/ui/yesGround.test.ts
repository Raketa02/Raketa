/**
 * **The yes screen's ground, computed** — the two colours the theme fences as that screen's
 * alone, and every ratio their comments state
 * ([ADR-0166](../../../../docs/adr/0166-a-yes-lands-on-its-own-screen-and-the-room-is-opened-by-a-tap.md)
 * §2, [Part 16](../../../docs/design-system.md#part-16--amendments-after-locking) 2026-09-14).
 *
 * The ground is the app's one dark screen and 2.5's table has no row for it, so this is the row:
 * what sits on it — `volt` for the word, white for the *Later* label over the on-dark fill, the
 * on-dark eyebrow grey for the decorative `vs` — and what each measures on both ends of the glow.
 * `Tag.test.tsx`'s shape: the figures are derived rather than typed, so a nudge to either colour
 * goes red here rather than in somebody's eyes.
 */

import { composite, contrast, hueAngle, hueDistance, parse } from '@/test-support/contrast';

import { theme } from './theme';

const ratio = (a: string, b: string) => contrast(parse(a).rgb, parse(b).rgb);

/** WCAG 2.1: 4.5:1 for text below the large-text threshold, and AAA at 7:1. */
const AA = 4.5;
const AAA = 7;

/** A translucent white as it lands on the glow's centre or edge. */
const over = (translucent: string, ground: string) => {
  const { rgb, alpha } = parse(translucent);
  return composite(rgb, alpha, parse(ground).rgb);
};

describe('the yes screen’s ground', () => {
  const CENTRE = theme.color.yesGroundCentre;
  const EDGE = theme.color.yesGroundEdge;

  it('is night’s family, and the edge is the centre gone darker rather than a second hue', () => {
    const centre = hueAngle(parse(CENTRE).rgb);
    const edge = hueAngle(parse(EDGE).rgb);
    expect(Math.round(centre)).toBe(198);
    expect(hueDistance(centre, edge)).toBeLessThan(2);
    expect(hueDistance(centre, hueAngle(parse(theme.color.night).rgb))).toBeLessThan(5);
  });

  it('carries the word in volt past AAA on both ends of the glow', () => {
    expect(ratio(theme.color.volt, CENTRE)).toBe(9.3);
    expect(ratio(theme.color.volt, EDGE)).toBe(12.59);
    expect(ratio(theme.color.volt, CENTRE)).toBeGreaterThanOrEqual(AAA);
  });

  it('carries white past AAA on both ends, which is what the initials over a poster fall back on', () => {
    expect(ratio(theme.color.surface, CENTRE)).toBe(11.66);
    expect(ratio(theme.color.surface, EDGE)).toBe(15.78);
  });

  it('carries the Later label in white over the on-dark fill past AA wherever the pill lands', () => {
    const onCentre = contrast(parse(theme.color.surface).rgb, over(theme.color.onDarkFill, CENTRE));
    const onEdge = contrast(parse(theme.color.surface).rgb, over(theme.color.onDarkFill, EDGE));
    expect(onCentre).toBe(6.94);
    expect(onEdge).toBe(9.18);
    expect(onCentre).toBeGreaterThanOrEqual(AA);
  });

  /**
   * Under AA, and recorded as such: the `vs` is decorative — hidden with the tiles inside the
   * header, whose sentence says *against* — so nothing a listener needs rides on it. The figure
   * is pinned so the day the grey is asked to carry a word, this is where it is found wanting.
   */
  it('carries the eyebrow grey under AA, which is why the vs is never spoken', () => {
    const vs = contrast(over(theme.color.onDarkEyebrow, CENTRE), parse(CENTRE).rgb);
    expect(vs).toBe(4.41);
    expect(vs).toBeLessThan(AA);
  });
});
