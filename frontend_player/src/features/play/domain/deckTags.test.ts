/**
 * The deck card's reading of the Social tag overlap: **the shared ones first**.
 */

import type { SocialTagOverlap } from '@/shared/vocabulary/socialTagOverlap';

import { sharedFirst } from './deckTags';

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
