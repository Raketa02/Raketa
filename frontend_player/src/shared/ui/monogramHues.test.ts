/**
 * The eight fills a group's monogram can be (`MONOGRAM_HUES`, docs/design-system.md 7.20), and
 * the two bounds that make them a set rather than eight colours somebody liked.
 *
 *   one per colour key     the backend serves a key from 0 to 7 and never a colour (ADR-0183 §5)
 *   4.5  white on each     the tile's two letters are text, and white is what they are drawn in
 *
 * Computed rather than asserted, as `posterHues.test.ts` computes the poster's.
 */

import { contrast, parse } from '@/test-support/contrast';

import { MONOGRAM_HUES, theme } from './theme';

/** WCAG 2.1, text below the large-text threshold — the letters on a 28pt tile are 10pt. */
const AA = 4.5;

const WHITE = parse(theme.color.surface).rgb;

describe('the monogram hues', () => {
  it('has one fill for every colour key the backend serves', () => {
    expect(MONOGRAM_HUES).toHaveLength(8);
    expect(new Set(MONOGRAM_HUES).size).toBe(8);
  });

  it.each(MONOGRAM_HUES.map((hue, key) => [key, hue] as const))(
    'carries white letters at AA on key %i (%s)',
    (_key, hue) => {
      expect(contrast(WHITE, parse(hue).rgb)).toBeGreaterThanOrEqual(AA);
    },
  );
});
