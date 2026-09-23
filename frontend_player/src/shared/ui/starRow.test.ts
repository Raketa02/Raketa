/**
 * A star row is five marks distinguished by **fill**, and this is the arithmetic that makes
 * that legal ([#386](https://github.com/Raketa02/Raketa/issues/386)).
 *
 * `recordSquares.test.ts`'s three rows, asked of the same pair on a different bed. A star
 * carries no word, so it is a **graphical object** conveying information and
 * [1.4.11](../../../docs/design-system.md#25-contrast--computed) asks 3:1 of it — against the
 * ground it is drawn on, and against the other state it has to be told apart from:
 *
 * - a **given** star against the card's `surface`,
 * - a **blank** one against the same ground, because a star that vanished would make *five
 *   stars* unreadable as a scale and the row would be three marks floating in a card,
 * - and the two against **each other**, which is the whole of what the control says.
 *
 * The pair is `ink` and `muted` — the run of form's, deliberately, since both are answers to
 * *tell two states of one mark apart* and a second pair would be a second thing to keep in
 * step. It is a **lightness** step and not a hue one, so the row survives being read by
 * somebody who cannot separate two hues, and
 * [Part 13](../../../docs/design-system.md#part-13--accessibility)'s *never colour alone* is
 * satisfied for the sighted half before the spoken clause is reached at all. **This row has a
 * second cue the squares could not have**: solid against outline, which is a shape difference
 * on the same mark.
 *
 * Derived here and copied into 2.5, exactly as `recordSquares.test.ts` and `bandEdges.test.ts`
 * derive theirs — so repainting either state goes red instead of going unnoticed. The two
 * values are read off `STAR_FILL` and not off the theme, because it is the star **on screen**
 * that has to clear 3:1; the ground is the theme's, because it belongs to the card the row is
 * drawn in rather than to the row.
 */

import { contrast, hueAngle, hueDistance, parse } from '@/test-support/contrast';

import { STAR_FILL } from './Star';
import { theme } from './theme';

/** WCAG 2.1's floor for a graphical object — a star is not text and is not held to 4.5. */
const GRAPHICAL = 3;

/** Degrees. Two values this close read as one colour at two lightnesses. */
const SAME_FAMILY = 7;

const GROUND = parse(theme.color.surface).rgb;
const GIVEN = parse(STAR_FILL.given).rgb;
const BLANK = parse(STAR_FILL.blank).rgb;

describe('the star row (2.5, 6.13)', () => {
  /** The three rows 2.5 publishes. Copied from here, never the other way round. */
  const PUBLISHED = { given: 17.5, blank: 5.4, apart: 3.24 };

  it('draws a given star that reads against the card it sits on', () => {
    expect(contrast(GIVEN, GROUND)).toBeGreaterThanOrEqual(GRAPHICAL);
    expect(contrast(GIVEN, GROUND)).toBe(PUBLISHED.given);
  });

  it('draws a blank star that reads too, so the scale is five marks and not three', () => {
    expect(contrast(BLANK, GROUND)).toBeGreaterThanOrEqual(GRAPHICAL);
    expect(contrast(BLANK, GROUND)).toBe(PUBLISHED.blank);
  });

  it('keeps the two states apart by lightness, which is what the control says', () => {
    expect(contrast(GIVEN, BLANK)).toBeGreaterThanOrEqual(GRAPHICAL);
    expect(contrast(GIVEN, BLANK)).toBe(PUBLISHED.apart);
  });

  it('is a lightness step and never a hue one, so one colour is enough to read it', () => {
    // WCAG contrast is a **luminance** ratio and says nothing about hue on its own: a pair
    // that cleared 3:1 across two hues would still be a hue cue for anybody who cannot
    // separate them. Held to the same 7 degrees the run of form's pair is held to.
    expect(hueDistance(hueAngle(GIVEN), hueAngle(BLANK))).toBeLessThanOrEqual(SAME_FAMILY);
  });
});
