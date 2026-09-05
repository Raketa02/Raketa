/**
 * How the rating's numbers are written. Comma decimals, two places — the house convention
 * the design system's quick reference states, and the other half of what keeps a row from
 * reflowing when a level goes from 2,71 to 2,80.
 */

import { formatLevel, formatPercent, formatRange, formatSignedLevel } from './ratingFormat';

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
   * ([#290](https://github.com/Raketa02/Raketa/issues/290)).
   */
  it('writes a negative one with the typographic minus', () => {
    expect(formatLevel(-0.09)).toBe('\u22120,09');
    expect(formatLevel(-1.5)).toBe('\u22121,50');
  });
});

describe('a movement on that scale', () => {
  /**
   * The competitive card's stake boxes print two figures whose **signs are the fact**
   * ([#312](https://github.com/Raketa02/Raketa/issues/312)), so the gain carries a plus that a
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

describe('a percentage', () => {
  it('is whole, always', () => {
    // No percentage in this app carries a decimal: the engine's precision does not survive
    // being read as "28,4% sure", and nothing on any screen compares two of them.
    expect(formatPercent(28)).toBe('28%');
    expect(formatPercent(28.4)).toBe('28%');
  });
});
