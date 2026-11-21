import {
  FEATURE_DEFAULTS,
  datafileInUse,
  isReadableSchemaVersion,
  type Datafile,
} from './featureFlags';

const datafile = (revision: string): Datafile => ({
  schemaVersion: '2',
  revision,
  segments: {},
  features: {},
});

describe('the code defaults', () => {
  // The app as it ships since #826: Play is the player's groups under a Groups title, and Explore
  // is one datafile away and nothing without one.
  it('has Explore off', () => {
    expect(FEATURE_DEFAULTS.explore).toBe(false);
  });

  // One feature flag, and nothing left over from the ones #576 removed.
  it('gates Explore and nothing else', () => {
    expect(Object.keys(FEATURE_DEFAULTS)).toEqual(['explore']);
  });
});

describe('which datafiles this build reads', () => {
  it('reads schema version 2, the one Featurevisor 3 builds', () => {
    expect(isReadableSchemaVersion('2')).toBe(true);
  });

  // The flags repo moved a major without the app: installed apps keep what they had.
  it.each(['1', '3', '', '2.0'])('refuses %p', (version) => {
    expect(isReadableSchemaVersion(version)).toBe(false);
  });
});

describe('the fallback order', () => {
  it('prefers the datafile fetched this session', () => {
    expect(datafileInUse(datafile('fresh'), datafile('cached'))?.revision).toBe('fresh');
  });

  it('falls back to the one cached on the device', () => {
    expect(datafileInUse(undefined, datafile('cached'))?.revision).toBe('cached');
  });

  // Neither: the code defaults decide, which the caller reads as `undefined`.
  it.each([null, undefined])('has none when nothing was fetched and the cache is %p', (cached) => {
    expect(datafileInUse(undefined, cached)).toBeUndefined();
  });
});
