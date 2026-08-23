/**
 * The key that makes leaving safe to send twice.
 *
 * The interesting properties are all about what the key is **not**: not the same
 * for two intents, not guessable from public data, and not longer than the
 * contract's bound.
 */

import { departureRequestKey } from './requestKey';

const MATCH = '5b0c0000-0000-4000-8000-000000000001';

/** The contract's own bound: `min_length: 1, max_length: 128`. */
const MAX_KEY_LENGTH = 128;

describe('a departure’s request key', () => {
  it('names the match it is about', () => {
    // The log is keyed on the whole string, so the prefix costs nothing — and the
    // first question anybody asks of a stuck departure is which match it was.
    expect(departureRequestKey(MATCH)).toContain(MATCH);
  });

  it('is a different key for a different intent', () => {
    // Two visits to the screen are two intents. If they shared a key, the second
    // departure of a player who came back would be answered with the first one's
    // outcome — for a different match, or after the first was abandoned.
    const keys = new Set(Array.from({ length: 50 }, () => departureRequestKey(MATCH)));

    expect(keys.size).toBe(50);
  });

  it('is not spelled out of anything a stranger can read', () => {
    // A key derived from the player and the match would survive a process death,
    // and would also be guessable: a person card carries a player id and Now
    // carries match ids, so anybody could file that key first and turn somebody
    // else's departure into a refusal. The random half is what prevents that.
    const drawn = departureRequestKey(MATCH, () => 0.123456789);
    const other = departureRequestKey(MATCH, () => 0.987654321);

    expect(drawn).not.toBe(MATCH);
    expect(drawn).not.toBe(other);
  });

  it('fits the contract’s bound even at its longest', () => {
    // `Math.random` at its most verbose in base 36. A key over the bound is a 422
    // on the one request that must not fail for a reason nobody can see.
    const longest = departureRequestKey(MATCH, () => 1 / 3);

    expect(longest.length).toBeLessThanOrEqual(MAX_KEY_LENGTH);
    expect(longest.length).toBeGreaterThan(MATCH.length);
  });
});
