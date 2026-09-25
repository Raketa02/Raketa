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
  // The app as it ships since #512: a first launch with no network gets Play › Groups.
  it('has Find a game off', () => {
    expect(FEATURE_DEFAULTS.find_a_game).toBe(false);
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
