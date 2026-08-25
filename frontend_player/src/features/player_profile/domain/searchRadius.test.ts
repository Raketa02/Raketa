/**
 * The Search radius: the bounds arithmetic, with no slider anywhere near it.
 *
 * Every number here arrives from `GET /player-profile/options` and is re-validated on the
 * write path, so what these rules owe is **a value the commit will accept, whatever the
 * finger did** — on a step boundary, inside the range, at both ends. The bounds served
 * today are 1–50 in whole kilometres; nothing below asserts those four numbers, because a
 * suite that pinned them would be the second, staler copy this rule exists not to be.
 */

import {
  openingRadius,
  radiusAtFraction,
  radiusFraction,
  steppedRadius,
  topOfScale,
  type SearchRadiusBounds,
} from './searchRadius';

/** The served shape, with numbers chosen to make each rule visible rather than to be real. */
const BOUNDS: SearchRadiusBounds = { minimumKm: 1, maximumKm: 50, stepKm: 1, defaultKm: 10 };

/** A step that does not divide the range, which is where the ends stop being obvious. */
const COARSE: SearchRadiusBounds = { minimumKm: 2, maximumKm: 21, stepKm: 5, defaultKm: 7 };

describe('what the step opens at', () => {
  it('is the served default when the player has not answered', () => {
    expect(openingRadius(undefined, BOUNDS)).toBe(10);
  });

  /**
   * The part's promise: walking back to a step finds the answer that was given. A step
   * that re-opened at the default would silently discard it on the way past.
   */
  it('is what the player already chose, once they have chosen', () => {
    expect(openingRadius(25, BOUNDS)).toBe(25);
  });
});

describe('the top of the scale', () => {
  it('is the served maximum when the step divides the range', () => {
    expect(topOfScale(BOUNDS)).toBe(50);
  });

  /**
   * The far end of the track has to be a value the commit accepts. 2 + 5n reaches 17 and
   * then 22, so 21 is inside the range and off the step — and a track whose end produced
   * it would be a control that can only be operated into a refusal.
   */
  it('stops at the last value on a step, never at an unreachable maximum', () => {
    expect(topOfScale(COARSE)).toBe(17);
  });
});

describe('where a finger lands', () => {
  it('reads the start of the track as the smallest radius and the end as the largest', () => {
    expect(radiusAtFraction(0, BOUNDS)).toBe(1);
    expect(radiusAtFraction(1, BOUNDS)).toBe(50);
  });

  /** Whole kilometres, so nobody lands on a distance the matcher could not use. */
  it('snaps to whole steps rather than to wherever the finger was', () => {
    expect(radiusAtFraction(0.5, BOUNDS)).toBe(26);
    expect(radiusAtFraction(0.505, BOUNDS)).toBe(26);
  });

  it('counts steps from the minimum, not from zero', () => {
    expect(radiusAtFraction(0, COARSE)).toBe(2);
    expect(radiusAtFraction(0.5, COARSE)).toBe(12);
    expect(radiusAtFraction(1, COARSE)).toBe(17);
  });

  /**
   * A press outside the track is a press on the row, and the row is the control. Past
   * either end it means the end it is past — never a number outside the bounds.
   */
  it('holds a press past either end of the track at that end', () => {
    expect(radiusAtFraction(-0.4, BOUNDS)).toBe(1);
    expect(radiusAtFraction(1.4, BOUNDS)).toBe(50);
  });

  /** A row that has not been laid out yet has no width, and a division by it is not a value. */
  it('answers the smallest radius rather than NaN when the track has no width', () => {
    expect(radiusAtFraction(Number.NaN, BOUNDS)).toBe(1);
  });
});

describe('where the thumb is drawn', () => {
  it('puts the smallest radius at the start and the largest at the end', () => {
    expect(radiusFraction(1, BOUNDS)).toBe(0);
    expect(radiusFraction(50, BOUNDS)).toBe(1);
  });

  it('places everything between them on the full served scale', () => {
    expect(radiusFraction(25.5, BOUNDS)).toBe(0.5);
  });

  /**
   * A radius recorded under bounds that have since been narrowed is still a fact about the
   * player — the backend's fold accepts what its write path refuses. The thumb stays on
   * the track rather than being drawn off the end of it.
   */
  it('keeps a radius from outside the current bounds on the track', () => {
    expect(radiusFraction(80, BOUNDS)).toBe(1);
    expect(radiusFraction(0, BOUNDS)).toBe(0);
  });
});

describe('one step, by assistive technology or a keyboard', () => {
  it('moves by exactly the served step in each direction', () => {
    expect(steppedRadius(10, BOUNDS, 'increment')).toBe(11);
    expect(steppedRadius(10, BOUNDS, 'decrement')).toBe(9);
    expect(steppedRadius(7, COARSE, 'increment')).toBe(12);
    expect(steppedRadius(7, COARSE, 'decrement')).toBe(2);
  });

  /** At an end there is nowhere to go, and going nowhere is not going outside the bounds. */
  it('stops at each end rather than stepping past it', () => {
    expect(steppedRadius(1, BOUNDS, 'decrement')).toBe(1);
    expect(steppedRadius(50, BOUNDS, 'increment')).toBe(50);
    expect(steppedRadius(17, COARSE, 'increment')).toBe(17);
  });

  /** Off-step is what a narrowed range leaves behind; a step from it lands back on one. */
  it('lands back on a step from a value that is not on one', () => {
    expect(steppedRadius(9, COARSE, 'increment')).toBe(12);
    expect(steppedRadius(9, COARSE, 'decrement')).toBe(7);
  });
});
