/**
 * **The switch's three positions, and the one line each of them writes** (#662, ADR-0195 §6).
 */

import { filterPosition, FILTER_POSITIONS, minimumOf } from './reliabilityFilter';

describe('the reliability filter', () => {
  it('offers Off, at least Medium and at least High, in that order', () => {
    expect(FILTER_POSITIONS).toEqual(['OFF', 'MEDIUM', 'HIGH']);
  });

  it('reads the saved position off the record — Off where no minimum is set', () => {
    expect(filterPosition({ hides: 0, of: 11 })).toBe('OFF');
    expect(filterPosition({ minimum: 'MEDIUM', hides: 1, of: 11 })).toBe('MEDIUM');
    expect(filterPosition({ minimum: 'HIGH', hides: 2, of: 11 })).toBe('HIGH');
  });

  /** Off is written as `null` — the route's word for *every profile starts here*. */
  it('writes a minimum for an on position and null for Off', () => {
    expect(minimumOf('OFF')).toBeNull();
    expect(minimumOf('MEDIUM')).toBe('MEDIUM');
    expect(minimumOf('HIGH')).toBe('HIGH');
  });
});
