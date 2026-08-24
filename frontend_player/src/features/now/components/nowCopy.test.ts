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

import {
  DEBT_CONSEQUENCE,
  DEBT_STILL_OPEN,
  SEAT_GONE,
  SEAT_WRITE_FAILED,
  STANDBY_LEAVE_FAILED,
  debtSentences,
  seatFailureLine,
} from './nowCopy';

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

describe('what a tap on leave standby says when it did not go through', () => {
  it('names what is still true, and not only what went wrong', () => {
    // Nothing can refuse this act (`ADR-0087`), so a failure is a tap that never
    // reached the server — and the card is still on her strip saying she is queued.
    // What she needs to know is whether that card is right, which it is.
    expect(STANDBY_LEAVE_FAILED).toBe('That did not go through — you are still on standby.');
  });

  it('is not the seat write’s sentence', () => {
    // Pinned apart rather than shared. The seat's line says *nothing has changed*
    // about a race she lost; this one says *you are still queued*, which is the
    // opposite kind of news and the only thing a card that stayed put leaves in
    // doubt.
    expect(STANDBY_LEAVE_FAILED).not.toBe(SEAT_WRITE_FAILED);
  });
});

describe('the one line on Now that is about the player', () => {
  const owing = { amount: 11200, currency: 'PLN' } as const;
  /** U+00A0, as `money.test.ts` spells it: a price never wraps mid-number. */
  const NBSP = '\u00a0';
  const OWED = `You owe 112,00${NBSP}zł.`;

  it('names the amount, in this app’s one money rendering', () => {
    // `112,00 zł` — comma decimal, non-breaking space, and never `Intl` or
    // `toFixed`. The sentence is the client's (`ADR-0041`); the characters are the
    // repo-wide table's, through the one formatter.
    expect(debtSentences({ owed: owing, blocked: true })[0]).toBe(OWED);
  });

  it('states the two acts she cannot take, in the words of the boolean', () => {
    // `ADR-0070` compresses them into one flag *"meaning this player may not create
    // a match or book a court"*, and the sentence is that meaning written out. It
    // is pinned to the literal rather than to the constant: a suite comparing a
    // constant against itself would let the two acts be rewritten in silence.
    expect(DEBT_CONSEQUENCE).toBe('Until it is settled you cannot create a match or book a court.');
  });

  it('says in the same breath what being cut off does not cost her', () => {
    // `Raketa02/Raketa#92`: *"she can still pay for a seat in someone else's match:
    // being cut off must not make her less likely to pay."* The screen enforces
    // that by withholding nothing; this is the half that says so out loud.
    expect(DEBT_STILL_OPEN).toBe('You can still take a seat in someone else’s match.');
    expect(debtSentences({ owed: owing, blocked: true })).toEqual([
      OWED,
      DEBT_CONSEQUENCE,
      DEBT_STILL_OPEN,
    ]);
  });

  it('claims no consequence for a debt the server says blocks nothing', () => {
    // The negative control, and the reason the boolean exists at all. A debt she is
    // not blocked by is still money she owes and is still worth a line — but a
    // client that printed the consequence anyway would be deriving it from the
    // amount, which is the rule `ADR-0053` leaves the phone none of.
    const said = debtSentences({ owed: owing, blocked: false });

    expect(said).toEqual([OWED]);
    expect(said.join(' ')).not.toMatch(/cannot|create|book/i);
  });
});
