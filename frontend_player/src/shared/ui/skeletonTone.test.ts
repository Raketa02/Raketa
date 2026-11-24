/**
 * **The skeleton's two tones, computed** (PRD #867, #868, #870; 2.1, 15.2, Part 16 2026-11-24) — the
 * ratios `color.skeleton` and `color.skeletonSheen`'s comments state, derived from the hex values
 * rather than typed, so a nudge to either goes red here rather than on a phone. `levelCardGround`'s
 * shape.
 *
 * Neither is asked for 1.4.11's 3:1: a skeleton is hidden from a listener and carries nothing a
 * player needs to read. What is held is that a shape reads as a shape on both grounds it is drawn
 * on, and that the band's peak never makes a shape on a white card vanish into it.
 */

import { contrast, parse } from '@/test-support/contrast';

import { theme } from './theme';

const ratio = (a: string, b: string) => contrast(parse(a).rgb, parse(b).rgb);

describe('the skeleton’s tones', () => {
  it('are paper3’s and paper’s values — a new meaning, no new colour (15.2)', () => {
    expect(theme.color.skeleton).toBe(theme.color.paper3);
    expect(theme.color.skeletonSheen).toBe(theme.color.paper);
  });

  it('stand a shape off both grounds it is drawn on: 1,20 on paper, 1,34 on a white card', () => {
    expect(ratio(theme.color.skeleton, theme.color.paper)).toBeCloseTo(1.2, 2);
    expect(ratio(theme.color.skeleton, theme.color.surface)).toBeCloseTo(1.34, 2);
  });

  it('lift a shape to its ground at the band’s peak, and still 1,12 off a white card', () => {
    expect(ratio(theme.color.skeletonSheen, theme.color.paper)).toBe(1);
    expect(ratio(theme.color.skeletonSheen, theme.color.surface)).toBeCloseTo(1.12, 2);
  });

  it('stand further off paper than the two tones refused as too faint (Q23): paper2 and line2', () => {
    expect(ratio(theme.color.paper2, theme.color.paper)).toBeLessThan(
      ratio(theme.color.skeleton, theme.color.paper),
    );
    expect(ratio(theme.color.line2, theme.color.paper)).toBeLessThan(
      ratio(theme.color.skeleton, theme.color.paper),
    );
  });
});
