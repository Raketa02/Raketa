/**
 * **A line's count, as drawn** (#822; ADR-0205 §6) — the served figure up to 99, *99+* past it, on the
 * count pill and on *See all N ›* alike.
 */

import { countFigure, withCount } from './countFigure';

describe('a line’s count, as drawn', () => {
  it.each([
    [0, '0'],
    [1, '1'],
    [14, '14'],
    [99, '99'],
  ])('writes %i as served', (count, figure) => {
    expect(countFigure(count)).toBe(figure);
  });

  /** The server stops counting at 100, which reads *100 or more*. */
  it.each([100, 250])('writes %i as 99+', (count) => {
    expect(countFigure(count)).toBe('99+');
  });
});

/** #822: *Players at your level, 14, collapsed* — the platform says the state after it. */
describe('a name with its count', () => {
  it('says the count after the name, as drawn', () => {
    expect(withCount('Players at your level', 14)).toBe('Players at your level, 14');
    expect(withCount('Players at your level', 100)).toBe('Players at your level, 99+');
  });

  it('is the name alone without one', () => {
    expect(withCount('Top 10', undefined)).toBe('Top 10');
  });
});
