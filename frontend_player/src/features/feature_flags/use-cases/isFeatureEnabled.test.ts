/**
 * The order a gate is answered in — fresh, then cached, then code default — and what counts as
 * the datafile having nothing to say.
 *
 * Not a test of Featurevisor. Which players a percentage or a segment reaches is the SDK's, and
 * the flags repo's specs prove it; the two datafiles here are the plainest *on* and *off* it
 * builds, so a failure means the order is wrong rather than an evaluation.
 */

import type { Datafile, FlagContext } from '../domain/featureFlags';

import { isFeatureEnabled } from './isFeatureEnabled';

const PLAYER: FlagContext = {
  playerId: '11111111-2222-4333-8444-555555555555',
  isTester: false,
  platform: 'ios',
  appVersion: '0.1.0',
};

/** `find_a_game` for everyone, or for no one — the flags repo's `percentage: 100` and `0`. */
function findAGameFor(percentage: 100 | 0, revision = '1'): Datafile {
  return {
    schemaVersion: '2',
    revision,
    segments: {},
    features: {
      find_a_game: {
        bucketBy: 'playerId',
        traffic: [{ key: 'everyone', segments: '*', percentage: percentage * 1000 }],
      },
    },
  };
}

/** A datafile that does not mention the feature — the two repositories disagreeing. */
const SILENT: Datafile = { schemaVersion: '2', revision: '1', segments: {}, features: {} };

describe('a gate with a datafile', () => {
  it('is on when the datafile turns it on', () => {
    expect(isFeatureEnabled('find_a_game', { fresh: findAGameFor(100), context: PLAYER })).toBe(
      true,
    );
  });

  it('is off when the datafile turns it off', () => {
    expect(isFeatureEnabled('find_a_game', { fresh: findAGameFor(0), context: PLAYER })).toBe(
      false,
    );
  });
});

describe('the fallback order', () => {
  it('takes the fresh datafile over the cached one', () => {
    expect(
      isFeatureEnabled('find_a_game', {
        fresh: findAGameFor(100, '2'),
        cached: findAGameFor(0, '1'),
        context: PLAYER,
      }),
    ).toBe(true);
  });

  it('takes the cached datafile when nothing was fetched', () => {
    expect(isFeatureEnabled('find_a_game', { cached: findAGameFor(0), context: PLAYER })).toBe(
      false,
    );
  });

  it('takes the code default when there is neither', () => {
    expect(isFeatureEnabled('find_a_game', { cached: null, context: PLAYER })).toBe(true);
  });
});

describe('a datafile with nothing to say', () => {
  // The SDK answers `false` for a feature it cannot find. Taken at its word, a key missing from
  // the flags repo would switch Find a game off for everybody; ADR-0180 says it evaluates to its
  // code default instead.
  it('leaves a feature it does not name at its code default', () => {
    expect(isFeatureEnabled('find_a_game', { fresh: SILENT, context: PLAYER })).toBe(true);
  });

  // A rollout buckets by player, and with no player there is nobody to bucket.
  it('leaves every feature at its code default when there is no player to ask about', () => {
    expect(isFeatureEnabled('find_a_game', { fresh: findAGameFor(0), context: undefined })).toBe(
      true,
    );
  });

  it('answers each datafile it is handed, not the first one it saw', () => {
    expect(isFeatureEnabled('find_a_game', { fresh: findAGameFor(0), context: PLAYER })).toBe(
      false,
    );
    expect(isFeatureEnabled('find_a_game', { fresh: SILENT, context: PLAYER })).toBe(true);
    expect(isFeatureEnabled('find_a_game', { fresh: findAGameFor(0), context: PLAYER })).toBe(
      false,
    );
  });
});
