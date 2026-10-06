/** The room's own folds — where a page backward starts from, and whether bubbles name authors. */

import { earlierThan } from './room';

describe('paging backward', () => {
  it('asks for what is before the oldest thing held, and stops at the beginning', () => {
    expect(earlierThan(7)).toBe(7);
    expect(earlierThan(1)).toBeUndefined();
    expect(earlierThan(undefined)).toBeUndefined();
  });
});
