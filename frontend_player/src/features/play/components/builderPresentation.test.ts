/**
 * The two things this file says that no screen test can pin: **which heading a court shape
 * gets**, and **how a side is named when nobody is standing on it**.
 *
 * The rest of `builderPresentation` is asserted through `builder.test.tsx`, where the sentence
 * and the state that produced it are checked together. These two are here because one is a
 * recorded reversal and the other is a state the fixtures do not reach.
 */

import { SIDE_HEADINGS, forecastHeading, sideName } from './builderPresentation';

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
