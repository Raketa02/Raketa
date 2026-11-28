/**
 * **The game card's ground, computed** — the colours the theme fences as a group's Games card's
 * alone, and every ratio their comments state
 * ([#553](https://github.com/Rakieta02/Rakieta/issues/553), the screens A2.3,
 * [Part 16](../../../docs/design-system.md#part-16--amendments-after-locking) 2026-09-30).
 *
 * `yesGround.test.ts`'s shape: 2.5's table has no row for this ground, so this is the row, and the
 * figures are derived rather than typed, so a nudge to any colour goes red here rather than in
 * somebody's eyes. The ratios are stated half-way down the gradient, which is where the forecast
 * and the grid sit.
 */

import {
  composite,
  contrast,
  hueAngle,
  hueDistance,
  luminance,
  parse,
} from '@/test-support/contrast';

import { theme } from './theme';

const ratio = (a: string, b: string) => contrast(parse(a).rgb, parse(b).rgb);

/** WCAG 2.1: 4.5:1 for text, 3:1 for large text and for a mark. */
const AA = 4.5;
const LARGE = 3;

/**
 * The gradient half-way down — where the forecast and the grid sit. Composited rather than typed,
 * so it moves with the two stops.
 */
const MIDDLE_RGB = composite(
  parse(theme.color.gameGroundTop).rgb,
  0.5,
  parse(theme.color.gameGroundFoot).rgb,
);
const MIDDLE = `rgb(${MIDDLE_RGB.map(Math.round).join(', ')})`;

describe('the game card’s ground', () => {
  it('is night’s family, top to foot', () => {
    const night = hueAngle(parse(theme.color.night).rgb);
    for (const ground of [theme.color.gameGroundTop, theme.color.gameGroundFoot, MIDDLE]) {
      expect(hueDistance(hueAngle(parse(ground).rgb), night)).toBeLessThan(12);
    }
  });

  it('carries white and volt past AAA', () => {
    expect(ratio(theme.color.surface, MIDDLE)).toBe(15.34);
    expect(ratio(theme.color.volt, MIDDLE)).toBe(12.24);
  });

  it('carries the forecast’s three figures as large text', () => {
    expect(ratio(theme.color.gameGreen, MIDDLE)).toBe(3.32);
    expect(ratio(theme.color.gameAmber, MIDDLE)).toBe(8.71);
    expect(ratio(theme.color.gameRed, MIDDLE)).toBe(3.39);
    for (const figure of [theme.color.gameGreen, theme.color.gameAmber, theme.color.gameRed]) {
      expect(ratio(figure, MIDDLE)).toBeGreaterThanOrEqual(LARGE);
    }
  });

  it('is red’s own family, lifted where `red` itself would not carry the figure', () => {
    const red = hueAngle(parse(theme.color.red).rgb);
    expect(hueDistance(hueAngle(parse(theme.color.gameRed).rgb), red)).toBeLessThan(4);
    expect(ratio(theme.color.red, MIDDLE)).toBeLessThan(LARGE);
  });
});

describe('what sits on the card’s own beds', () => {
  it('carries white on the green of the IN tag and the Book it now tag', () => {
    expect(ratio(theme.color.surface, theme.color.gameGreen)).toBe(4.62);
    expect(ratio(theme.color.surface, theme.color.gameGreen)).toBeGreaterThanOrEqual(AA);
  });

  it('carries the ribbon’s words, and the countdown under an hour in lifted coral', () => {
    expect(ratio(theme.color.surface, theme.color.gameRibbon)).toBe(11.66);
    expect(ratio(theme.color.gameCoral, theme.color.gameRibbon)).toBe(4.74);
    expect(ratio(theme.color.coral, theme.color.gameRibbon)).toBeLessThan(LARGE);
    expect(
      hueDistance(
        hueAngle(parse(theme.color.gameCoral).rgb),
        hueAngle(parse(theme.color.coral).rgb),
      ),
    ).toBeLessThan(2);
  });

  it('carries a rescue’s ribbon in white on coralInk', () => {
    expect(ratio(theme.color.surface, theme.color.coralInk)).toBeGreaterThanOrEqual(AA);
  });

  it('carries the share in volt and the late line in amber on both court beds', () => {
    expect(ratio(theme.color.volt, theme.color.gameCourt)).toBe(10.93);
    expect(ratio(theme.color.volt, theme.color.gameCourtBooked)).toBe(10.03);
    expect(ratio(theme.color.gameAmber, theme.color.gameCourt)).toBeGreaterThanOrEqual(AA);
    expect(ratio(theme.color.surface, theme.color.gameCourtBooked)).toBe(12.57);
  });

  it('tells the grid’s bright cell from the dark past 3:1, and the dim one by position and name', () => {
    expect(ratio(theme.color.volt, theme.color.gameCellDark)).toBeGreaterThanOrEqual(LARGE);
    expect(ratio(theme.color.gameCellDim, theme.color.gameCellDark)).toBe(2.07);
  });
});

/**
 * The Social vibe row's inks (#838; ADR-0207 §8, 7.38): volt and the two lower bands, each the
 * figure on the ground and the fill under `ink`, against the track it fills — `onDarkTag` over the
 * ground, which is mock 2's track to the pixel (white at 0,14).
 */
describe('the Social vibe row', () => {
  const TRACK_RGB = composite([255, 255, 255], parse(theme.color.onDarkTag).alpha, MIDDLE_RGB);
  const TRACK = `rgb(${TRACK_RGB.map(Math.round).join(', ')})`;
  const BANDS = [theme.color.volt, theme.color.gameVoltDim, theme.color.gameGrey];

  it('carries every band’s figure past AA on the ground — no figure needs large text’s 3:1', () => {
    expect(ratio(theme.color.gameVoltDim, MIDDLE)).toBe(5.31);
    expect(ratio(theme.color.gameGrey, MIDDLE)).toBe(5.05);
    for (const figure of BANDS) expect(ratio(figure, MIDDLE)).toBeGreaterThanOrEqual(AA);
  });

  it('carries the name in ink on every fill, and in white on the track', () => {
    expect(ratio(theme.color.ink, theme.color.gameVoltDim)).toBe(6.06);
    expect(ratio(theme.color.ink, theme.color.gameGrey)).toBe(5.77);
    for (const fill of BANDS) expect(ratio(theme.color.ink, fill)).toBeGreaterThanOrEqual(AA);
    expect(ratio(theme.color.surface, TRACK)).toBe(9.9);
  });

  it('tells every fill from the track it fills, as a mark must', () => {
    expect(ratio(theme.color.gameVoltDim, TRACK)).toBe(3.43);
    expect(ratio(theme.color.gameGrey, TRACK)).toBe(3.26);
    for (const fill of BANDS) expect(ratio(fill, TRACK)).toBeGreaterThanOrEqual(LARGE);
  });

  it('is one hue family: the dimmed volt is volt’s, the grey night’s, and neither is the forecast’s', () => {
    const volt = hueAngle(parse(theme.color.volt).rgb);
    expect(hueDistance(hueAngle(parse(theme.color.gameVoltDim).rgb), volt)).toBeLessThan(5);
    const night = hueAngle(parse(theme.color.night).rgb);
    expect(hueDistance(hueAngle(parse(theme.color.gameGrey).rgb), night)).toBeLessThan(5);
    for (const fill of BANDS) {
      expect([theme.color.gameGreen, theme.color.gameAmber, theme.color.gameRed]).not.toContain(
        fill,
      );
    }
  });

  it('dims in order: volt, then the dimmed volt, then the grey a shade under it', () => {
    const [volt, dim, grey] = BANDS.map((colour) => luminance(parse(colour).rgb));
    expect(volt).toBeGreaterThan(dim ?? 1);
    expect(dim).toBeGreaterThan(grey ?? 1);
  });
});
