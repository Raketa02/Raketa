/**
 * One query key and one mutation key, and the two never meet.
 *
 * The mutation key is what the room filters the cache on to find what this feature's writes were
 * refused with, so it is asserted by value: a spelling drift there would not fail a type and would
 * silently empty the room's fold.
 */

import { planKeys } from './planKeys';

describe('the keys', () => {
  it('nest under the feature root, so a sign-out clears them together', () => {
    expect(planKeys.list()).toEqual(['plans', 'list']);
    expect(planKeys.writing()).toEqual(['plans', 'writing']);
  });

  /** One list, not several: there is no `GET /plans/{id}` to key a per-game entry under. */
  it('key the list by nothing', () => {
    expect(planKeys.list()).toHaveLength(2);
  });

  /**
   * Not keyed per court, deliberately: the one thing read off it is the account's standing, and a
   * hold met on one plan is true in every room.
   */
  it('make every write under one key, whichever game it is about', () => {
    expect(planKeys.writing()).toHaveLength(2);
    expect(planKeys.writing()).not.toEqual(planKeys.list());
  });
});
