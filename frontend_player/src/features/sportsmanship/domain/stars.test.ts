/**
 * The scale, the draft, and the three things a card must not be able to send.
 *
 * Two of the ticket's acceptance criteria are unrepresentable rather than validated, and this
 * suite is where that claim is made: **stars are whole, one to five** — there is no zero and
 * there are no halves — and **one card carries one answer about each player**, which the
 * backend refuses by name and a `Record` keyed by a player id cannot express. The third is the
 * blank: leaving somebody out is an absence and never a value.
 */

import { NOTHING_SAID, isStars, pressed, starsFor, starsGiven, type StarsDraft } from './stars';

const KASIA = 'aaaaaaaa-0000-4000-8000-000000000001';
const TOMEK = 'bbbbbbbb-0000-4000-8000-000000000002';
const MAREK = 'cccccccc-0000-4000-8000-000000000003';

/** The card's own order, which is the line-up's. */
const COURT = [KASIA, TOMEK, MAREK] as const;

describe('the scale', () => {
  it('is one to five whole stars, and there is no zero', () => {
    expect([1, 2, 3, 4, 5].every(isStars)).toBe(true);
    expect(isStars(0)).toBe(false);
  });

  it('has no halves and nothing off the end of it', () => {
    expect(isStars(2.5)).toBe(false);
    expect(isStars(6)).toBe(false);
    expect(isStars(-1)).toBe(false);
  });
});

describe('the draft', () => {
  it('starts with nobody rated, which is not everybody rated nought', () => {
    expect(starsFor(NOTHING_SAID, KASIA)).toBeUndefined();
    expect(starsGiven(NOTHING_SAID, COURT)).toEqual([]);
  });

  it('takes one answer per person, whatever order they are answered in', () => {
    const draft = pressed(pressed(NOTHING_SAID, TOMEK, 4), KASIA, 2);

    expect(starsFor(draft, KASIA)).toBe(2);
    expect(starsFor(draft, TOMEK)).toBe(4);
    expect(starsFor(draft, MAREK)).toBeUndefined();
  });

  it('replaces an answer rather than adding to it, so one card says one thing about one person', () => {
    const draft = pressed(pressed(NOTHING_SAID, KASIA, 2), KASIA, 5);

    expect(starsGiven(draft, COURT)).toEqual([{ playerId: KASIA, stars: 5 }]);
  });

  /**
   * The one gesture that makes a mis-tap survivable. Submitting is final and there is no
   * correction path, so a row that could only ever go up would force an opinion out of a
   * finger that slipped — which is the opposite of *leave anybody blank*.
   */
  it('clears the row when the star that already stands is pressed again', () => {
    const draft = pressed(pressed(NOTHING_SAID, KASIA, 3), KASIA, 3);

    expect(starsFor(draft, KASIA)).toBeUndefined();
  });

  it('does not clear when a different star is pressed', () => {
    const draft = pressed(pressed(NOTHING_SAID, KASIA, 3), KASIA, 1);

    expect(starsFor(draft, KASIA)).toBe(1);
  });

  it('ignores a press off the scale rather than storing one', () => {
    // Unreachable from the row, which draws exactly five. It is refused here because the
    // scale is a rule about answers and not about a drawing: `stars_are_one_to_five` is a
    // refusal this client should never be able to earn.
    expect(starsFor(pressed(NOTHING_SAID, KASIA, 0), KASIA)).toBeUndefined();
    expect(starsFor(pressed(NOTHING_SAID, KASIA, 6), KASIA)).toBeUndefined();
  });
});

describe('what a card sends', () => {
  it('sends the rated in the court’s own order and leaves the rest out', () => {
    const draft = pressed(pressed(NOTHING_SAID, MAREK, 5), KASIA, 3);

    expect(starsGiven(draft, COURT)).toEqual([
      { playerId: KASIA, stars: 3 },
      { playerId: MAREK, stars: 5 },
    ]);
  });

  /**
   * `they_were_not_on_this_court` is a 400 the backend spells *including yourself*. A draft
   * that outlived the card it was typed on cannot produce one, because the court is what the
   * answer is read against rather than what it is checked against afterwards.
   */
  it('never sends stars for somebody who is not on this card', () => {
    const stranger = 'dddddddd-0000-4000-8000-000000000004';
    const draft: StarsDraft = pressed(pressed(NOTHING_SAID, stranger, 1), KASIA, 4);

    expect(starsGiven(draft, COURT)).toEqual([{ playerId: KASIA, stars: 4 }]);
  });

  it('sends an empty list when nobody was rated, which is an answer and closes the card', () => {
    expect(starsGiven(NOTHING_SAID, COURT)).toEqual([]);
  });
});
