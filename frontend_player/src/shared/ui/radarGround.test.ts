/**
 * **The radar's ground, computed** — the two colours the theme fences as the Radar pane's
 * alone, the zoom cluster's bed beside them, and every ratio their comments state
 * ([ADR-0174](../../../../docs/adr/0174-the-radar-plots-the-reach-and-a-look-is-not-a-deal.md)
 * §7, [Part 16](../../../docs/design-system.md#part-16--amendments-after-locking) 2026-09-16).
 *
 * The ground is the app's third dark surface and 2.5's table has no row for it, so this is the
 * row, in `yesGround.test.ts`'s shape: what sits on it — `volt` for the viewer's ring and the
 * chip, white for the footer's headline and the cluster's marks, the on-dark greys for the
 * counter, the hint, a ring's label and a level under a face — and what each measures on both
 * ends of the glow. The figures are derived rather than typed, so a nudge to either colour goes
 * red here rather than in somebody's eyes.
 */

import { composite, contrast, hueAngle, hueDistance, parse } from '@/test-support/contrast';

import { theme } from './theme';

const ratio = (a: string, b: string) => contrast(parse(a).rgb, parse(b).rgb);

/** WCAG 2.1: 4.5:1 for text below the large-text threshold, and AAA at 7:1. */
const AA = 4.5;
const AAA = 7;

/** A translucent colour as it lands on the glow's centre or edge. */
const over = (translucent: string, ground: string) => {
  const { rgb, alpha } = parse(translucent);
  return composite(rgb, alpha, parse(ground).rgb);
};

describe('the radar’s ground', () => {
  const CENTRE = theme.color.radarGroundCentre;
  const EDGE = theme.color.radarGroundEdge;

  it('is night’s family beside the yes ground, and the edge is the centre gone darker', () => {
    const centre = hueAngle(parse(CENTRE).rgb);
    const edge = hueAngle(parse(EDGE).rgb);
    expect(Math.round(centre)).toBe(199);
    expect(hueDistance(centre, edge)).toBeLessThan(3);
    expect(hueDistance(centre, hueAngle(parse(theme.color.night).rgb))).toBeLessThan(6);
    expect(hueDistance(centre, hueAngle(parse(theme.color.yesGroundCentre).rgb))).toBeLessThan(3);
  });

  it('is not the yes ground under a second name', () => {
    expect(CENTRE).not.toBe(theme.color.yesGroundCentre);
    expect(EDGE).not.toBe(theme.color.yesGroundEdge);
  });

  it('carries the viewer’s ring and the chip in volt past AAA on both ends', () => {
    expect(ratio(theme.color.volt, CENTRE)).toBe(10.67);
    expect(ratio(theme.color.volt, EDGE)).toBe(13.81);
    expect(ratio(theme.color.volt, CENTRE)).toBeGreaterThanOrEqual(AAA);
  });

  it('carries white past AAA on both ends — the footer’s headline and the cluster’s marks', () => {
    expect(ratio(theme.color.surface, CENTRE)).toBe(13.37);
    expect(ratio(theme.color.surface, EDGE)).toBe(17.31);
  });

  it('carries the counter, the hint and a level under a face in the on-dark tiny grey past AAA', () => {
    const onCentre = contrast(over(theme.color.onDarkTiny, CENTRE), parse(CENTRE).rgb);
    expect(onCentre).toBe(7.05);
    expect(onCentre).toBeGreaterThanOrEqual(AAA);
  });

  it('carries a ring’s label in the on-dark eyebrow grey past AA', () => {
    const onCentre = contrast(over(theme.color.onDarkEyebrow, CENTRE), parse(CENTRE).rgb);
    const onEdge = contrast(over(theme.color.onDarkEyebrow, EDGE), parse(EDGE).rgb);
    expect(onCentre).toBe(4.8);
    expect(onEdge).toBe(5.5);
    expect(onCentre).toBeGreaterThanOrEqual(AA);
  });

  /**
   * Under AA, and recorded as such: `coral` and `mint` are the card's colours — the sport dot
   * and the tags line — and the card is paper. The figures are pinned so the day either is asked
   * to carry a word on the ground itself, this is where it is found wanting.
   */
  it('carries neither coral nor mint as text, which is why the card is paper', () => {
    expect(ratio(theme.color.coral, CENTRE)).toBeLessThan(AA);
    expect(ratio(theme.color.mint, CENTRE)).toBeLessThan(AA);
  });
});

describe('the zoom cluster’s bed', () => {
  const CENTRE = theme.color.radarGroundCentre;

  it('is ink at half strength — darker than the ground, where every other on-dark tile is lighter', () => {
    const bed = over(theme.color.radarControl, CENTRE);
    const lighter = over(theme.color.onDarkTag, CENTRE);
    expect(bed[0] + bed[1] + bed[2]).toBeLessThan(parse(CENTRE).rgb.reduce((a, b) => a + b, 0));
    expect(lighter[0] + lighter[1] + lighter[2]).toBeGreaterThan(
      parse(CENTRE).rgb.reduce((a, b) => a + b, 0),
    );
  });

  it('carries its white marks past AAA', () => {
    const bed = over(theme.color.radarControl, CENTRE);
    expect(contrast(parse(theme.color.surface).rgb, bed)).toBe(15.48);
  });
});
