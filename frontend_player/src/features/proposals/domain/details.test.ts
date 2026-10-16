import type { DeckPerson } from './deck';
import {
  completesTheGame,
  courtOfDetails,
  detailsCanRunOut,
  paymentDueOf,
  yesOnDetails,
  type ProposalDetails,
} from './details';

const person = (playerId: string, extra: Partial<DeckPerson> = {}): DeckPerson => ({
  playerId,
  isYou: false,
  isIn: false,
  ...extra,
});

function details(extra: Partial<ProposalDetails> = {}): ProposalDetails {
  return {
    proposalId: 'p-1',
    groupId: 'group-1',
    type: 'PICKED_FOR_YOU',
    kind: 'competitive',
    sport: 'padel',
    readAt: '2026-09-30T08:00:00Z',
    status: 'FILLING',
    actions: ['YES', 'NO'],
    inCount: 2,
    seats: 4,
    startsAt: '2026-10-03T14:00:00Z',
    where: { id: 'club-1', name: 'Bonarka Arena', distanceKm: 3.1 },
    shareGrosze: 3200,
    deadline: '2026-10-02T11:00:00Z',
    noFreeCancellation: false,
    sides: {
      yours: [person('me', { isYou: true }), person('zofia', { isIn: true })],
      theirs: [person('ania', { isIn: true }), person('ewa')],
    },
    overlap: { grade: 'GOOD', cells: [], game: { day: 6, range: 'AFTERNOON' } },
    ...extra,
  };
}

describe('courtOfDetails — what a yes from the details does (the deck’s own rule)', () => {
  it('is a free vote while the game is short of more than your yes', () => {
    expect(courtOfDetails(details({ inCount: 2 }))).toBe('COURT_AVAILABLE');
  });

  it('books it now when your yes is the last seat', () => {
    expect(courtOfDetails(details({ inCount: 3 }))).toBe('BOOK_IT_NOW');
  });

  it('is nothing to book for a reader already In, whose yes is said', () => {
    const youIn = details({
      inCount: 3,
      sides: {
        yours: [person('me', { isYou: true, isIn: true }), person('zofia', { isIn: true })],
        theirs: [person('ania', { isIn: true })],
      },
    });
    expect(courtOfDetails(youIn)).toBe('COURT_AVAILABLE');
    expect(completesTheGame(youIn)).toBe(false);
  });
});

describe('completesTheGame — You complete it', () => {
  it('says so only when your yes would leave no seat open', () => {
    expect(completesTheGame(details({ inCount: 3 }))).toBe(true);
    expect(completesTheGame(details({ inCount: 2 }))).toBe(false);
  });
});

describe('yesOnDetails — what the fill holds for a yes said here', () => {
  it('carries the id, the card’s type, the court and the sides', () => {
    const shown = details({ inCount: 3 });
    expect(yesOnDetails(shown)).toEqual({
      proposalId: 'p-1',
      type: 'PICKED_FOR_YOU',
      court: 'BOOK_IT_NOW',
      sides: shown.sides,
    });
  });
});

/** Tuesday 6 October, 14:10 in Warsaw — the read; the time to pay runs to 14:40 (#625). */
const READ = Date.parse('2026-10-06T12:10:00Z');
const TWENTY_TO_THREE = '2026-10-06T12:40:00Z';
const yours = {
  seatChargeId: 's-1',
  refusal: 'AUTHENTICATION_REQUIRED',
  confirmBy: TWENTY_TO_THREE,
} as const;

describe('paymentDueOf — the times to pay the money row names (Q111)', () => {
  it('is the payment the game waits for, and the reader’s own, while each is ahead', () => {
    const waiting = details({
      status: 'WAITING_FOR_A_PAYMENT',
      paymentDueBy: TWENTY_TO_THREE,
      yourPayment: yours,
    });
    expect(paymentDueOf(waiting, READ)).toEqual({
      dueBy: { at: TWENTY_TO_THREE, today: true },
      yours: { by: { at: TWENTY_TO_THREE, today: true }, window: 'UNNAMED' },
    });
    expect(paymentDueOf(waiting, Date.parse(TWENTY_TO_THREE))).toEqual({});
  });

  it('says what the reader’s own time is for, while it runs — to fix the card (#638; Q113)', () => {
    const fixing = details({
      status: 'WAITING_FOR_A_PAYMENT',
      yourPayment: { ...yours, timeTo: 'FIX_THE_CARD' },
    });
    expect(paymentDueOf(fixing, READ)).toEqual({
      yours: { by: { at: TWENTY_TO_THREE, today: true }, window: 'FIX_THE_CARD' },
    });
    expect(paymentDueOf(fixing, Date.parse(TWENTY_TO_THREE))).toEqual({});
  });

  it('is nothing where no time is given — a refused share whose time ran out included', () => {
    expect(paymentDueOf(details(), READ)).toEqual({});
    expect(
      paymentDueOf(
        details({ yourPayment: { seatChargeId: 's-1', refusal: 'AUTHENTICATION_REQUIRED' } }),
        READ,
      ),
    ).toEqual({});
  });
});

describe('detailsCanRunOut — a deadline the money row names that leaves by itself', () => {
  it('runs while a time to pay, or the reader’s own time, is there to pass', () => {
    expect(detailsCanRunOut(details())).toBe(false);
    expect(detailsCanRunOut(details({ paymentDueBy: TWENTY_TO_THREE }))).toBe(true);
    expect(detailsCanRunOut(details({ yourPayment: yours }))).toBe(true);
  });
});
