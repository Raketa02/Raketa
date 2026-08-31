/**
 * How the rating's numbers are written. Comma decimals, two places — the house convention
 * the design system's quick reference states, and the other half of what keeps a row from
 * reflowing when a level goes from 2,71 to 2,80.
 */

import { formatLevel, formatPercent, formatRange } from './ratingFormat';

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
