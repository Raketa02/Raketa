/**
 * **The posting grid's greens, computed** — the two colours the theme adds for *Post a game*'s
 * cells, their inks, and every ratio their comments state
 * ([#558](https://github.com/Rakieta02/Rakieta/issues/558), the Games & Fill in screens A5.2, A10,
 * [Part 16](../../../docs/design-system.md#part-16--amendments-after-locking) 2026-10-02).
 *
 * `gameGround.test.ts`'s shape: 2.5's table has no row for these fills, so this is the row, and the
 * figures are derived rather than typed, so a nudge to any colour goes red here rather than in
 * somebody's eyes.
 */

import { contrast, hueAngle, hueDistance, lightness, parse } from '@/test-support/contrast';

import { theme } from './theme';

const ratio = (a: string, b: string) => contrast(parse(a).rgb, parse(b).rgb);
const hue = (value: string) => hueAngle(parse(value).rgb);

/** WCAG 2.1: 4.5:1 for text. */
const AA = 4.5;

const { color } = theme;

describe('the posting grid’s greens', () => {
  it('would not carry the mocks’ white figure — which is why each has an ink', () => {
    expect(ratio(color.surface, color.gridLight)).toBe(1.51);
    expect(ratio(color.surface, color.gridMid)).toBe(2.15);
  });

  it('carry their figure and glyph in their own ink, past AA', () => {
    expect(ratio(color.gridLightInk, color.gridLight)).toBe(4.65);
    expect(ratio(color.gridMidInk, color.gridMid)).toBe(4.68);
    expect(ratio(color.gridLightInk, color.gridLight)).toBeGreaterThanOrEqual(AA);
    expect(ratio(color.gridMidInk, color.gridMid)).toBeGreaterThanOrEqual(AA);
  });

  it('keep each ink in its green’s own hue', () => {
    expect(hueDistance(hue(color.gridLightInk), hue(color.gridLight))).toBeLessThan(3);
    expect(hueDistance(hue(color.gridMidInk), hue(color.gridMid))).toBeLessThan(3);
  });

  it('carry the rest of the ramp’s figures: mintInk on mintSoft, white on mintInk', () => {
    expect(ratio(color.mintInk, color.mintSoft)).toBe(5.08);
    expect(ratio(color.surface, color.mintInk)).toBe(5.84);
  });

  it('climb in brightness from the few to the hot — brighter is more worth picking, read darker', () => {
    const ramp = [color.mintSoft, color.gridLight, color.gridMid, color.mintInk].map((value) =>
      lightness(parse(value).rgb),
    );
    for (let at = 1; at < ramp.length; at += 1) {
      expect(ramp[at]).toBeLessThan(ramp[at - 1] ?? Infinity);
    }
  });

  it('are a shade on paper, never the only signal — the figure and the glyph carry it', () => {
    expect(ratio(color.gridLight, color.paper)).toBe(1.35);
    expect(ratio(color.gridMid, color.paper)).toBe(1.92);
  });

  it('ring the hot cell in volt that reads against its fill, edged so it reads on paper', () => {
    expect(ratio(color.volt, color.mintInk)).toBe(4.66);
    expect(ratio(color.volt, color.paper)).toBeLessThan(1.2);
    expect(ratio(color.mintInk, color.paper)).toBeGreaterThanOrEqual(3);
  });

  it('dot a game happening in coralInk on a surface ring — the dot alone vanishes on the hot fill', () => {
    expect(ratio(color.coralInk, color.mintInk)).toBeLessThan(1.1);
    expect(ratio(color.coralInk, color.surface)).toBe(5.89);
  });
});
