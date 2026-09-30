import { readDatafile } from './datafileSchema';

/** A datafile as the flags repo's CLI 3.11.0 builds it for `local` today. */
const BUILT = {
  schemaVersion: '2',
  featurevisorVersion: '3.11.0',
  revision: '1',
  segments: {},
  features: {
    classic_play: {
      bucketBy: 'playerId',
      traffic: [{ key: 'everyone', segments: '*', percentage: 100000 }],
    },
  },
  variables: {},
};

describe('a datafile the app can read', () => {
  it('is accepted whole, including what the envelope does not name', () => {
    const read = readDatafile(BUILT);

    expect(read).toEqual({ readable: true, datafile: BUILT });
  });
});

describe('a datafile the app refuses', () => {
  // ADR-0180 §10: an upgrade in the flags repo stops installed apps from updating, never from
  // working — so the format this build does not know is refused, by name.
  it('refuses a schema version this build does not read', () => {
    expect(readDatafile({ ...BUILT, schemaVersion: '3' })).toEqual({
      readable: false,
      reason: 'unknown-schema-version',
    });
  });

  it.each([
    ['no features', { ...BUILT, features: undefined }],
    ['no revision', { ...BUILT, revision: undefined }],
    ['no schema version', { ...BUILT, schemaVersion: undefined }],
    ['features as a list', { ...BUILT, features: [] }],
    ['a string', 'Not Found'],
    ['nothing', undefined],
  ])('refuses one with %s as malformed', (_label, raw) => {
    expect(readDatafile(raw)).toEqual({ readable: false, reason: 'malformed' });
  });
});
