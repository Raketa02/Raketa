import { DEFAULT_PLAY_SEGMENT, playSegmentFrom } from './playSegment';

describe('the Play segment a saved value opens on', () => {
  it('is Groups when nothing was saved', () => {
    expect(playSegmentFrom(undefined)).toBe('groups');
  });

  it('is the segment that was saved', () => {
    expect(playSegmentFrom('explore')).toBe('explore');
    expect(playSegmentFrom('groups')).toBe('groups');
  });

  // ADR-0188 §4: stale or unrecognised is the default, never an error.
  it('is Groups for anything this build does not know', () => {
    expect(playSegmentFrom('find-a-game')).toBe('groups');
    expect(playSegmentFrom('')).toBe('groups');
    expect(playSegmentFrom('Explore')).toBe('groups');
  });

  it('defaults to Groups', () => {
    expect(DEFAULT_PLAY_SEGMENT).toBe('groups');
  });
});
