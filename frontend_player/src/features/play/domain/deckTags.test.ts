/**
 * The deck card's two readings of the Social tag overlap: **the shared ones first**, and the
 * count the *Shared tags* tile prints — with the three spellings of absence kept apart, because
 * *0* is a claim and *—* is not.
 */

import type { SocialTagOverlap } from '@/shared/vocabulary/socialTagOverlap';

import { sharedFirst, sharedTagCount } from './deckTags';

const ROW: SocialTagOverlap & { readonly kind: 'shared' } = {
  kind: 'shared',
  tags: [
    { id: 'PLAYS_TO_WIN', shared: false },
    { id: 'HERE_TO_IMPROVE', shared: true },
    { id: 'STAYS_FOR_A_DRINK', shared: false },
    { id: 'QUIET_AND_FOCUSED', shared: true },
  ],
};

describe('the shared tags first', () => {
  /**
   * Up to six, wrapping — and the volt *· you too* must never be the one that is cut off. The
   * shared ones lead, and the rest keep the order the person published them in.
   */
  it('moves the shared tags to the front and keeps the rest in the person’s own order', () => {
    expect(sharedFirst(ROW.tags)).toEqual([
      { id: 'HERE_TO_IMPROVE', shared: true },
      { id: 'QUIET_AND_FOCUSED', shared: true },
      { id: 'PLAYS_TO_WIN', shared: false },
      { id: 'STAYS_FOR_A_DRINK', shared: false },
    ]);
  });
});

describe('the Shared tags tile', () => {
  it('counts the shared ones where the engine matched some', () => {
    expect(sharedTagCount(ROW)).toBe(2);
  });

  /** The amber answer is a claim — compared, and nothing matched — and a nought is what it says. */
  it('is nought where the engine compared and found nothing in common', () => {
    expect(sharedTagCount({ kind: 'none-in-common' })).toBe(0);
  });

  /** *We do not know* is not *there is nothing*: the tile prints a dash, never a nought. */
  it('is absent where nothing was compared, or the match is one this build cannot name', () => {
    expect(sharedTagCount({ kind: 'unknown', tags: ['PLAYS_TO_WIN'] })).toBeUndefined();
    expect(sharedTagCount({ kind: 'hidden' })).toBeUndefined();
  });
});
