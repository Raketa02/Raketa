/**
 * The sport bar's memory: long enough to answer a text, short enough that last
 * week's tap cannot hide tomorrow's match.
 */

import { VISIT_GAP_MS, withinSameVisit } from './visit';

const NOW = Date.parse('2026-08-23T12:00:00Z');

describe('whether a selection is still the same visit', () => {
  it('survives stepping out for two minutes', () => {
    expect(withinSameVisit(NOW - 2 * 60 * 1000, NOW)).toBe(true);
  });

  it('survives exactly the gap, and not a millisecond more', () => {
    expect(withinSameVisit(NOW - VISIT_GAP_MS, NOW)).toBe(true);
    expect(withinSameVisit(NOW - VISIT_GAP_MS - 1, NOW)).toBe(false);
  });

  it('does not survive the night', () => {
    expect(withinSameVisit(NOW - 18 * 60 * 60 * 1000, NOW)).toBe(false);
  });

  it('has nothing to survive when no selection was ever made', () => {
    expect(withinSameVisit(undefined, NOW)).toBe(false);
  });

  it('is half an hour', () => {
    expect(VISIT_GAP_MS).toBe(30 * 60 * 1000);
  });
});
