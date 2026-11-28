/**
 * **The Social vibe card's paper paint, computed** — every ratio `theme.ts` states for `voltPale`,
 * `oliveInk`, `oliveInkDim` and `vibeGrey` ([#840](https://github.com/Rakieta02/Rakieta/issues/840);
 * ADR-0207 §8–§9, 7.39, Part 16 2026-11-23).
 *
 * `gameGround.test.ts`'s shape: the figures are derived rather than typed, so a nudge to any of the
 * four goes red here rather than in somebody's eyes. The card is `surface`, bounded by `line`.
 */

import {
  contrast,
  hueAngle,
  hueDistance,
  luminance,
  parse,
  type Rgb,
} from '@/test-support/contrast';

import { SOCIAL_VIBE_CARD_FILL } from './SocialVibeCard';
import { SOCIAL_VIBE_ON_DARK } from './SocialVibeRow';
import { theme } from './theme';

const ratio = (a: string, b: string) => contrast(parse(a).rgb, parse(b).rgb);
const lum = (a: string) => luminance(parse(a).rgb);
const hue = (a: string) => hueAngle(parse(a).rgb);

/** WCAG 2.1: 4.5:1 for text, 3:1 for a mark. */
const AA = 4.5;
const MARK = 3;

/**
 * Mock 7's measured inks, as the pixels read: the olive of its dots and %, the grey of a row only you
 * have, and its grey dot.
 */
const MOCK_OLIVE: Rgb = [94, 112, 16];
const MOCK_ROW_GREY: Rgb = [124, 139, 141];
const MOCK_GREY_DOT: Rgb = [230, 226, 216];

/** A theme colour against a measured one. */
const against = (a: string, measured: Rgb) => contrast(parse(a).rgb, measured);

const { surface, ink, line, line2, volt, gameVoltDim, gameGrey } = theme.color;
const { voltPale, oliveInk, oliveInkDim, vibeGrey } = theme.color;

describe('a shared row — the pale volt band', () => {
  it('carries its words in ink and its dots in olive', () => {
    expect(ratio(ink, voltPale)).toBe(16.82);
    expect(ratio(oliveInk, voltPale)).toBe(5.78);
    expect(ratio(oliveInk, voltPale)).toBeGreaterThanOrEqual(MARK);
  });

  it('is a bed, never a word or a mark: on the card it is barely a shade', () => {
    expect(ratio(voltPale, surface)).toBeLessThan(1.1);
  });
});

describe('the olive', () => {
  /** ADR-0207 §9.2: olive ink is today's `gameCellDim`, not a second olive beside it. */
  it('is the overlap grid’s olive, and the mock’s olive is only a shade off it', () => {
    expect(oliveInk).toBe(theme.color.gameCellDim);
    expect(against(oliveInk, MOCK_OLIVE)).toBeLessThan(1.1);
  });

  it('carries the % past AA on the card, and the dimmed step still does', () => {
    expect(ratio(oliveInk, surface)).toBe(6.01);
    expect(ratio(oliveInkDim, surface)).toBe(4.91);
    expect(ratio(oliveInkDim, surface)).toBeGreaterThanOrEqual(AA);
  });

  it('dims at its own hue, lighter than the olive', () => {
    expect(hueDistance(hue(oliveInkDim), hue(oliveInk))).toBeLessThan(1);
    expect(lum(oliveInkDim)).toBeGreaterThan(lum(oliveInk));
  });
});

describe('a row only you have, and Fresh mix — the grey', () => {
  it('is the mock’s grey at its own hue, darkened past AA, which the mock’s is not', () => {
    expect(against(surface, MOCK_ROW_GREY)).toBe(3.54);
    expect(ratio(vibeGrey, surface)).toBe(4.58);
    expect(hueDistance(hue(vibeGrey), hueAngle(MOCK_ROW_GREY))).toBeLessThan(1);
  });

  /** As `gameGrey` sits under `gameVoltDim` on dark: Fresh mix never reads stronger. */
  it('is a shade lighter than the dimmed olive, so Fresh mix never reads above Some common ground', () => {
    expect(lum(vibeGrey)).toBeGreaterThan(lum(oliveInkDim));
  });

  it('draws its dot in line — the card’s own border, the mock’s value to within a unit', () => {
    expect(against(line, MOCK_GREY_DOT)).toBeLessThanOrEqual(1.01);
  });

  /**
   * **Under a mark's 3:1, on purpose** (7.39): the dot under You on a row only you have says the row
   * is yours, which every row is — the grey words and the missing band say it too, and the row is
   * spoken. A dot that read as strongly as the olive would claim a match.
   */
  it('is a faint dot by design — never the only signal', () => {
    expect(ratio(line, surface)).toBe(1.3);
    expect(ratio(line, surface)).toBeLessThan(MARK);
    expect(ratio(vibeGrey, surface)).toBeGreaterThanOrEqual(AA);
  });

  /** One fill per band whatever the ground (ADR-0207 §8): the card's bar reads the row's table. */
  it('fills the card’s bar from the row’s own table', () => {
    expect(SOCIAL_VIBE_CARD_FILL).toBe(SOCIAL_VIBE_ON_DARK);
  });
});

/**
 * ADR-0207 §8: one fill per band, whatever the ground. On paper every fill is a shade beside the
 * `line2` track — volt itself 1,07, as the mock draws it — and never the only signal: the % and its
 * word are printed above the bar.
 */
describe('the bar on paper', () => {
  it('fills volt, the dimmed volt and the grey over a line2 track', () => {
    expect(ratio(volt, line2)).toBe(1.07);
    expect(ratio(gameVoltDim, line2)).toBe(2.47);
    expect(ratio(gameGrey, line2)).toBe(2.6);
  });
});
