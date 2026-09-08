/**
 * The meter's three fills, and the arithmetic that makes drawing a figure in one of them legal
 * ([#385](https://github.com/Raketa02/Raketa/issues/385)).
 *
 * A meter is a **graphical object** conveying information, so
 * [1.4.11](../../../docs/design-system.md#25-contrast--computed) asks 3:1 of each fill against
 * the track it sits in. That is one of the two bounds. The other is the one the record card
 * actually leans on: three fills stacked in a column have to be told apart from **each other**,
 * and colour is never the only cue this system allows for that
 * ([Part 13](../../../docs/design-system.md#part-13--accessibility)).
 *
 * ## Two measures, because one of them is the wrong instrument here
 *
 * `recordSquares.test.ts` holds its two fills 3:1 apart from each other and calls that the
 * lightness step. **Three fills cannot be held to that**, and the reason is arithmetic rather
 * than a shortage of colours: each has to clear 3:1 against a near-white track, which caps how
 * light it may be, and 3:1 from each of the other two, which caps how light the second and
 * third may be *again*. Run the two constraints together and the third fill needs a negative
 * luminance. The test below computes exactly that, so the bound this file states instead is
 * not a bound somebody softened when the first one failed.
 *
 * What is stated instead is a **lightness step in `L*`**, which is the measure the ratio was
 * standing in for. WCAG's ratio adds 0,05 of flare to both sides, so at the dark end it reads
 * two obviously different colours as barely apart; `L*` is what a reader with no hue perception
 * actually separates them by.
 *
 * ## The pair at the floor is at the palette's own ceiling
 *
 * `mint` against `red` is 10,2 `L*`, and neither half can be pulled further: a lighter green
 * fails the track bound above, and there is no darker red in the palette
 * ([15.2](../../../docs/design-system.md#152-adding-a-colour) forbids inventing one). So the
 * floor is the honest statement of what this palette can do, and the tone is the **third** cue
 * on every row that draws it — behind the bar's own length and the raw fraction printed two
 * words earlier, both of which carry the value on their own.
 *
 * Derived here and copied into [2.5](../../../docs/design-system.md#25-contrast--computed),
 * beside `recordSquares.test.ts` and `textOnMedia.test.ts` and for their reason: a test rather
 * than a runtime check, because a `theme.ts` that scored its own arithmetic would be the app
 * refusing to launch over a drawing detail.
 */

import {
  contrast,
  hueAngle,
  hueDistance,
  lightness,
  luminance,
  parse,
  type Rgb,
} from '@/test-support/contrast';

import { METER_TONE_FILL, type MeterTone } from './Meter';
import { theme } from './theme';

/** WCAG 2.1's floor for a graphical object — a bar is not text and is not held to 4.5. */
const GRAPHICAL = 3;

/** Degrees. The poster's own bound for two fills that must not read as one colour. */
const DISTINCT_HUE = 25;

/** `L*` points. A tenth of the lightness scale — the smallest step this system calls a step. */
const DISTINCT_LIGHTNESS = 10;

/** The track every meter is drawn in (7.3), which belongs to the component and not to the tone. */
const TRACK = parse(theme.color.line2).rgb;

const FILL: Readonly<Record<MeterTone, Rgb>> = {
  good: parse(METER_TONE_FILL.good).rgb,
  neutral: parse(METER_TONE_FILL.neutral).rgb,
  poor: parse(METER_TONE_FILL.poor).rgb,
};

const PAIRS = [
  ['good', 'neutral'],
  ['neutral', 'poor'],
  ['good', 'poor'],
] as const;

describe('the meter’s three tones (7.3)', () => {
  /** The three rows 2.5 publishes. Copied from here, never the other way round. */
  const PUBLISHED = { good: 3.48, neutral: 11.36, poor: 5.04 };

  it.each(PAIRS.flat().filter((tone, at, all) => all.indexOf(tone) === at))(
    'draws a %s fill that reads against the track it fills',
    (tone) => {
      expect(contrast(FILL[tone], TRACK)).toBeGreaterThanOrEqual(GRAPHICAL);
      expect(contrast(FILL[tone], TRACK)).toBe(PUBLISHED[tone]);
    },
  );

  it.each(PAIRS)('tells %s and %s apart by hue', (one, other) => {
    expect(hueDistance(hueAngle(FILL[one]), hueAngle(FILL[other]))).toBeGreaterThanOrEqual(
      DISTINCT_HUE,
    );
  });

  /**
   * The half that matters: a reader who cannot separate two hues still separates the marks.
   * `good` against `poor` is a green and a red, which is the pair colour vision most often
   * collapses — so it is the pair the lightness step exists for, and it is the one at the floor.
   *
   * **Separable, and deliberately not a ramp.** In lightness the three read good › poor ›
   * neutral, which is not the ladder's order — and it is not meant to be one. A tone is a
   * **categorical** cue naming which step the caller's rule reached, where the *value* is
   * carried by the bar's own length, which is monotone by construction, and by the fraction
   * printed beside it. Ordering the three by lightness as well would need a colour the palette
   * does not have, since the darkest fill available for `poor` is the one already used for
   * `neutral`.
   */
  it.each(PAIRS)('tells %s and %s apart by lightness as well', (one, other) => {
    const apart = Math.abs(lightness(FILL[one]) - lightness(FILL[other]));
    expect(apart).toBeGreaterThanOrEqual(DISTINCT_LIGHTNESS);
  });

  /**
   * **Why the bound above is stated in `L*` and not as a contrast ratio.**
   *
   * Not a preference: with the track bound in force, no three colours exist that are also 3:1
   * from one another. The third would have to be darker than black. Recomputed here rather
   * than asserted in prose, so that the day the track lightens the claim is re-derived instead
   * of inherited.
   */
  it('cannot hold three fills 3:1 apart from each other, and that is arithmetic', () => {
    // The darkest thing 3:1 below a given luminance — the step every one of the bounds is.
    const below = (lighter: number) => (lighter + 0.05) / GRAPHICAL - 0.05;
    // The lightest a fill may be and still clear the track, then two 3:1 steps down from it.
    const third = below(below(below(luminance(TRACK))));

    expect(third).toBeLessThan(0);
  });
});
