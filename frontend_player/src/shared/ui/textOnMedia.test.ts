/**
 * The one rule this system has for text over a **generated** fill, and the arithmetic that
 * makes it a rule rather than a hope.
 *
 * Every pair in `docs/design-system.md` 2.5 is a fixed pair — two hexes, one ratio. The
 * court is neither: its ground runs from the selected Sport's hue to a dark end, so the
 * ratio behind a white label depends on which Sport a player picked, and no fixed pair can
 * state it. #219 B6 closed that by **pinning the scrim**: at `color.courtScrim` the hue
 * is at most 7% of the ground, the dark end is a constant, and the light end is one of
 * **four** known composites — four ratios to compute rather than an unbounded set.
 *
 * This file is the computation, and the WCAG arithmetic under it is `contrast.testkit.ts`'s,
 * so the court's four rows and the poster's two are one formula. 2.5's four court rows are
 * **derived here and copied there**, exactly as the level bar's edges are derived in
 * `bandEdges.test.ts` rather than asserted, so unpinning the scrim or retuning a Sport hue
 * goes red instead of going unnoticed.
 *
 * A test and not a runtime check, for the reason `bandEdges.test.ts` gives: a `theme.ts`
 * that checked its own arithmetic would be the app refusing to launch over a drawing detail,
 * and a red build is where a human reconciles it.
 */

import { composite, contrast, parse, type Rgb } from '@/test-support/contrast';
import { theme, type SportKey } from './theme';

/** WCAG 2.1 requires 4.5:1 for text below the large-text threshold. Nothing here is above it. */
const AA = 4.5;

/**
 * The court's ground at its **light end** — the worst case for a label on it.
 *
 * The ground is a 150° gradient from the Sport hue to `night`, under one `courtScrim` pass.
 * At the dark end that composite is `night` whatever the Sport; at the light end it is the
 * hue showing through the pinned alpha, which is the four values this file computes.
 */
function courtGround(sport: SportKey): Rgb {
  const scrim = parse(theme.color.courtScrim);
  return composite(scrim.rgb, scrim.alpha, parse(theme.sport[sport]).rgb);
}

const WHITE = parse(theme.color.surface).rgb;

/** Low to high in ratio, so the first row is the one every other row clears. */
const SPORTS = ['tennis', 'badminton', 'padel', 'squash'] as const satisfies readonly SportKey[];

describe('the court scrim', () => {
  it('is pinned, which is the whole reason the four ratios below are computable', () => {
    expect(parse(theme.color.courtScrim).alpha).toBe(0.93);
  });

  it('is the night colour rather than a black, exactly as the sheet scrim is', () => {
    expect(parse(theme.color.courtScrim).rgb).toEqual(parse(theme.color.night).rgb);
  });
});

describe('white on the court ground (2.5)', () => {
  /** The four rows in 2.5. Copied from here, never the other way round. */
  const PUBLISHED: Readonly<Record<SportKey, number>> = {
    tennis: 12.29,
    badminton: 12.8,
    padel: 12.87,
    squash: 13.03,
  };

  it.each(SPORTS)('clears AA on %s, by a margin the pin guarantees', (sport) => {
    expect(contrast(WHITE, courtGround(sport))).toBeGreaterThanOrEqual(AA);
  });

  it.each(SPORTS)('is the ratio 2.5 publishes for %s', (sport) => {
    expect(contrast(WHITE, courtGround(sport))).toBe(PUBLISHED[sport]);
  });

  /**
   * B6 asked for the side labels to be raised off white `.6` *to whatever clears 4.5*. Under
   * the pinned scrim they already do, so nothing is raised and the finding is pinned instead
   * — a value left alone on evidence is one the next reader will otherwise change back.
   */
  it('still clears AA at the .6 white the side labels are drawn in', () => {
    const SIDE_LABEL_ALPHA = 0.6;
    const worst = Math.min(
      ...SPORTS.map((sport) => {
        const ground = courtGround(sport);
        return contrast(composite(WHITE, SIDE_LABEL_ALPHA, ground), ground);
      }),
    );

    expect(worst).toBeGreaterThanOrEqual(AA);
    // Pinned as well as bounded: 2.5 prints this figure as the reason the value is left
    // alone, and a published number nothing derives is one of the two documents drifting.
    expect(worst).toBe(5.46);
  });
});

describe('the textOnMedia shadow', () => {
  it('is drawn in a black that is dark enough to separate white from any ground', () => {
    expect(parse(theme.shadow.textOnMedia.textShadowColor).alpha).toBeGreaterThanOrEqual(0.6);
  });

  /**
   * A shadow WCAG cannot score. It is required on both label sets rather than one, because
   * the ratios above are the ground's *light end* and a label can sit anywhere on the ramp.
   */
  it('offsets and blurs, so it survives a label sitting on its own colour', () => {
    expect(theme.shadow.textOnMedia.textShadowRadius).toBeGreaterThan(0);
    expect(theme.shadow.textOnMedia.textShadowOffset.height).toBeGreaterThan(0);
  });
});
