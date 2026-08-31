import { findAGameStanding, sportOnScreen } from './findAGame';

describe('the sport the screen is on', () => {
  it('is the one the player chose', () => {
    expect(sportOnScreen(['padel', 'tennis'], 'tennis')).toBe('tennis');
  });

  it('falls back to the first rated sport when nothing has been chosen', () => {
    expect(sportOnScreen(['padel', 'tennis'], undefined)).toBe('padel');
  });

  // A process-scoped choice outlives the read that justified it, so this is repair rather
  // than a default: a chip row with nothing selected has no sport to search for.
  it('repairs a choice the player is no longer rated in', () => {
    expect(sportOnScreen(['padel'], 'squash')).toBe('padel');
  });

  it('is nobody at all when the player is rated in nothing', () => {
    expect(sportOnScreen([], 'padel')).toBeUndefined();
  });
});

describe('what stands between the player and a search', () => {
  it('is nothing, once the sport is rated and declared in', () => {
    expect(findAGameStanding(['padel'], 'padel', { padel: 'FOR_FUN' })).toEqual({
      kind: 'searchable',
      sport: 'padel',
    });
  });

  // The set difference ADR-0021 licenses: rated, and absent from the declaration map.
  it('is the declaration, where the sport is rated and absent from the map', () => {
    expect(findAGameStanding(['padel', 'tennis'], 'tennis', { padel: 'COMPETITIVE' })).toEqual({
      kind: 'undeclared',
      sport: 'tennis',
    });
  });

  // NO_PREFERENCE is an explicit answer and never an absence — the interstitial must close.
  it('treats NO_PREFERENCE as declared', () => {
    expect(findAGameStanding(['padel'], 'padel', { padel: 'NO_PREFERENCE' })).toEqual({
      kind: 'searchable',
      sport: 'padel',
    });
  });

  it('is the rating itself, where the player has none', () => {
    expect(findAGameStanding([], undefined, {})).toEqual({ kind: 'no-rated-sport' });
  });
});
