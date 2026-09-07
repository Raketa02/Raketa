/**
 * How long each of the two waits may be seen for, and what a calm presentation takes off it.
 *
 * The split is the whole of [#269](https://github.com/Raketa02/Raketa/issues/269)'s last
 * criterion: **a hold is not an animation**, so the floor survives, and the stagger drawn over
 * it is motion, so it goes to zero. A helper that collapsed both would be the flash
 * `motion.hold` exists to refuse; one that collapsed neither would leave §G5's finding — *the
 * animations are killed but the 2,3-second stagger continues regardless* — exactly where it
 * was.
 */

import { theme } from '@/shared/ui';

import { searchingFloorMs } from './searchingWait';

const { fill, pool } = theme.motion.hold;

describe('the pool’s floor', () => {
  /**
   * It has no stagger over it, so there is nothing for a collapse to take — which is why the
   * pool is the variant that cannot be asked about one.
   */
  it('is a hold, and holds', () => {
    expect(searchingFloorMs({ kind: 'pool' })).toBe(pool);
  });
});

describe('the engine fill’s floor', () => {
  it('is the held half plus a seat’s worth of stagger for each seat after the first', () => {
    expect(searchingFloorMs({ kind: 'fill', seats: 1, collapsed: false })).toBe(fill);
    // §G5's 2,3 seconds: 650, and 550 more for each of the three seats after yours.
    expect(searchingFloorMs({ kind: 'fill', seats: 4, collapsed: false })).toBe(2300);
  });

  it('keeps the floor and drops the stagger when presentation collapses', () => {
    expect(searchingFloorMs({ kind: 'fill', seats: 4, collapsed: true })).toBe(fill);
    expect(searchingFloorMs({ kind: 'fill', seats: 1, collapsed: true })).toBe(fill);
  });

  /** A court the engine had nothing left to seat still waited for the answer that said so. */
  it('holds its floor with no seats to land', () => {
    expect(searchingFloorMs({ kind: 'fill', seats: 0, collapsed: false })).toBe(fill);
  });
});
