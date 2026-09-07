import {
  NOT_DECLARED,
  NOT_DECLARED_LINE,
  PLAY_INTENTS_BODY,
  PLAY_INTENTS_HEADING,
  declaredValue,
  playIntentRowLabel,
} from './playIntentsPresentation';

describe('what the You tab says about a declaration', () => {
  /**
   * The heading names **who reads it**, because that is the fact that makes the list worth
   * having and the one a player cannot get from the value.
   */
  it('says who the answer is for, and what it is not', () => {
    expect(PLAY_INTENTS_HEADING).toBe('What other players see');
    // The confusion this section and the standing line both exist for, said once here.
    expect(PLAY_INTENTS_BODY).toContain('does not change what you can search for');
  });

  it('gives a rated sport with no answer a word rather than a blank', () => {
    expect(declaredValue(undefined)).toBe(NOT_DECLARED);
    expect(declaredValue('NO_PREFERENCE')).toBe('Either suits me');
  });

  /**
   * *Not set* is the discovery and this is the consequence: every matchmaking route refuses a
   * sport with no declaration, and a gap nobody explained is not a problem anybody can act on.
   */
  it('says what an unanswered sport costs', () => {
    expect(NOT_DECLARED_LINE).toContain('cannot be searched in');
  });

  /** A row is one element, or a sport is read a screen apart from the value it names. */
  it('names a row by the sport and its answer together', () => {
    expect(playIntentRowLabel('Padel', 'COMPETITIVE')).toBe('Padel, Competitive');
    expect(playIntentRowLabel('Squash', undefined)).toBe('Squash, Not set');
  });
});
