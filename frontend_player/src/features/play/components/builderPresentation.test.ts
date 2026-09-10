/**
 * The two things this file says that no screen test can pin: **which heading a court shape
 * gets**, and **how a side is named when nobody is standing on it**.
 *
 * The rest of `builderPresentation` is asserted through `builder.test.tsx`, where the sentence
 * and the state that produced it are checked together. These two are here because one is a
 * recorded reversal and the other is a state the fixtures do not reach.
 */

import { courtEntryTitle } from './findAGamePresentation';

import {
  SIDE_HEADINGS,
  USE_MATCHMAKING_LABEL,
  builderTitle,
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
 * **The court's name, and the control that opens it, are one string.**
 *
 * `builderTitle` is the screen's; `courtEntryTitle` reads it, because the control names the
 * screen it opens. Asserted as words rather than through the constant, so a reword has to
 * come here and be read.
 */
describe('what the court is called', () => {
  it('names the game the sport plays, in the sport’s own two words', () => {
    expect(builderTitle(4)).toBe('Build a doubles');
    expect(builderTitle(2)).toBe('Build a singles');
  });

  it('is what the control on Find a game promises, so the press keeps its word', () => {
    for (const seats of [2, 4]) expect(courtEntryTitle(seats)).toBe(builderTitle(seats));
  });

  it('says nothing about how full the court is', () => {
    // *Complete the four* named the state of the court, which is the one thing on the screen
    // a player can already see — and it moved the heading under them as they filled seats.
    for (const seats of [2, 4]) expect(builderTitle(seats)).not.toMatch(/complete/i);
  });
});

/**
 * The three facts, drawn as the **eyebrow** on the court and on the pool.
 *
 * They were promoted to the title on both for a day, which left two screens under one heading
 * — the search named on both and the screen on neither.
 */
describe('the line above it', () => {
  it('prints the sport, the shape and the mode, in that order', () => {
    expect(searchFacts({ sportName: 'Padel', seats: 4, mode: 'FOR_FUN' })).toBe(
      'Padel · doubles · for fun',
    );
    expect(searchFacts({ sportName: 'Tennis', seats: 2, mode: 'COMPETITIVE' })).toBe(
      'Tennis · singles · competitive',
    );
  });

  it('states the shape and never acts on it, which is what keeps it an eyebrow', () => {
    // A region label, not a control's name: the verb belongs to the title above the court and
    // to the button on Find a game, and this line only says what was searched for.
    for (const seats of [2, 4]) {
      const line = searchFacts({ sportName: 'Padel', seats, mode: 'FOR_FUN' });
      expect(line).not.toMatch(/build|set up|complete|pick/i);
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
