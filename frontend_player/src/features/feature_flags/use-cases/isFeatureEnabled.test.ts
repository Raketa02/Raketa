/**
 * The order a gate is answered in — fresh, then cached, then code default — and what counts as
 * the datafile having nothing to say.
 *
 * Not a test of Featurevisor. Which players a percentage or a segment reaches is the SDK's, and
 * the flags repo's specs prove it; the two datafiles here are the plainest *on* and *off* it
 * builds, so a failure means the order is wrong rather than an evaluation.
 */

import { FEATURE_DEFAULTS, type Datafile, type FlagContext } from '../domain/featureFlags';

import { isFeatureEnabled } from './isFeatureEnabled';

const PLAYER: FlagContext = {
  playerId: '11111111-2222-4333-8444-555555555555',
  isTester: false,
  platform: 'ios',
  appVersion: '0.1.0',
};

/** `classic_play` for everyone, or for no one — the flags repo's `percentage: 100` and `0`. */
function classicPlayFor(percentage: 100 | 0, revision = '1'): Datafile {
  return {
    schemaVersion: '2',
    revision,
    segments: {},
    features: {
      classic_play: {
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
    expect(isFeatureEnabled('classic_play', { fresh: classicPlayFor(100), context: PLAYER })).toBe(
      true,
    );
  });

  it('is off when the datafile turns it off', () => {
    expect(isFeatureEnabled('classic_play', { fresh: classicPlayFor(0), context: PLAYER })).toBe(
      false,
    );
  });
});

describe('the fallback order', () => {
  it('takes the fresh datafile over the cached one', () => {
    expect(
      isFeatureEnabled('classic_play', {
        fresh: classicPlayFor(100, '2'),
        cached: classicPlayFor(0, '1'),
        context: PLAYER,
      }),
    ).toBe(true);
  });

  // On, because on is the answer only the cache can give: the code default is off (#550).
  it('takes the cached datafile when nothing was fetched', () => {
    expect(isFeatureEnabled('classic_play', { cached: classicPlayFor(100), context: PLAYER })).toBe(
      true,
    );
  });

  it('takes the code default when there is neither', () => {
    expect(isFeatureEnabled('classic_play', { cached: null, context: PLAYER })).toBe(false);
  });
});

/**
 * The SDK answers `false` for a feature it cannot find, and `classic_play`'s code default is off
 * (#550) — so with the shipped default the two would agree and nothing here could fail. The
 * default is raised to **on** for these walks, which is what makes *the code default, not the
 * SDK's `false`* observable; the rule is about whichever default a key has.
 */
describe('a datafile with nothing to say', () => {
  beforeEach(() => {
    jest.replaceProperty(FEATURE_DEFAULTS, 'classic_play', true as never);
  });

  afterEach(() => {
    jest.restoreAllMocks();
  });

  // The SDK answers `false` for a feature it cannot find. Taken at its word, a key missing from
  // the flags repo would switch Classic play off for everybody; ADR-0180 says it evaluates to its
  // code default instead.
  it('leaves a feature it does not name at its code default', () => {
    expect(isFeatureEnabled('classic_play', { fresh: SILENT, context: PLAYER })).toBe(true);
  });

  // A rollout buckets by player, and with no player there is nobody to bucket.
  it('leaves every feature at its code default when there is no player to ask about', () => {
    expect(isFeatureEnabled('classic_play', { fresh: classicPlayFor(0), context: undefined })).toBe(
      true,
    );
  });

  it('answers each datafile it is handed, not the first one it saw', () => {
    expect(isFeatureEnabled('classic_play', { fresh: classicPlayFor(0), context: PLAYER })).toBe(
      false,
    );
    expect(isFeatureEnabled('classic_play', { fresh: SILENT, context: PLAYER })).toBe(true);
    expect(isFeatureEnabled('classic_play', { fresh: classicPlayFor(0), context: PLAYER })).toBe(
      false,
    );
  });
});
