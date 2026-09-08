/**
 * *Last 5* is five squares distinguished by **fill**, and this is the arithmetic that makes
 * that legal ([#312](https://github.com/Raketa02/Raketa/issues/312)).
 *
 * A square carries no word. It is a **graphical object** conveying information, so
 * [1.4.11](../../../docs/design-system.md#25-contrast--computed) asks 3:1 of it — against
 * the ground it is drawn on, and against the other state it has to be told apart from. Three
 * ratios, and none of them is a pair anybody eyeballed:
 *
 * - a **won** square against the block's `paper2` ground,
 * - a **lost** square against the same ground,
 * - and the two against **each other**, which is the one the whole row depends on.
 *
 * The pair is `ink` and `muted`, which is a **lightness** step and not a hue one — so the run
 * survives being read by somebody who cannot tell two hues apart, and
 * [Part 13](../../../docs/design-system.md#part-13--accessibility)'s *never colour alone*
 * is satisfied for the sighted half before the spoken clause is reached at all. The listener's
 * half is `lastFiveReading`'s and is asserted with the card.
 *
 * Derived here and copied into 2.5, beside `bandEdges.test.ts` and `textOnMedia.test.ts` and
 * exactly as they derive theirs — so repainting either fill goes red instead of going
 * unnoticed. A test rather than a runtime check, for those files' reason: a `theme.ts` that
 * checked its own arithmetic would be the app refusing to launch over a drawing detail.
 *
 * **The two fills are read off `RunOfForm` and not off the theme**, which is what makes that
 * sentence true. A test that parsed `theme.color.ink` would go on passing the day the
 * component was repainted to some other token, and the run is a **drawn object** rather than
 * a pair of tokens — it is the square on screen that has to clear 3:1, so it is the square
 * on screen the arithmetic is done against. The ground is still the theme's, because it
 * belongs to the box the run is drawn in ([7.13](../../../docs/design-system.md#713-the-record-block))
 * rather than to the run.
 */

import { contrast, hueAngle, hueDistance, parse } from '@/test-support/contrast';

import { RUN_OF_FORM_FILL } from './RunOfForm';
import { theme } from './theme';

/** WCAG 2.1's floor for a graphical object — a square is not text and is not held to 4.5. */
const GRAPHICAL = 3;

/** Degrees. Two fills this close read as one colour at two lightnesses. */
const SAME_FAMILY = 7;

const GROUND = parse(theme.color.paper2).rgb;
const WON = parse(RUN_OF_FORM_FILL.WIN).rgb;
const LOST = parse(RUN_OF_FORM_FILL.LOSS).rgb;

describe('the run of form (2.5, 7.13)', () => {
  /** The three rows 2.5 publishes. Copied from here, never the other way round. */
  const PUBLISHED = { won: 14.57, lost: 4.49, apart: 3.24 };

  it('draws a won square that reads against the block’s recessed ground', () => {
    expect(contrast(WON, GROUND)).toBeGreaterThanOrEqual(GRAPHICAL);
    expect(contrast(WON, GROUND)).toBe(PUBLISHED.won);
  });

  it('draws a lost square that reads against it too, so a gap is not mistaken for a loss', () => {
    // The difference between *three results* and *five* is squares against no squares, and a
    // pale square that vanished into its ground would make the run's length unreadable.
    expect(contrast(LOST, GROUND)).toBeGreaterThanOrEqual(GRAPHICAL);
    expect(contrast(LOST, GROUND)).toBe(PUBLISHED.lost);
  });

  it('keeps the two states apart by lightness, which is the row’s whole claim', () => {
    expect(contrast(WON, LOST)).toBeGreaterThanOrEqual(GRAPHICAL);
    expect(contrast(WON, LOST)).toBe(PUBLISHED.apart);
  });

  it('is a lightness step and never a hue one, so one colour is enough to read it', () => {
    // The two fills are the same blue-grey at two lightnesses. That matters because WCAG
    // contrast is a **luminance** ratio and says nothing about hue on its own: a pair that
    // cleared 3:1 across two hues would still be a hue cue for anybody who cannot separate
    // them. Held to the same 7 degrees `voltStroke` is held to against volt in `Tag.test.tsx`.
    expect(hueDistance(hueAngle(WON), hueAngle(LOST))).toBeLessThanOrEqual(SAME_FAMILY);
  });
});
