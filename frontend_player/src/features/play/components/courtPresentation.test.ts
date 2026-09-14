/**
 * An empty seat, and who the answer was for.
 *
 * **`NO_SHARED_SLOTS` is a dock and not a refusal** — nobody is removed from the court for it,
 * and the sentence must not read as though somebody were. **The withheld seat states the fact
 * and never the cause.** And **`GROUP` is said and `SEARCHER` is not**, because a sentence
 * under every court would make the exception unreadable.
 *
 * `GroupReason` no longer has sentences to assert. The five lines were drawn in a row of their
 * own under the forecast card's names, and the row is gone — so the copy is gone with it
 * rather than living on as a table nothing renders (`courtPresentation`'s module note).
 */

import { OPTIMISED_FOR, UNFILLED_REASONS } from '../domain/vocabulary';

import { WITHHELD_SEAT_LINE, optimisedForLine, unfilledSeatLine } from './courtPresentation';

describe('an unfilled seat', () => {
  it('gives each obstacle its own sentence', () => {
    const lines = UNFILLED_REASONS.map(unfilledSeatLine);

    expect(new Set(lines).size).toBe(UNFILLED_REASONS.length);
  });

  it('states the shortfall rather than a count of who was found', () => {
    // #223 replaced AC-69's "Only found N" with the actual obstacle for the actual seat.
    for (const line of UNFILLED_REASONS.map(unfilledSeatLine)) {
      expect(line).not.toMatch(/^Only found/);
    }
  });

  it('reads a shared-slot zero as a bend, never as a removal', () => {
    const line = unfilledSeatLine('NO_SHARED_SLOTS');

    expect(line).toMatch(/bend/);
    expect(line).not.toMatch(/cannot|can't|unavailable|removed/i);
  });
});

describe('a seat whose player is no longer available', () => {
  it('states the fact and never the cause', () => {
    // Four fail-closed gates reach this mark — a block either way, a hold, an account that
    // may not be shown, and the mutual gender preference — and naming which one fired would
    // tell a searcher that a particular person blocked them or changed a safety setting.
    const said = WITHHELD_SEAT_LINE.toLowerCase();

    for (const cause of ['block', 'hold', 'suspend', 'preference', 'gender']) {
      expect(said).not.toContain(cause);
    }
  });

  it('says something changed rather than something about them', () => {
    // The register the send refusal is held to: the fact is that the line-up went out of
    // date, and a person's standing is not the organiser's to be told.
    expect(WITHHELD_SEAT_LINE).toMatch(/^Something's changed/);
  });

  it('is not a sentence about an unfilled seat — the seat is filled, by somebody', () => {
    expect(UNFILLED_REASONS.map(unfilledSeatLine)).not.toContain(WITHHELD_SEAT_LINE);
  });
});

/**
 * **Whom the answer was optimised for**, and the one value that says nothing.
 *
 * `GROUP` is the consequence of an act the player took — hand-seating somebody — said before
 * they discover it. `SEARCHER` is the ordinary case, and a sentence under every court is what
 * would make the exception unreadable.
 */
describe('whom the answer was optimised for', () => {
  it('says nothing about an answer optimised for the searcher', () => {
    expect(optimisedForLine('SEARCHER')).toBeUndefined();
  });

  it('says nothing about a code this build has never seen', () => {
    // §3's drop: the sentence is an extra caveat over an answer rather than a row in a total,
    // so an absent one leaves nothing on screen unaccounted for. Claiming *optimised for you*
    // about an answer this build cannot read would be the alternative.
    expect(optimisedForLine(null)).toBeUndefined();
  });

  it('says what a hand-seated court cost, in the voice a provisional figure uses', () => {
    const line = optimisedForLine('GROUP');

    expect(line).toBeDefined();
    // It states the trade rather than apologising for it, and it names no number: the group
    // objective is recorded and never returned.
    expect(line).toMatch(/four of you/);
    expect(line).not.toMatch(/\d/);
  });

  it('gives every value a decision, so a third cannot ship without one', () => {
    for (const optimised of OPTIMISED_FOR) {
      expect(() => optimisedForLine(optimised)).not.toThrow();
    }
  });

  /**
   * The engine answers `GROUP` for any locked seat, and on a challenge's fill the locked
   * seats are the people who said yes — nobody the organiser picked, and no trade the engine
   * made around them. So the fill says nothing, whatever the envelope says.
   */
  it('says nothing on a fill that is completing a challenge, whatever the envelope says', () => {
    for (const optimised of [...OPTIMISED_FOR, null]) {
      expect(optimisedForLine(optimised, true)).toBeUndefined();
    }
    expect(optimisedForLine('GROUP', false)).toBeDefined();
  });
});
