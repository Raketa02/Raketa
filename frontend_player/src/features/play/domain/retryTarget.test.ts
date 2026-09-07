/**
 * What *Try again* means, on the one wait where it is ambiguous.
 *
 * The ambiguity is expensive rather than cosmetic: a search and a read-back are two acts with
 * two ids, so a retry that re-ran the search would mint a new record and orphan the line-up
 * bound to the old one — and `POST /forecasts` answers that with `404 search_not_found`, one
 * code for four cases, so a client that did this to itself could not even diagnose it.
 */

import { retryTarget } from './retryTarget';

describe('what a retry re-runs', () => {
  it('re-fires the search when nothing was ever recorded', () => {
    expect(retryTarget(undefined)).toEqual({ kind: 'the-search' });
  });

  it('re-reads the record once there is one', () => {
    expect(retryTarget('search-1')).toEqual({ kind: 'the-record', searchId: 'search-1' });
  });

  it('never mints a second search over a record a line-up may be bound to', () => {
    // Running a fresh search stays an explicit act the player chooses, which is also what
    // keeps it inside the origin guard rather than arriving as a fourth trigger the guard
    // never sees.
    expect(retryTarget('search-1').kind).not.toBe('the-search');
  });
});
