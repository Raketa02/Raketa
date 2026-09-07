/**
 * The sixteen hues a generated poster can be, and the four bounds that make them a designed
 * set rather than a hash inventing a value (ADR-0134 §3 and §5, `docs/design-system.md` 6.9).
 *
 * Three of the four are the reason the poster is allowed to have a colour at all:
 *
 *   25°  from every named hue   so no poster can claim a Sport, by construction
 *   10°  from every other       so two players' posters are two colours and not one
 *   4.5  white on the light stop, 3:1 `ink` on the dark stop
 *
 * The fourth is the one nothing else in this system needs: **every light stop has the same
 * relative luminance, and so does every dark stop.** That is what "one fixed
 * saturation-and-lightness pair" has to mean once it is measured — sixteen hues at one
 * sRGB-HSL `S`/`L` vary in luminance by a factor of three between the greens and the blues,
 * and there is no such pair that clears 4.5 on the greens and 3:1 on the blues at once. The
 * set is therefore designed at one **CIE LCh(uv)** lightness and chroma per stop, which is
 * a space where equal lightness *is* equal luminance, and the two ratios below are two
 * numbers instead of thirty-two.
 *
 * These are derived here and copied into 2.5, exactly as the court's four rows are derived
 * in `textOnMedia.test.ts` — a published number nothing computes is one of the two documents
 * drifting.
 */

import {
  contrast,
  hueAngle,
  hueDistance,
  luminance,
  parse,
  type Rgb,
} from '@/test-support/contrast';
import { POSTER_HUES, theme, type PosterHue } from './theme';

/** WCAG 2.1: text below the large-text threshold. Every label drawn over a poster is. */
const AA = 4.5;
/** WCAG 2.1 1.4.11: a graphical object, which is what the figure is and the text is not. */
const NON_TEXT = 3;

const WHITE = parse(theme.color.surface).rgb;
const INK = parse(theme.color.ink).rgb;

/**
 * The hues a poster is kept away from: everything the palette has already given a meaning.
 *
 * `sport` aliases four of them, and it is listed anyway — 2.3's premise is that a Sport hue
 * never appears without the Sport's name in text, and a fifth Sport that stopped aliasing
 * would have to widen this list rather than remember to.
 */
const NAMED = [
  theme.color.red,
  theme.color.coral,
  theme.color.mint,
  theme.color.amber,
  theme.color.volt,
  ...Object.values(theme.sport),
].map((value) => hueAngle(parse(value).rgb));

/** Both ends of the ramp, because a bound that held at one end would be half a bound. */
const STOPS = ['light', 'dark'] as const;

const angleOf = (hue: PosterHue, stop: (typeof STOPS)[number]) => hueAngle(parse(hue[stop]).rgb);
const lumOf = (hue: PosterHue, stop: (typeof STOPS)[number]) => luminance(parse(hue[stop]).rgb);

describe('POSTER_HUES', () => {
  it('is sixteen, which is sixteen hues by three poses and the poster count', () => {
    expect(POSTER_HUES).toHaveLength(16);
  });

  it('is not reachable where a semantic colour is expected', () => {
    // 1.3 — colour is picked by MEANING. A poster hue is picked by a hash, so it is exported
    // beside the theme and never inside it; a `theme.color.poster…` would be the first hue in
    // the app that means nothing sitting where every other one means something.
    expect(Object.values(theme)).not.toContain(POSTER_HUES);
    expect(Object.keys(theme.color).filter((name) => /poster/i.test(name))).toEqual([]);
  });

  it.each(STOPS)('keeps every %s stop 25° from every hue the palette has named', (stop) => {
    for (const hue of POSTER_HUES) {
      const angle = angleOf(hue, stop);
      const nearest = Math.min(...NAMED.map((named) => hueDistance(angle, named)));

      expect(nearest).toBeGreaterThanOrEqual(25);
    }
  });

  it.each(STOPS)('keeps every %s stop 10° from every other poster hue', (stop) => {
    const angles = POSTER_HUES.map((hue) => angleOf(hue, stop));

    for (let a = 0; a < angles.length; a += 1) {
      for (let b = a + 1; b < angles.length; b += 1) {
        expect(hueDistance(angles[a] as number, angles[b] as number)).toBeGreaterThanOrEqual(10);
      }
    }
  });

  it('ramps saturation and lightness on ONE hue, and does not shift it', () => {
    // §4 refuses the prototype's 40°-warmer light stop: a poster that occupied a 40° arc
    // would have to clear the 25° bound at both ends, and the usable space collapses. The
    // stops are one LCh hue; the couple of degrees sRGB-HSL measures between them is the
    // difference between the two spaces, not a shift anybody drew.
    for (const hue of POSTER_HUES) {
      expect(hueDistance(angleOf(hue, 'light'), angleOf(hue, 'dark'))).toBeLessThan(4);
    }
  });

  it('has a light stop that is actually lighter, on every hue', () => {
    for (const hue of POSTER_HUES) {
      expect(lumOf(hue, 'light')).toBeGreaterThan(lumOf(hue, 'dark'));
    }
  });

  it('is one lightness pair — which is what makes the two ratios below two numbers', () => {
    const spread = (stop: (typeof STOPS)[number]) => {
      const values = POSTER_HUES.map((hue) => lumOf(hue, stop));
      return Math.max(...values) / Math.min(...values);
    };

    // Sixteen hues at one sRGB-HSL S/L would spread by a factor of three here. Under 2% is
    // the signature of a set designed at one perceptual lightness.
    expect(spread('light')).toBeLessThan(1.02);
    expect(spread('dark')).toBeLessThan(1.02);
  });
});

/**
 * Why the pair is fixed in LCh(uv) and not in sRGB HSL — **derived, not asserted**.
 *
 * `theme.ts`, 6.9 and Part 16 all claim that no fixed HSL saturation-and-lightness pair
 * clears both bounds on sixteen hues in the usable arcs. A claim in three documents and
 * nowhere in a test is the kind of number the next reader changes back, so this is the
 * argument itself.
 *
 * It rests on one observation: **every stop of every hue lies between the two bounds.** The
 * dark stop is at or above the floor by requirement; the light stop is at or below the
 * ceiling by requirement; and each is on the other side of the other because the light stop
 * is the lighter one. So a single HSL `S`/`L` used as a stop has to put every hue it is
 * applied to inside that band — and sixteen hues at 10° cannot all come from one arc, since
 * the wider arc holds thirteen. At least one green and at least one blue are in the set.
 */
describe('the pair sRGB HSL cannot supply', () => {
  /** The two arcs the 25° bound leaves, as whole degrees. */
  const ARCS = { green: [94, 138], blue: [220, 340] } as const;

  /** The floor the `ink` figure sets and the ceiling white sets, as relative luminance. */
  const FLOOR = NON_TEXT * (luminance(INK) + 0.05) - 0.05;
  const CEILING = 1.05 / AA - 0.05;

  /** sRGB from HSL, which is the space `theme.ts` states every other colour in. */
  const fromHsl = (hue: number, saturation: number, lightness: number): Rgb => {
    const [s, l] = [saturation / 100, lightness / 100];
    const chroma = (1 - Math.abs(2 * l - 1)) * s;
    const sextant = hue / 60;
    const middle = chroma * (1 - Math.abs((sextant % 2) - 1));
    const base = Math.floor(sextant);
    const rgb = (
      [
        [chroma, middle, 0],
        [middle, chroma, 0],
        [0, chroma, middle],
        [0, middle, chroma],
        [middle, 0, chroma],
        [chroma, 0, middle],
      ] as const
    )[base % 6] as readonly [number, number, number];
    const lift = l - chroma / 2;
    return [(rgb[0] + lift) * 255, (rgb[1] + lift) * 255, (rgb[2] + lift) * 255];
  };

  const holdsOne = (arc: readonly [number, number], saturation: number, lightness: number) => {
    for (let hue = arc[0]; hue <= arc[1]; hue += 1) {
      const y = luminance(fromHsl(hue, saturation, lightness));
      if (y >= FLOOR && y <= CEILING) return true;
    }
    return false;
  };

  it('runs out at 17% saturation, which is a grey and not a colour', () => {
    // Above this there is no lightness at all at which one hue from EACH arc sits inside the
    // band — so no stop can carry both a green and a blue, and sixteen hues need both.
    const highest = Math.max(
      ...Array.from({ length: 101 }, (_unused, saturation) => saturation).filter((saturation) =>
        Array.from({ length: 101 }, (_unused, lightness) => lightness).some(
          (lightness) =>
            holdsOne(ARCS.green, saturation, lightness) &&
            holdsOne(ARCS.blue, saturation, lightness),
        ),
      ),
    );

    expect(highest).toBe(17);
  });

  it('is why the shipped set is far more saturated than that ceiling would allow', () => {
    // Not a proof that LCh is the only answer — a demonstration that the set this file holds
    // is outside what the refused parameterisation could ever have reached.
    const saturation = ([r, g, b]: Rgb) => {
      const [max, min] = [Math.max(r, g, b) / 255, Math.min(r, g, b) / 255];
      const lightness = (max + min) / 2;
      return max === min ? 0 : ((max - min) / (1 - Math.abs(2 * lightness - 1))) * 100;
    };

    const weakest = Math.min(...POSTER_HUES.map((hue) => saturation(parse(hue.light).rgb)));

    expect(weakest).toBeGreaterThan(17);
  });
});

describe('text and the figure over a poster (2.5)', () => {
  /** The two rows in 2.5. Copied from here, never the other way round. */
  const PUBLISHED = {
    white: { low: 4.6, high: 4.65 },
    ink: { low: 3.09, high: 3.12 },
  } as const;

  it('clears AA for white on every light stop, which is the worst case for a label', () => {
    for (const hue of POSTER_HUES) {
      expect(contrast(WHITE, parse(hue.light).rgb)).toBeGreaterThanOrEqual(AA);
    }
  });

  it('clears 1.4.11 for the `ink` figure on every dark stop, which is its worst case', () => {
    // The figure is a graphical object and not text, so 4.5 does not apply to it — and the
    // two requirements bind the pair from opposite sides, which is the whole reason the
    // lightness is fixed rather than chosen.
    for (const hue of POSTER_HUES) {
      expect(contrast(INK, parse(hue.dark).rgb)).toBeGreaterThanOrEqual(NON_TEXT);
    }
  });

  it.each(['white', 'ink'] as const)('is the range 2.5 publishes for %s', (subject) => {
    const ratios = POSTER_HUES.map((hue) =>
      subject === 'white'
        ? contrast(WHITE, parse(hue.light).rgb)
        : contrast(INK, parse(hue.dark).rgb),
    );

    expect(Math.min(...ratios)).toBe(PUBLISHED[subject].low);
    expect(Math.max(...ratios)).toBe(PUBLISHED[subject].high);
  });

  it('leaves the ramp narrow, and says so rather than letting a reader widen it', () => {
    // The two bounds confine the whole ground to one band of luminance, so the gradient can
    // never be a strong one: 1,21–1,23 between the stops is the most the pair allows. A
    // reader who wants a deeper ramp is asking for one of the two ratios, and this is where
    // they find that out.
    const ramps = POSTER_HUES.map(
      (hue) => (lumOf(hue, 'light') + 0.05) / (lumOf(hue, 'dark') + 0.05),
    );
    const round = (value: number) => Math.round(value * 100) / 100;

    expect(round(Math.min(...ramps))).toBe(1.21);
    expect(round(Math.max(...ramps))).toBe(1.23);
  });
});
