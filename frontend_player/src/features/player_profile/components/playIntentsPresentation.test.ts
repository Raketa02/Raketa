import {
  NOT_DECLARED,
  NOT_DECLARED_LINE,
  declaredValue,
  intentCostLine,
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

/** The words §27's rows marked *(ADR-0201)*: the panel's lines, counted across the groups. */
describe('what an answer on You costs', () => {
  it('says how many cards of the kind that goes go, across the groups', () => {
    expect(intentCostLine({ change: 'drops', kind: 'competitive', count: 7 })).toBe(
      'Your 7 competitive cards in your groups go. Games you’re In on stay.',
    );
    expect(intentCostLine({ change: 'drops', kind: 'forFun', count: 3 })).toBe(
      'Your 3 for-fun cards in your groups go. Games you’re In on stay.',
    );
  });

  it('says one card goes', () => {
    expect(intentCostLine({ change: 'drops', kind: 'forFun', count: 1 })).toBe(
      'Your 1 for-fun card in your groups goes. Games you’re In on stay.',
    );
  });

  /** PRD #736, call 4: a zero drops the number rather than saying *your 0 cards*. */
  it('says Rakieta stops dealing the kind when none of its cards is held', () => {
    expect(intentCostLine({ change: 'drops', kind: 'competitive', count: 0 })).toBe(
      'Rakieta stops dealing you competitive games. Games you’re In on stay.',
    );
  });

  /** A count not in hand is not zero: the line keeps its shape and loses only the number. */
  it('says the cards go without a number while the count is not in hand', () => {
    expect(intentCostLine({ change: 'drops', kind: 'competitive', count: undefined })).toBe(
      'Your competitive cards in your groups go. Games you’re In on stay.',
    );
  });

  it('says the kind played is kept and the other added, with no count', () => {
    expect(intentCostLine({ change: 'widens', keeps: 'competitive', gets: 'forFun' })).toBe(
      'Keep your competitive cards and get for-fun ones too.',
    );
    expect(intentCostLine({ change: 'widens', keeps: 'forFun', gets: 'competitive' })).toBe(
      'Keep your for-fun cards and get competitive ones too.',
    );
  });
});
