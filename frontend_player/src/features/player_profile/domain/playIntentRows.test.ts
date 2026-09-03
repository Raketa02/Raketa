import { anySportUndeclared, playIntentRows } from './playIntentRows';

describe('the sports a player has declared in', () => {
  it('pairs each rated sport with what was answered for it, in the order they arrived', () => {
    expect(
      playIntentRows(['padel', 'tennis'], { padel: 'COMPETITIVE', tennis: 'NO_PREFERENCE' }),
    ).toEqual([
      { sport: 'padel', intent: 'COMPETITIVE' },
      { sport: 'tennis', intent: 'NO_PREFERENCE' },
    ]);
  });

  /**
   * Absence is *never asked* and never `NO_PREFERENCE` — the distinction ADR-0094 forbids a
   * null intent on the wire in order to keep.
   */
  it('keeps a rated sport with no answer as a row with no value', () => {
    expect(playIntentRows(['squash'], {})).toEqual([{ sport: 'squash', intent: undefined }]);
  });

  /** A rating is what makes a sport matchable, so an unrated one is not a question to ask. */
  it('says nothing about a sport the player is not rated in', () => {
    expect(playIntentRows(['padel'], { padel: 'FOR_FUN', tennis: 'FOR_FUN' })).toEqual([
      { sport: 'padel', intent: 'FOR_FUN' },
    ]);
  });

  it('answers whether anything is still unanswered', () => {
    expect(anySportUndeclared(playIntentRows(['padel'], { padel: 'FOR_FUN' }))).toBe(false);
    expect(anySportUndeclared(playIntentRows(['padel', 'squash'], { padel: 'FOR_FUN' }))).toBe(
      true,
    );
  });
});
