/**
 * *Last 5* is five squares distinguished by **fill**, and this is the arithmetic that makes
 * that legal ([#312](https://github.com/Rakieta02/Rakieta/issues/312)).
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
 * The pair is `mint` and `muted`, which is a **hue** step, and that is a deliberate change
 * from the lightness step it was. `ink` against `muted` cleared 3:1 by luminance alone, so the
 * run survived being read in one colour. Green against grey is **1,33:1**, and this palette
 * has no green that does better: a fill 3:1 from a light ground and 3:1 from a partner that is
 * *also* 3:1 from that ground has to be near-black, and a near-black green is not green.
 *
 * **So the third ratio is gone and this file says so rather than quietly dropping it.** What
 * survives is the pair against the ground — the ratio that keeps a loss from reading as the
 * **gap** at the end of a short run, which is what makes the run's length legible — plus the
 * spoken clause, `lastFiveReading`'s, asserted with the card. A reader who cannot separate the
 * two hues gets the count and not the row. The cheap way back is a **hollow** loss square: a
 * shape cue, no geometry change, and the green kept.
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

/**
 * Degrees. Two fills this far apart are two colours rather than one at two lightnesses —
 * the inverse of what this file used to assert, and the whole of what tells the row apart now.
 */
const TWO_HUES = 30;

const GROUND = parse(theme.color.paper2).rgb;
const WON = parse(RUN_OF_FORM_FILL.WIN).rgb;
const LOST = parse(RUN_OF_FORM_FILL.LOSS).rgb;

describe('the run of form (2.5, 7.13)', () => {
  /** The rows 2.5 publishes. Copied from here, never the other way round. */
  const PUBLISHED = { won: 3.39, lost: 4.49, apart: 1.33 };

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

  it('tells the two states apart by hue, and the luminance step is recorded as spent', () => {
    // **This is the cost, pinned so it cannot drift further without going red.** The pair used
    // to clear 3:1 by luminance and now does not, so the row is a hue cue for a sighted
    // reader. Asserted as an exact number rather than a floor: a repaint that made it *worse*
    // should fail here, and one that made it better should be noticed and published in 2.5.
    expect(contrast(WON, LOST)).toBe(PUBLISHED.apart);
    expect(hueDistance(hueAngle(WON), hueAngle(LOST))).toBeGreaterThanOrEqual(TWO_HUES);
  });
});
