/**
 * The sort row and the ordering under it — **two rules the pool must not get wrong.**
 *
 * A stood-down distance sorts **last** rather than as a zero, and *Best fit* stays reachable
 * once the player has left the order they arrived in. The second is the non-obvious one: the
 * chip is withheld exactly when the returned order already is best-fit order, so a pool that
 * drew `sorts_available` and nothing else would make *Closest* a one-way door.
 */

import type { Candidate } from './candidate';

import { bestMatchId, orderPool, poolSortRow } from './poolOrder';

function row(playerId: string, fit: number, distanceKm?: number, playerScore?: number): Candidate {
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
      ...(playerScore === undefined ? {} : { playerScore }),
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
    // `EVENEST` reads `would_be_forecast`, which nothing in the backend has ever written, so it
    // keeps a word and no ordering — the table stays exhaustive by type.
    expect(ids(orderPool(rows, 'EVENEST'))).toEqual(['a', 'b', 'c']);
  });

  it('is what a sort whose reading nobody carries leaves untouched', () => {
    // Not the same statement as the one above. `MOST_RELIABLE` *has* an ordering now; what
    // these rows have is no reading for it, and every row reading the same is what the server
    // withholds the chip for. Tapping it anyway is a no-op rather than a reshuffle.
    expect(ids(orderPool(rows, 'MOST_RELIABLE'))).toEqual(['a', 'b', 'c']);
  });
});

describe('most reliable', () => {
  it('sorts by the published Player Score, highest first', () => {
    const rows = [row('a', 61, 9, 40), row('b', 88, 2, 91), row('c', 74, 5, 63)];

    expect(ids(orderPool(rows, 'MOST_RELIABLE'))).toEqual(['b', 'c', 'a']);
  });

  it('puts a player the platform has watched nothing of last, never first', () => {
    // `CLOSEST`'s rule for `CLOSEST`'s reason: the omission is *no record*, and a `0` read out
    // of it would sort them as the least reliable person here rather than the one there is
    // nothing to say about.
    const rows = [row('a', 61, 9), row('b', 88, 2, 12), row('c', 74, 5, 63)];

    expect(ids(orderPool(rows, 'MOST_RELIABLE'))).toEqual(['c', 'b', 'a']);
  });

  it('leaves two equal scores in the order they were served', () => {
    const rows = [row('a', 61, 9, 70), row('b', 88, 2, 70), row('c', 74, 5, 91)];

    expect(ids(orderPool(rows, 'MOST_RELIABLE'))).toEqual(['c', 'a', 'b']);
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
    expect(poolSortRow(['CLOSEST', 'EVENEST'], undefined)).toEqual(['CLOSEST']);
  });

  it('draws the reliability chip the server offers, now that it can order by it', () => {
    expect(poolSortRow(['BEST_FIT', 'CLOSEST', 'MOST_RELIABLE'], undefined)).toEqual([
      'BEST_FIT',
      'CLOSEST',
      'MOST_RELIABLE',
    ]);
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

/**
 * **The pin** — the one reordering this client does that is not a comparator.
 *
 * It is bound to the served order, so every assertion here is paired: what the default draws,
 * and what the same rows draw the moment a chip is tapped.
 */
describe('the pin', () => {
  const lifted = (playerId: string, fit: number, distanceKm?: number): Candidate => ({
    ...row(playerId, fit, distanceKm),
    inclusionReason: 'INTEREST_LIFT',
  });

  it('leaves the served order exactly as it is when nobody was lifted', () => {
    const rows = [row('a', 61, 9), row('b', 88, 2), row('c', 74, 5)];

    expect(ids(orderPool(rows, undefined))).toEqual(['a', 'b', 'c']);
  });

  it('lifts somebody who already said yes to the top, whatever they scored', () => {
    const rows = [row('a', 88, 9), lifted('b', 41, 2), row('c', 74, 5)];

    expect(ids(orderPool(rows, undefined))).toEqual(['b', 'a', 'c']);
  });

  it('keeps two pinned rows in the order the engine served them', () => {
    const rows = [row('a', 88), lifted('b', 41), row('c', 74), lifted('d', 55)];

    expect(ids(orderPool(rows, undefined))).toEqual(['b', 'd', 'a', 'c']);
  });

  it('releases the moment the player asks for a different order', () => {
    const rows = [row('a', 88, 9), lifted('b', 41, 2), row('c', 74, 5)];

    // Their honest place under each of the three: the number, the kilometres, and the record.
    expect(ids(orderPool(rows, 'BEST_FIT'))).toEqual(['a', 'c', 'b']);
    expect(ids(orderPool(rows, 'CLOSEST'))).toEqual(['b', 'c', 'a']);
    expect(ids(orderPool(rows, 'MOST_RELIABLE'))).toEqual(['a', 'b', 'c']);
  });

  it('releases even where the sort this build performs reorders nothing', () => {
    // `EVENEST` has a word and no ordering, and a `MOST_RELIABLE` over rows with no readings
    // separates nobody. Either way the player has **left** the served order, and the pin is a
    // property of that order rather than of whether the comparator moved anything.
    const rows = [row('a', 88, 9), lifted('b', 41, 2), row('c', 74, 5)];

    expect(ids(orderPool(rows, 'EVENEST'))).toEqual(['a', 'b', 'c']);
  });

  it('does not touch the printed number, which is the whole of why it is not a bonus', () => {
    const rows = [row('a', 88), lifted('b', 41)];

    expect(orderPool(rows, undefined).map((one) => one.fit)).toEqual([41, 88]);
  });
});

/**
 * **The coral tag** — which row wears it, and on which orderings it exists at all.
 *
 * The input is the rows in the order the **server** served them, which is what makes *the row
 * the server served first* a tie-break this function can state rather than a property of
 * whatever array a screen happened to draw.
 */
describe('the best match', () => {
  it('is the highest number in the order the rows arrived in', () => {
    const rows = [row('a', 61), row('b', 88), row('c', 74)];

    expect(bestMatchId(rows, undefined)).toBe('b');
  });

  it('is the first row under best fit, which is the same row', () => {
    const rows = [row('a', 61), row('b', 88), row('c', 74)];

    expect(bestMatchId(rows, 'BEST_FIT')).toBe('b');
  });

  it('goes to the row the server served first when two share the highest number', () => {
    const rows = [row('a', 74), row('b', 88), row('c', 88)];

    expect(bestMatchId(rows, undefined)).toBe('b');
  });

  it('exists on nobody under the three orderings that are not about the number', () => {
    const rows = [row('a', 61), row('b', 88), row('c', 74)];

    for (const sort of ['CLOSEST', 'EVENEST', 'MOST_RELIABLE'] as const) {
      expect(bestMatchId(rows, sort)).toBeUndefined();
    }
  });

  it('is nobody on an empty list', () => {
    expect(bestMatchId([], undefined)).toBeUndefined();
  });

  /**
   * The tag keys off **the ordering in force**, never off whether a chip was tapped — and this
   * is the state that would catch the other reading: `BEST_FIT` is withheld from
   * `sorts_available` precisely when the served order already is fit order, so on most searches
   * there is no chip to have tapped.
   */
  it('is drawn on a search whose sort row could never offer best fit', () => {
    const rows = [row('a', 88), row('b', 74), row('c', 61)];

    expect(poolSortRow([], undefined)).toEqual([]);
    expect(bestMatchId(rows, undefined)).toBe('a');
  });

  /**
   * `candidateTag` resolves the collision — the volt tag replaces the coral one on the card
   * they share, *"because it's the stronger fact"*. What this rule must not do is hand the
   * coral tag to the **second** best row, which would be the card saying *best match* about a
   * row that is not one.
   */
  it('still names the highest row when that row is the pinned one', () => {
    const rows = [row('a', 61), { ...row('b', 88), inclusionReason: 'INTEREST_LIFT' as const }];

    expect(bestMatchId(rows, undefined)).toBe('b');
  });
});
