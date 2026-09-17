import {
  NOT_DECLARED,
  NOT_DECLARED_LINE,
  declaredValue,
  playIntentRowLabel,
} from './playIntentsPresentation';

describe('what the You tab says about a declaration', () => {
  // The section's heading and body — *What other players see*, *it does not change what you
  // can search for* — retired with ADR-0179 §9: the *What kind of game* screen says the one
  // thing they said in one line under its title, asserted in `youProfilePresentation.test.ts`.

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
