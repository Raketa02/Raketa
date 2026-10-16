/**
 * The rules of the moment a yes may fill a game — which yes waits ten seconds behind *Undo*, how
 * long it has left, what the server's answer to it means, and who *It's a game!* draws.
 */

import type { DeckCard, DeckPerson } from './deck';
import {
  UNDO_WINDOW_MS,
  aPaymentAwaited,
  confirmationOf,
  fillOutcome,
  fillRefusal,
  itsAGamePicture,
  paymentToConfirmOn,
  seatAtStake,
  undoSecondsLeft,
  waitsForUndo,
  yesOnRescue,
  type YesAnswer,
  type YourPayment,
} from './fill';

function person(name: string, extra: Partial<DeckPerson> = {}): DeckPerson {
  return { playerId: `id-${name}`, isYou: false, name, isIn: false, ...extra };
}

const YOU = person('You', { isYou: true });

function card(extra: Partial<DeckCard> = {}): DeckCard {
  return {
    proposalId: 'p-1',
    type: 'PICKED_FOR_YOU',
    kind: 'competitive',
    startsAt: '2026-10-03T14:00:00Z',
    club: { id: 'c-1', name: 'Bonarka Arena' },
    shareGrosze: 3200,
    deadline: '2026-10-02T08:00:00Z',
    inCount: 0,
    versionCount: 1,
    openSeatsAfterYourYes: 3,
    court: 'COURT_AVAILABLE',
    noFreeCancellation: false,
    sides: { yours: [YOU, person('Zofia')], theirs: [person('Ania'), person('Ewa')] },
    overlap: { grade: 'SLIM', cells: [], game: { day: 6, range: 'AFTERNOON' } },
    ...extra,
  };
}

function answer(extra: Partial<YesAnswer> = {}): YesAnswer {
  return {
    proposalId: 'p-1',
    openSeats: 2,
    booked: null,
    yourPayment: null,
    ...extra,
  };
}

describe('waitsForUndo — the yes that moves money waits ten seconds (the mechanics §6.5)', () => {
  it('holds a yes on Book it now', () => {
    expect(waitsForUndo(card({ court: 'BOOK_IT_NOW', openSeatsAfterYourYes: 0 }))).toBe(true);
  });

  it('holds every rescue join, not only the last seat (Q74)', () => {
    expect(waitsForUndo(card({ type: 'SEAT_OPEN', openSeatsAfterYourYes: 1 }))).toBe(true);
  });

  it('sends a free vote at once', () => {
    expect(waitsForUndo(card())).toBe(false);
    expect(waitsForUndo(card({ type: 'CHALLENGE' }))).toBe(false);
  });
});

describe('undoSecondsLeft — the toast’s count', () => {
  const started = Date.parse('2026-09-30T08:00:00Z');
  const endsAt = started + UNDO_WINDOW_MS;

  it('is ten at the start, and the window is ten seconds', () => {
    expect(UNDO_WINDOW_MS).toBe(10_000);
    expect(undoSecondsLeft(endsAt, started)).toBe(10);
  });

  it('rounds up, so the toast never says nought while there is time left', () => {
    expect(undoSecondsLeft(endsAt, started + 9_001)).toBe(1);
    expect(undoSecondsLeft(endsAt, started + 1)).toBe(10);
    expect(undoSecondsLeft(endsAt, started + 1_000)).toBe(9);
  });

  it('is nought at the end and after it', () => {
    expect(undoSecondsLeft(endsAt, endsAt)).toBe(0);
    expect(undoSecondsLeft(endsAt, endsAt + 5_000)).toBe(0);
  });
});

describe('fillOutcome — what a yes did, read off the server’s answer', () => {
  it('is It’s a game! when the yes booked the game', () => {
    expect(
      fillOutcome(answer({ openSeats: 0, booked: { bookingId: 'p-1', gameId: 'g-1' } })),
    ).toEqual({ kind: 'booked', bookingId: 'p-1' });
  });

  it('is a payment to confirm when this player’s share could not be held', () => {
    expect(
      fillOutcome(
        answer({
          openSeats: 1,
          yourPayment: { seatChargeId: 's-1', refusal: 'AUTHENTICATION_REQUIRED' },
        }),
      ),
    ).toEqual({ kind: 'confirm', seatChargeId: 's-1' });
    expect(
      fillOutcome(answer({ yourPayment: { seatChargeId: 's-2', refusal: 'DECLINED' } })),
    ).toEqual({ kind: 'confirm', seatChargeId: 's-2' });
  });

  it('asks for a method when the player has none at the fill, and the terms when the card changed brand', () => {
    expect(
      fillOutcome(answer({ yourPayment: { seatChargeId: 's-1', refusal: 'NO_METHOD' } })),
    ).toEqual({ kind: 'setUp' });
    expect(
      fillOutcome(answer({ yourPayment: { seatChargeId: 's-1', refusal: 'TERMS_NEEDED' } })),
    ).toEqual({ kind: 'termsAgain' });
  });

  it('is a vote counted otherwise — seats still open', () => {
    expect(fillOutcome(answer({ openSeats: 2 }))).toEqual({ kind: 'counted' });
    expect(fillOutcome(answer({ openSeats: 1 }))).toEqual({ kind: 'counted' });
  });

  // Q110: the four are matched, one payment missing — It's a game!, with until when.
  it('is the game waiting for one payment when this yes filled it and somebody else’s share was refused', () => {
    expect(
      fillOutcome(answer({ openSeats: 0, paymentAwaitedUntil: '2026-10-06T12:40:00Z' })),
    ).toEqual({ kind: 'paymentAwaited', bookingId: 'p-1', until: '2026-10-06T12:40:00Z' });
  });

  // Q110: a refusal of his own is no screen — his sheet, naming his time (Q109).
  it('is his own payment to confirm, with his time to pay, when the share refused is his', () => {
    expect(
      fillOutcome(
        answer({
          openSeats: 0,
          yourPayment: {
            seatChargeId: 's-1',
            refusal: 'AUTHENTICATION_REQUIRED',
            confirmBy: '2026-10-06T12:40:00Z',
          },
          paymentAwaitedUntil: '2026-10-06T12:40:00Z',
        }),
      ),
    ).toEqual({ kind: 'confirm', seatChargeId: 's-1', confirmBy: '2026-10-06T12:40:00Z' });
  });
});

describe('confirmationOf — a refused share to confirm, and its time to pay', () => {
  it('is the payment, with the time while one is given and none once it ran out', () => {
    const refused: YourPayment = {
      seatChargeId: 's-1',
      refusal: 'DECLINED',
      confirmBy: '2026-10-06T12:40:00Z',
    };
    expect(confirmationOf(refused)).toEqual({
      seatChargeId: 's-1',
      confirmBy: '2026-10-06T12:40:00Z',
    });
    expect(confirmationOf({ seatChargeId: 's-1' })).toEqual({ seatChargeId: 's-1' });
  });

  it('carries what the time is for to the sheet (#638; Q113)', () => {
    expect(
      confirmationOf({
        seatChargeId: 's-1',
        confirmBy: '2026-10-06T12:40:00Z',
        timeTo: 'FIX_THE_CARD',
      }),
    ).toEqual({ seatChargeId: 's-1', confirmBy: '2026-10-06T12:40:00Z', timeTo: 'FIX_THE_CARD' });
  });
});

describe('seatAtStake — whose seat a refused yes leaves at stake (#640)', () => {
  it('is a rescue’s when the yes was said on one, and the player’s own otherwise', () => {
    expect(seatAtStake({ type: 'SEAT_OPEN' })).toBe('aRescue');
    expect(seatAtStake({ type: 'PICKED_FOR_YOU' })).toBe('yours');
    // A TO CONFIRM row holds no card: the read does not say which it is.
    expect(seatAtStake(undefined)).toBe('yours');
  });
});

describe('paymentToConfirmOn — the reader’s refused share on one game', () => {
  const on = (proposalId: string, seatChargeId: string) => ({
    proposalId,
    groupId: 'g-1',
    sport: 'padel' as const,
    kind: 'competitive' as const,
    startsAt: '2026-10-03T14:00:00Z',
    club: { id: 'c-1', name: 'Bonarka Arena' },
    shareGrosze: 4000,
    deadline: '2026-10-02T14:00:00Z',
    seatChargeId,
    refusal: 'AUTHENTICATION_REQUIRED' as const,
  });

  /** A booking takes its proposal's id (#541): the game Home opens is the one the row is for. */
  it('is the row for the booking’s game, and nothing with none or no list', () => {
    const list = [on('p-1', 's-1'), on('p-2', 's-2')];
    expect(paymentToConfirmOn('p-2', list)?.seatChargeId).toBe('s-2');
    expect(paymentToConfirmOn('p-3', list)).toBeUndefined();
    expect(paymentToConfirmOn('p-1', undefined)).toBeUndefined();
  });
});

describe('aPaymentAwaited — what It’s a game! says is missing while one payment is (Q110)', () => {
  /** Tuesday 6 October, 14:10 in Warsaw. */
  const NOW = Date.parse('2026-10-06T12:10:00Z');

  it('is until when — the hour alone when it falls that day', () => {
    expect(aPaymentAwaited('2026-10-06T12:40:00Z', NOW)).toEqual({
      until: { at: '2026-10-06T12:40:00Z', today: true },
    });
  });

  it('says it falls on another day, past the club’s midnight', () => {
    expect(aPaymentAwaited('2026-10-06T22:15:00Z', NOW)).toEqual({
      until: { at: '2026-10-06T22:15:00Z', today: false },
    });
  });
});

describe('fillRefusal — the refused yeses the fill mends itself', () => {
  it('opens the setup for a yes with nothing saved', () => {
    expect(fillRefusal('payment_method_required', undefined)).toEqual({ kind: 'setUp' });
  });

  it('opens the confirmation on the payment a refusal names', () => {
    expect(fillRefusal('payment_to_confirm', { seat_charge_id: 's-1' })).toEqual({
      kind: 'confirm',
      seatChargeId: 's-1',
    });
  });

  it('leaves the screen to say every other refusal — and one that names no payment', () => {
    expect(fillRefusal('payment_to_confirm', {})).toBeUndefined();
    expect(fillRefusal('proposal_is_full', undefined)).toBeUndefined();
    expect(fillRefusal(undefined, undefined)).toBeUndefined();
  });
});

describe('itsAGamePicture — the faces It’s a game! draws', () => {
  it('puts you first on your side, then your partner, against the other side', () => {
    const zofia = person('Zofia', { isIn: true, photoUrl: 'https://photos/zofia.jpg' });
    const picture = itsAGamePicture(
      card({ sides: { yours: [zofia, YOU], theirs: [person('Ania'), person('Ewa')] } }),
    );

    expect(picture.yours.map((face) => face.name)).toEqual(['You', 'Zofia']);
    expect(picture.yours[1]).toEqual({
      playerId: 'id-Zofia',
      name: 'Zofia',
      photoUrl: 'https://photos/zofia.jpg',
    });
    expect(picture.theirs.map((face) => face.name)).toEqual(['Ania', 'Ewa']);
  });

  it('draws singles as you against them', () => {
    const picture = itsAGamePicture(card({ sides: { yours: [YOU], theirs: [person('Kuba')] } }));

    expect(picture.yours).toHaveLength(1);
    expect(picture.theirs.map((face) => face.name)).toEqual(['Kuba']);
  });

  it('keeps a person the server can no longer name, unnamed', () => {
    const nobody: DeckPerson = { playerId: 'id-gone', isYou: false, isIn: true };
    const picture = itsAGamePicture(card({ sides: { yours: [YOU], theirs: [nobody] } }));

    expect(picture.theirs).toEqual([{ playerId: 'id-gone' }]);
  });
});

describe('yesOnRescue — what the fill holds for a rescue’s I’m in', () => {
  it('is the booking’s seat, a rescue on a booked court, with the sides when the surface holds them', () => {
    expect(yesOnRescue({ bookingId: 'b-1' })).toEqual({
      proposalId: 'b-1',
      type: 'SEAT_OPEN',
      court: 'BOOKED',
    });
    const sides = { yours: [YOU], theirs: [] };
    expect(yesOnRescue({ bookingId: 'b-1', sides })).toMatchObject({ sides });
    expect(waitsForUndo(yesOnRescue({ bookingId: 'b-1' }))).toBe(true);
  });
});
