/**
 * **The stage's ground, computed** — the hero's flat dark and the glow at its foot, which the
 * theme fences as sign-in's and sign-up's alone, and every ratio their comments state
 * ([#784](https://github.com/Raketa02/Raketa/issues/784), [Part 16](../../../docs/design-system.md#part-16--amendments-after-locking)
 * 2026-11-08).
 *
 * The app's fifth dark surface, and 2.5's table has no row for it, so this is the row: what sits
 * on it — white for the wordmark and the headline, `volt` for the wordmark's dot — on the ground
 * and on the glow the headline's last line sits above. `yesGround.test.ts`'s shape: the figures are
 * derived rather than typed, so a nudge to either colour goes red here rather than in somebody's
 * eyes.
 */

import { contrast, hueAngle, hueDistance, parse } from '@/test-support/contrast';

import { theme } from './theme';

const ratio = (a: string, b: string) => contrast(parse(a).rgb, parse(b).rgb);

/** WCAG 2.1: AAA for text at 7:1, and 3:1 for a mark that is not text (1.4.11). */
const AAA = 7;
const NON_TEXT = 3;

describe('the stage’s ground', () => {
  const GROUND = theme.color.stageGround;
  const GLOW = theme.color.stageGlow;

  it('is night’s family, as every dark ground before it is', () => {
    const ground = hueAngle(parse(GROUND).rgb);
    expect(Math.round(ground)).toBe(198);
    expect(hueDistance(ground, hueAngle(parse(theme.color.night).rgb))).toBeLessThan(5);
  });

  /**
   * Its own token, though the yes screen's edge is one step from it: the yes ground is that
   * screen's alone, and a value is written for what was drawn. Pinned, so the two are never
   * merged by somebody tidying up.
   */
  it('is not the yes screen’s edge, though it is a step from it', () => {
    expect(GROUND).not.toBe(theme.color.yesGroundEdge);
    expect(ratio(GROUND, theme.color.yesGroundEdge)).toBe(1);
  });

  it('carries the wordmark and the headline in white past AAA, on the ground and on the glow', () => {
    expect(ratio(theme.color.surface, GROUND)).toBe(15.76);
    expect(ratio(theme.color.surface, GLOW)).toBe(12.95);
    expect(ratio(theme.color.surface, GLOW)).toBeGreaterThanOrEqual(AAA);
  });

  it('carries the wordmark’s volt dot far past what a mark needs', () => {
    expect(ratio(theme.color.volt, GROUND)).toBe(12.57);
    expect(ratio(theme.color.volt, GROUND)).toBeGreaterThanOrEqual(NON_TEXT);
  });

  /** A glow and not a shape: a light the ground falls into, never an edge anybody reads. */
  it('glows by a step and not by an edge', () => {
    expect(ratio(GLOW, GROUND)).toBe(1.22);
    expect(Math.round(hueAngle(parse(GLOW).rgb))).toBe(160);
  });
});
