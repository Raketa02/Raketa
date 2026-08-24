/**
 * The sentences on this screen that no rendered test can reach.
 *
 * Two of them are here for the reason `features/result` records: **the
 * prototype-key half of a failure table cannot be exercised end to end.** A
 * backend code spelled `toString` would have to survive `shared/errors/mapError.ts`
 * to reach one, and that module indexes its own `Record<string, …>` with the same
 * arbitrary string and **throws** on the way — so the write fails with a raw
 * `TypeError` carrying no code at all and this function is never asked
 * (`Raketa02/Raketa#121`). The guard is asserted here, on the function it lives in.
 */

import { AppError } from '@/shared/errors';

import { SEAT_GONE, SEAT_WRITE_FAILED, seatFailureLine } from './nowCopy';

function failedWith(code: string | undefined): AppError {
  return new AppError('conflict', 'business-conflict', 'diagnostic', { code });
}

describe('the one sentence this screen writes for itself', () => {
  it('is ADR-0062’s own line, word for word', () => {
    // Pinned to the literal rather than to the constant. The whole of this
    // sentence is its wording — *"a seat that is gone must never be presented as
    // an exceptional card"* is kept by what it says, so a suite comparing the
    // constant against itself would let the words be rewritten in silence.
    expect(SEAT_GONE).toBe('That seat has gone.');
  });

  it('never says she had a seat', () => {
    // She raced for it and was not fastest. *You lost your seat* describes
    // something else entirely, and would be the exceptional card arriving as a
    // sentence — a claim that something was hers, retracted.
    expect(SEAT_GONE).not.toMatch(/your seat|lost|reserved|yours/i);
  });
});

describe('what a tap on a seat says when it did not apply', () => {
  it('names the two refusals no card about this match could state', () => {
    // `ADR-0081`'s two structural limits on a serial claimant. One is a sentence
    // about a **different** match and the other is about a moment, and each
    // carries the thing to do about it rather than only what went wrong.
    expect(seatFailureLine(failedWith('match_player_already_claiming'))).toBe(
      'You are already buying a seat. Finish that one first.',
    );
    expect(seatFailureLine(failedWith('match_claim_cooling_down'))).toBe(
      'Give that seat a moment before trying again.',
    );
  });

  it('says the plain thing for a code this build has never heard of', () => {
    // Old app versions live on real phones for months, and the backend will add
    // codes this build has never seen. A failure with no sentence of its own is
    // not an occasion to invent one about a seat.
    expect(seatFailureLine(failedWith('match_seat_already_claimed'))).toBe(SEAT_WRITE_FAILED);
    expect(seatFailureLine(failedWith(undefined))).toBe(SEAT_WRITE_FAILED);
  });

  it('never resolves a code off Object.prototype', () => {
    // Without the own-property guard this returns `Object.prototype.toString` — a
    // function, handed to a `<Text>` as its child.
    expect(seatFailureLine(failedWith('toString'))).toBe(SEAT_WRITE_FAILED);
    expect(seatFailureLine(failedWith('constructor'))).toBe(SEAT_WRITE_FAILED);
    expect(seatFailureLine(failedWith('hasOwnProperty'))).toBe(SEAT_WRITE_FAILED);
  });

  it('says nothing that claims a seat was ever hers', () => {
    // The negative control the wording needs. *That seat has gone* is honest
    // because nothing before it claimed she had one — a failure line saying *you
    // lost your seat* would be the exceptional card, arriving as a sentence.
    for (const code of ['match_player_already_claiming', 'match_claim_cooling_down', undefined]) {
      expect(seatFailureLine(failedWith(code))).not.toMatch(/your seat|lost|reserved/i);
    }
  });
});
