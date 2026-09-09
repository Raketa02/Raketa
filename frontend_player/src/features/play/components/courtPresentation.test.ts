/**
 * An empty seat, and why this four.
 *
 * Two rules are asserted. **`NO_SHARED_SLOTS` is a dock and not a refusal** — nobody is
 * removed from the court for it, and the sentence must not read as though somebody were. And
 * **no group reason quotes a figure**: `G` is recorded and never returned, so these five
 * sentences are the whole explanation and a number in one would be invented.
 */

import { seatLock, type BuildSeat, type SeatGuard, type SpokenSeatGuard } from '../domain/lineup';
import { GROUP_REASONS, OPTIMISED_FOR, UNFILLED_REASONS } from '../domain/vocabulary';

import { SWAP_TOGGLE_LABEL } from './accessibilityPresentation';
import {
  WITHHELD_SEAT_LINE,
  groupReasonLine,
  optimisedForLine,
  seatGuardLine,
  unfilledSeatLine,
} from './courtPresentation';

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

describe('why this four', () => {
  it('gives each reason that has a sentence its own', () => {
    const lines = GROUP_REASONS.map(groupReasonLine).filter((line) => line !== undefined);

    expect(new Set(lines).size).toBe(lines.length);
  });

  it('says nothing at all for the two that grade the answer', () => {
    // The card above them prints two side strengths, the gap and the evenness percentage.
    // *Nobody is out of their depth* and *the best all-round fit* are both claims about how
    // good this four is, under four figures saying exactly that — the card arguing for its
    // answer rather than reporting it. The three that remain name a choice the engine made,
    // which no figure carries.
    expect(groupReasonLine('STRONGEST_WEAKEST_SEAT')).toBeUndefined();
    expect(groupReasonLine('BEST_AVERAGE_FIT')).toBeUndefined();
  });

  it('quotes no figure, because the objective is recorded and never returned', () => {
    for (const line of GROUP_REASONS.map(groupReasonLine)) expect(line ?? '').not.toMatch(/\d/);
  });

  it('gives the two group rapport terms one sentence', () => {
    // The code is the vocabulary: splitting it in copy would publish a distinction the enum
    // deliberately does not carry.
    expect(groupReasonLine('GROUP_RAPPORT')).toBe('These four read each other well');
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

describe('a refused tap on a seat', () => {
  const SPOKEN: readonly SpokenSeatGuard[] = ['SEAT_IS_YOURS'];

  it('has a sentence for the lock that speaks, and silence for the one that does not', () => {
    // `seatLock` returns exactly these codes, so a third lock added there fails the compiler at
    // the table. Two of them lock a seat and only one of them says so: ADR-0150 §8 makes an
    // accepted seat *not a control*, so the sentence it used to have — `{Name} already accepted
    // — they keep their place` — is gone rather than unreachable.
    const locks: readonly (SeatGuard | undefined)[] = (
      [
        { kind: 'you' },
        { kind: 'player', accepted: true },
        { kind: 'player', accepted: false },
        { kind: 'empty' },
      ] satisfies readonly BuildSeat[]
    ).map(seatLock);

    expect(locks).toEqual(['SEAT_IS_YOURS', 'ALREADY_ACCEPTED', undefined, undefined]);
    expect(new Set(SPOKEN.map(seatGuardLine)).size).toBe(SPOKEN.length);
  });

  it('names the way out rather than only saying no', () => {
    // A refusal that only refuses is a control a player presses twice. Your own seat is
    // refused BECAUSE swap mode is where sides change, so the sentence names that toggle —
    // through the switch's own label, so the screen cannot start referring to a control that
    // is not on it.
    expect(seatGuardLine('SEAT_IS_YOURS')).toContain(SWAP_TOGGLE_LABEL);
  });

  it('quotes nobody, because the one refusal left is about your own seat', () => {
    // *You already accepted* is not a thing to be told, and the handle the table used to take
    // went with the sentence that named somebody else's seat.
    expect(seatGuardLine('SEAT_IS_YOURS')).not.toContain('You already');
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
});
