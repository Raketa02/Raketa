/**
 * The two things this file says that no screen test can pin: **which heading a court shape
 * gets**, and **how a side is named when nobody is standing on it**.
 *
 * The rest of `builderPresentation` is asserted through `builder.test.tsx`, where the sentence
 * and the state that produced it are checked together. These two are here because one is a
 * recorded reversal and the other is a state the fixtures do not reach.
 */

import {
  SIDE_HEADINGS,
  USE_MATCHMAKING_LABEL,
  forecastHeading,
  searchFacts,
  sideName,
} from './builderPresentation';

describe('the forecast card’s heading', () => {
  /**
   * **A reversal, pinned.** The module note refused *Pairing forecast* / *Balance forecast*
   * while the card said one number; it says what that number is a split **between** now, and
   * neither word is the engine's name (`the-words.md` §20.3 is about *Match Fit*).
   */
  it('names what the card draws, once per court shape', () => {
    expect(forecastHeading(4)).toBe('Pairing forecast');
    expect(forecastHeading(2)).toBe('Balance forecast');
  });
});

describe('naming one half of the court', () => {
  it('joins whoever is standing on it', () => {
    expect(sideName(['You', 'piotr'], SIDE_HEADINGS.yours)).toBe('You + piotr');
    expect(sideName(['piotr'], SIDE_HEADINGS.yours)).toBe('piotr');
  });

  /**
   * A provisional court can have a whole half open, and an empty label over a strength the
   * engine did serve reads as a missing **number** rather than as a missing player.
   */
  it('falls back to which side it is when nobody is on it', () => {
    expect(sideName([], SIDE_HEADINGS.theirs)).toBe('Their side');
  });
});

/**
 * **The screen's name is the search's own three facts**, and it stopped having a second one.
 *
 * The h1 over this line said *Build the four* — which re-states the shape the line already
 * carries and adds a verb for the furniture — or *Complete the four* once anybody was seated.
 * Both are gone with the heading, so the words themselves are what is asserted here rather
 * than a constant that could be renamed under a passing test.
 */
describe('what the court is called', () => {
  it('prints the sport, the shape and the mode, in that order', () => {
    expect(searchFacts({ sportName: 'Padel', seats: 4, mode: 'FOR_FUN' })).toBe(
      'Padel · doubles · for fun',
    );
    expect(searchFacts({ sportName: 'Tennis', seats: 2, mode: 'COMPETITIVE' })).toBe(
      'Tennis · singles · competitive',
    );
  });

  it('says the shape once, and never as a verb', () => {
    // The line the removed h1 duplicated: *doubles* is in here, and *build*, *set up* and
    // *complete* are nowhere.
    for (const seats of [2, 4]) {
      const line = searchFacts({ sportName: 'Padel', seats, mode: 'FOR_FUN' });
      expect(line).not.toMatch(/build|set up|complete/i);
    }
  });
});

/**
 * ⚡'s label, which names the act rather than the machinery or the scope.
 *
 * It was a pair — *Let the engine fill the seats* and *Let the engine fill the rest* — and the
 * branch existed because the engine fills **around** `locked_seats`. Naming the act instead of
 * the scope is true of both courts, so there is one string and nothing left to correct.
 */
describe('the control that fills the court', () => {
  it('is one string, and names the thing the platform calls itself', () => {
    expect(USE_MATCHMAKING_LABEL).toBe('Use Matchmaking');
  });

  it('says nothing about how many seats are left, because it no longer has to', () => {
    expect(USE_MATCHMAKING_LABEL).not.toMatch(/seat|rest|engine/i);
  });
});
