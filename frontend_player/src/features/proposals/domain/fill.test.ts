/**
 * The rules of the moment a yes may fill a game — which yes waits ten seconds behind *Undo*, how
 * long it has left, what the server's answer to it means, and who *It's a game!* draws.
 */

import type { DeckCard, DeckPerson } from './deck';
import {
  UNDO_WINDOW_MS,
  fillOutcome,
  fillRefusal,
  itsAGamePicture,
  itsAGameWaiting,
  undoSecondsLeft,
  waitsForUndo,
  yesOnRescue,
  type YesAnswer,
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
    clubConfirms: false,
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
    waitingForTheClub: false,
    yourPayment: null,
    ...extra,
  };
}

describe('waitsForUndo — the yes that moves money waits ten seconds (the mechanics §6.5)', () => {
  it('holds a yes on Book it now', () => {
    expect(waitsForUndo(card({ court: 'BOOK_IT_NOW', openSeatsAfterYourYes: 0 }))).toBe(true);
  });

  it('holds Book it now at an On request club too — at zero the game goes to the club (A2.4)', () => {
    expect(waitsForUndo(card({ court: 'BOOK_IT_NOW', clubConfirms: true }))).toBe(true);
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

  // Q103: It's a game! at once, for the game the yes filled — the booking it went to the club as.
  it('is the game sent to the club when an On request club has it to confirm (#543)', () => {
    expect(fillOutcome(answer({ openSeats: 0, waitingForTheClub: true }))).toEqual({
      kind: 'waiting',
      bookingId: 'p-1',
    });
  });

  it('is a vote counted otherwise — seats still open, or somebody else’s share refused', () => {
    expect(fillOutcome(answer({ openSeats: 2 }))).toEqual({ kind: 'counted' });
    expect(fillOutcome(answer({ openSeats: 1 }))).toEqual({ kind: 'counted' });
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

describe('itsAGameWaiting — what It’s a game! says is missing at a club that confirms (Q103)', () => {
  /** Read at 10:00 in Warsaw, Wednesday 30 September. */
  const READ_AT = '2026-09-30T08:00:00Z';
  /** `null` — a read that no longer names the club. */
  const read = (answerBy: string | undefined, name: string | null = 'Kazimierz Padel') => ({
    readAt: READ_AT,
    where: { id: 'c-9', ...(name === null ? {} : { name }) },
    ...(answerBy === undefined ? {} : { answerBy }),
  });

  it('is the club’s deadline from the booking’s read, the hour alone when it falls that day', () => {
    expect(itsAGameWaiting('Kazimierz Padel', read('2026-09-30T19:15:00Z'))).toEqual({
      club: 'Kazimierz Padel',
      answerBy: { at: '2026-09-30T19:15:00Z', today: true },
    });
  });

  it('says it falls on another day — a club given until the next morning', () => {
    expect(itsAGameWaiting('Kazimierz Padel', read('2026-10-01T07:00:00Z'))).toEqual({
      club: 'Kazimierz Padel',
      answerBy: { at: '2026-10-01T07:00:00Z', today: false },
    });
  });

  it('names no deadline the read says is gone, or does not give', () => {
    expect(itsAGameWaiting('Kazimierz Padel', read('2026-09-30T07:59:00Z'))).toEqual({
      club: 'Kazimierz Padel',
    });
    expect(itsAGameWaiting('Kazimierz Padel', read(undefined))).toEqual({
      club: 'Kazimierz Padel',
    });
  });

  it('with no read, is the club the card named — and nothing when it named none', () => {
    expect(itsAGameWaiting('Bonarka Arena', undefined)).toEqual({ club: 'Bonarka Arena' });
    expect(itsAGameWaiting(undefined, undefined)).toEqual({});
  });

  it('takes the club’s name from the read, and the card’s when the read has none', () => {
    expect(itsAGameWaiting('Old name', read(undefined, 'Kazimierz Padel'))).toEqual({
      club: 'Kazimierz Padel',
    });
    expect(itsAGameWaiting('Bonarka Arena', read(undefined, null))).toEqual({
      club: 'Bonarka Arena',
    });
  });
});

describe('yesOnRescue — what the fill holds for a rescue’s I’m in', () => {
  it('is the booking’s seat, a rescue on a booked court, with the sides when the surface holds them', () => {
    const club = { id: 'club-1', name: 'Ogrody 33' };
    expect(yesOnRescue({ bookingId: 'b-1', club })).toEqual({
      proposalId: 'b-1',
      type: 'SEAT_OPEN',
      court: 'BOOKED',
      club,
    });
    const sides = { yours: [YOU], theirs: [] };
    expect(yesOnRescue({ bookingId: 'b-1', club, sides })).toMatchObject({ sides });
    expect(waitsForUndo(yesOnRescue({ bookingId: 'b-1', club }))).toBe(true);
  });
});
