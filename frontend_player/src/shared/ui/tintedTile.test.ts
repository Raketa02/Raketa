/**
 * **The tinted tile's wash, against the words on it** (#803; 7.35) — derived for all sixteen poster
 * hues at the wash's strongest point, the top-left corner, rather than asserted: a published ratio
 * nothing computes is one of two documents drifting (`posterHues.test.ts`' rule).
 */

import { composite, contrast, parse } from '@/test-support/contrast';

import { TINTED_TILE } from './TintedTile';
import { POSTER_HUES, theme } from './theme';

/** WCAG 2.1: text below the large-text threshold — the tile's second line and *+N more* are. */
const AA = 4.5;

const SURFACE = parse(theme.color.surface).rgb;
const corner = (hue: string) => composite(parse(hue).rgb, TINTED_TILE.tint, SURFACE);

describe('the tinted tile', () => {
  it('keeps muted text at 4.5 on the strongest corner of every poster hue', () => {
    for (const hue of POSTER_HUES) {
      expect(contrast(parse(theme.color.muted).rgb, corner(hue.light))).toBeGreaterThanOrEqual(AA);
    }
  });

  it('keeps ink at 7 there, the nickname’s', () => {
    for (const hue of POSTER_HUES) {
      expect(contrast(parse(theme.color.ink).rgb, corner(hue.light))).toBeGreaterThanOrEqual(7);
    }
  });

  it('stays a pale card: the strongest corner is still nearer surface than any hue', () => {
    expect(TINTED_TILE.tint).toBeLessThanOrEqual(1 / 8);
    expect(TINTED_TILE.until).toBeLessThan(1);
  });
});
