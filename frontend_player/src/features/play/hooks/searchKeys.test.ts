import { withheldSeats } from '../domain/lineup';

import { RANKED_LIST_QUERY_OPTIONS, searchKeys } from './searchKeys';

describe('query keys', () => {
  it('nests every key under the feature root, so a sign-out clears them together', () => {
    expect(searchKeys.detail('s1')).toEqual(['play', 'search', 'detail', 's1']);
    expect(searchKeys.forecasts()).toEqual(['play', 'search', 'forecast']);
  });

  it('keys a ranked list by its search id — one key for the pool, the shortlist and the deal', () => {
    expect(searchKeys.detail('s1')).not.toEqual(searchKeys.detail('s2'));
  });

  it('keys a forecast by the search and the set of players', () => {
    expect(searchKeys.forecast('s1', ['b', 'a'])).toEqual([
      'play',
      'search',
      'forecast',
      's1',
      ['a', 'b'],
    ]);
  });

  it('re-arranging four costs no round trip: seat order is not in the key', () => {
    // ForecastResponse returns every arrangement of the four you composed, so a swap picks a
    // different arrangement out of a response already held.
    expect(searchKeys.forecast('s1', ['a', 'b', 'c'])).toEqual(
      searchKeys.forecast('s1', ['c', 'a', 'b']),
    );
  });

  it('changing who is on the court does cost one', () => {
    expect(searchKeys.forecast('s1', ['a', 'b'])).not.toEqual(
      searchKeys.forecast('s1', ['a', 'c']),
    );
  });

  it("does not sort the caller's own list while keying it", () => {
    const players = ['c', 'a', 'b'];
    searchKeys.forecast('s1', players);

    expect(players).toEqual(['c', 'a', 'b']);
  });

  it('asks the same four off two searches as two questions — search_id is the origin key', () => {
    expect(searchKeys.forecast('s1', ['a', 'b'])).not.toEqual(
      searchKeys.forecast('s2', ['a', 'b']),
    );
  });
});

describe('a seat the live gates no longer admit', () => {
  it('is still in the forecast key, so the number is about the court on screen', () => {
    // The mark is derived beside the line-up and subtracted from nothing: dropping a marked
    // player would make the figure silently disagree with the four in front of the player,
    // and would force a second cause for *provisional*.
    const lineup = { originSearchId: 's1', seats: ['player-a', 'player-b'] };
    const marked = withheldSeats(lineup, ['player-b']);

    expect(marked).toEqual(['player-a']);
    expect(searchKeys.forecast(lineup.originSearchId, lineup.seats)).toContainEqual(
      expect.arrayContaining(marked),
    );
  });
});

describe('the ranked-list override of the global defaults', () => {
  it('never goes stale on a timer and never refetches on foreground', () => {
    // Foregrounding under the app-wide `refetchOnWindowFocus: true` would reorder the pool
    // under the player's finger — AC-70's harm, arriving from focus.
    expect(RANKED_LIST_QUERY_OPTIONS.staleTime).toBe(Infinity);
    expect(RANKED_LIST_QUERY_OPTIONS.refetchOnWindowFocus).toBe(false);
  });

  it('never retries by itself, so the Try again the player can see is reachable', () => {
    // One automatic attempt is 15s of timeout plus a second of backoff plus another 15s, so
    // the visible *Try again* could not appear for ~31 seconds. An automatic retry the player
    // cannot see is a manual retry they cannot reach.
    expect(RANKED_LIST_QUERY_OPTIONS.retry).toBe(false);
  });

  it('outlives the screens that read it, so a line-up cannot lose its origin to the collector', () => {
    // Find a game renders no search. Under the app-wide five-minute gcTime, a player who
    // walked back from the builder and thought about it would return to a line-up whose
    // origin — and therefore whose rows, and whose guard — had been collected.
    expect(RANKED_LIST_QUERY_OPTIONS.gcTime).toBe(Infinity);
  });
});
