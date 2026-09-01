/**
 * The sort row and the ordering under it — **two rules the pool must not get wrong.**
 *
 * A stood-down distance sorts **last** rather than as a zero, and *Best fit* stays reachable
 * once the player has left the order they arrived in. The second is the non-obvious one: the
 * chip is withheld exactly when the returned order already is best-fit order, so a pool that
 * drew `sorts_available` and nothing else would make *Closest* a one-way door.
 */

import type { Candidate } from './candidate';

import { orderPool, poolSortRow } from './poolOrder';

function row(playerId: string, fit: number, distanceKm?: number): Candidate {
  return {
    playerId,
    fit,
    ...(distanceKm === undefined ? {} : { distanceKm }),
    card: {
      nickname: playerId,
      areaCode: 'A+050612+0019938',
      socialTags: [],
      level: 2.7,
      band: 'Established',
      range: { low: 2.5, high: 2.9 },
    },
    terms: [],
    concerns: [],
    livenessReasons: [],
    degradedTerms: [],
    modifiers: [],
  };
}

const ids = (rows: readonly Candidate[]) => rows.map((one) => one.playerId);

describe('the order the rows arrived in', () => {
  const rows = [row('a', 61, 9), row('b', 88, 2), row('c', 74, 5)];

  it('is what the pool draws until the player chooses otherwise', () => {
    expect(ids(orderPool(rows, undefined))).toEqual(['a', 'b', 'c']);
  });

  it('is what a sort this build cannot perform falls back to', () => {
    // `EVENEST` reads `would_be_forecast`, which nothing in the backend has ever written, and
    // `MOST_RELIABLE` reads a published Player Score that does not cross. Neither is offered
    // today; both keep a word so the table is exhaustive by type.
    expect(ids(orderPool(rows, 'EVENEST'))).toEqual(['a', 'b', 'c']);
    expect(ids(orderPool(rows, 'MOST_RELIABLE'))).toEqual(['a', 'b', 'c']);
  });
});

describe('best fit', () => {
  it('sorts by the printed number, which is not the order the engine returned', () => {
    const rows = [row('a', 61), row('b', 88), row('c', 74)];

    expect(ids(orderPool(rows, 'BEST_FIT'))).toEqual(['b', 'c', 'a']);
  });

  it('leaves two equal numbers in the order they were served', () => {
    const rows = [row('a', 74), row('b', 74)];

    expect(ids(orderPool(rows, 'BEST_FIT'))).toEqual(['a', 'b']);
  });
});

describe('closest', () => {
  it('sorts by kilometres', () => {
    const rows = [row('a', 61, 9), row('b', 88, 2), row('c', 74, 5)];

    expect(ids(orderPool(rows, 'CLOSEST'))).toEqual(['b', 'c', 'a']);
  });

  /**
   * An omitted distance is the term standing down, not a zero — which is exactly why
   * `distance_km` was promoted out of the evidence in the first place.
   */
  it('puts a stood-down distance last rather than first', () => {
    const rows = [row('a', 61), row('b', 88, 9), row('c', 74, 5)];

    expect(ids(orderPool(rows, 'CLOSEST'))).toEqual(['c', 'b', 'a']);
  });
});

describe('the sort row', () => {
  it('is empty when the server offers nothing, so the row is not drawn', () => {
    expect(poolSortRow([], undefined)).toEqual([]);
  });

  it('draws what the server offered, in the order it offered it', () => {
    expect(poolSortRow(['BEST_FIT', 'CLOSEST'], undefined)).toEqual(['BEST_FIT', 'CLOSEST']);
  });

  /** A chip this build has no ordering for would be a control that does nothing. */
  it('drops a sort nothing here can perform', () => {
    expect(poolSortRow(['CLOSEST', 'EVENEST', 'MOST_RELIABLE'], undefined)).toEqual(['CLOSEST']);
  });

  /**
   * *Best fit* is withheld precisely when the returned order already is best-fit order — so
   * tapping *Closest* would otherwise strand the player with no control representing where
   * they came from.
   */
  it('gains the way back once the player has left the order they arrived in', () => {
    expect(poolSortRow(['CLOSEST'], 'CLOSEST')).toEqual(['BEST_FIT', 'CLOSEST']);
  });

  it('does not offer the way back before anybody has left', () => {
    expect(poolSortRow(['CLOSEST'], undefined)).toEqual(['CLOSEST']);
  });

  it('adds nothing where the server offered the way back itself', () => {
    expect(poolSortRow(['BEST_FIT', 'CLOSEST'], 'CLOSEST')).toEqual(['BEST_FIT', 'CLOSEST']);
  });
});
