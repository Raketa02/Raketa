/**
 * The one pluralisation seam.
 *
 * What is asserted is the seam rather than English: both forms come from the caller, so the
 * helper never derives a plural, and the day a market with three plural forms arrives there is
 * one function to change instead of every sentence that counts something.
 */

import { counted } from './counted';

describe('a counted phrase', () => {
  it('takes the singular at one and the plural everywhere else', () => {
    expect(counted(1, 'slot', 'slots')).toBe('1 slot');
    expect(counted(3, 'slot', 'slots')).toBe('3 slots');
    expect(counted(0, 'slot', 'slots')).toBe('0 slots');
  });

  it('derives nothing, so an irregular plural is the caller’s word', () => {
    expect(counted(2, 'person', 'people')).toBe('2 people');
  });
});
