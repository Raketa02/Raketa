/**
 * How the rating's numbers are written. Comma decimals — the house convention the design
 * system's quick reference states, and the other half of what keeps a row from reflowing when a
 * level goes from 2,71 to 2,80.
 *
 * **Two places for a Level and one for a star average**, which is the one thing in this file
 * worth being careful about: both are on a one-to-five scale, and the second decimal is a
 * precision the platform does not publish for the second of them.
 */

import {
  formatDistanceKm,
  formatLevel,
  formatPercent,
  formatRange,
  formatSignedLevel,
  formatStars,
  formatZloty,
} from './ratingFormat';

describe('levels', () => {
  it('writes two decimals with a comma, whatever the value arrived as', () => {
    expect(formatLevel(2.71)).toBe('2,71');
    // A whole number is still written to two places: 3 and 3,00 must be the same width in
    // a column, which is the entire reason for a fixed number of decimals.
    expect(formatLevel(3)).toBe('3,00');
    expect(formatLevel(2.7)).toBe('2,70');
  });

  it('rounds rather than truncating', () => {
    expect(formatLevel(2.716)).toBe('2,72');
  });

  /**
   * **U+2212 and never the hyphen** — `the-words.md` §6.2's *"two decimals, decimal comma,
   * U+2212 minus"*.
   *
   * A Level is 1,00–5,00, so nothing was negative until the forecast card's **gap**, which is
   * one side's strength minus the other's and signed by construction
   * ([#290](https://github.com/Rakieta02/Rakieta/issues/290)).
   */
  it('writes a negative one with the typographic minus', () => {
    expect(formatLevel(-0.09)).toBe('\u22120,09');
    expect(formatLevel(-1.5)).toBe('\u22121,50');
  });
});

describe('a movement on that scale', () => {
  /**
   * The competitive card's stake boxes print two figures whose **signs are the fact**
   * ([#312](https://github.com/Rakieta02/Rakieta/issues/312)), so the gain carries a plus that a
   * Level never needs.
   */
  it('signs a gain, which is the whole of what it adds', () => {
    expect(formatSignedLevel(0.08)).toBe('+0,08');
    expect(formatSignedLevel(1)).toBe('+1,00');
  });

  it('leaves a loss the typographic minus it already had', () => {
    expect(formatSignedLevel(-0.05)).toBe('\u22120,05');
    expect(formatSignedLevel(-0.05)).toBe(formatLevel(-0.05));
  });

  it('signs a nought neither way, because nothing moved', () => {
    expect(formatSignedLevel(0)).toBe('0,00');
  });
});

describe('ranges', () => {
  it('writes both ends the same way, with a spaced en dash between them', () => {
    expect(formatRange({ low: 2.09, high: 3.33 })).toBe('2,09 – 3,33');
  });
});

describe('a star average', () => {
  /**
   * **One decimal, and never two.** The platform publishes this mean to one place, so `4,70`
   * would claim a second that nobody serves — on the one figure whose design is being coarse
   * enough to be honest. Both are on a one-to-five scale, which is exactly why the two
   * formatters have to stay apart.
   */
  it('writes one decimal where a level writes two', () => {
    expect(formatStars(4.7)).toBe('4,7');
    expect(formatStars(4.7)).not.toBe(formatLevel(4.7));
  });

  /** A whole average is still written to its one place: `3` and `3,0` are the same figure. */
  it('keeps the trailing nought rather than trimming it', () => {
    expect(formatStars(3)).toBe('3,0');
  });

  it('rounds rather than truncating', () => {
    expect(formatStars(4.25)).toBe('4,3');
  });
});

describe('a percentage', () => {
  it('is whole, always', () => {
    // No percentage in this app carries a decimal: the engine's precision does not survive
    // being read as "28,4% sure", and nothing on any screen compares two of them.
    expect(formatPercent(28)).toBe('28%');
    expect(formatPercent(28.4)).toBe('28%');
  });
});

describe('a distance', () => {
  /**
   * **One decimal, a comma, and the unit** — the number the deck card, the record's identity
   * line and the why-fit sentence all print for one person (ADR-0174 §2). The server serves it
   * to one place already, measured spot to spot; this is the print and nothing else.
   */
  it('writes one decimal with a comma and the unit', () => {
    expect(formatDistanceKm(1.9)).toBe('1,9 km');
    expect(formatDistanceKm(0.6)).toBe('0,6 km');
  });

  /** A whole number of kilometres is still written to its one place: nothing prints `12 km`. */
  it('keeps the trailing nought rather than printing a whole kilometre', () => {
    expect(formatDistanceKm(12)).toBe('12,0 km');
  });

  it('rounds rather than truncating, so a float that arrived as 1.85 is not written as 1,8', () => {
    expect(formatDistanceKm(1.85)).toBe('1,9 km');
    expect(formatDistanceKm(1.96)).toBe('2,0 km');
  });

  /**
   * The floor is the **server's** — `distance_km` is never served below `0.1` — and the print
   * neither raises it nor lowers it: the smallest number a screen can say is `0,1 km`, and it
   * is said as served.
   */
  it('prints the floor as served', () => {
    expect(formatDistanceKm(0.1)).toBe('0,1 km');
  });
});

/**
 * **A share in złoty** — the first price this app draws (#553), so the rule is decided here, as
 * `docs/value-formatting.md` said the first client to draw one would: the decimal comma, a space
 * before `zł`, and the grosze only when there are some.
 */
describe('money', () => {
  it('writes whole złoty without grosze, the unit after a space', () => {
    expect(formatZloty(3200)).toBe('32 zł');
    expect(formatZloty(0)).toBe('0 zł');
  });

  it('writes grosze to two places with the comma when there are some', () => {
    expect(formatZloty(2750)).toBe('27,50 zł');
    expect(formatZloty(2705)).toBe('27,05 zł');
  });
});
