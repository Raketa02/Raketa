/** What the moment a game fills says: the count, It's a game! spoken whole, and a share's facts. */

import {
  bookingAnnouncement,
  bookingIn,
  chargeGameLine,
  chargeLine,
  itsAGameLine,
  itsAGameSentence,
  confirmNote,
  refusedToast,
  seatKeptBy,
  toConfirmLabel,
  toConfirmRowLine,
} from './fillPresentation';

describe('the Undo toast', () => {
  it('counts in whole seconds, and says once that the booking can be undone', () => {
    expect(bookingIn(10)).toBe('Booking in 10 s');
    expect(bookingAnnouncement(10)).toBe('Booking in 10 seconds. You can undo it.');
  });
});

describe('It’s a game! as a listener hears it', () => {
  it('names you, your partner and the other side, whole', () => {
    expect(
      itsAGameSentence({
        yours: [
          { playerId: 'me', name: 'ada' },
          { playerId: 'z', name: 'zofia.b' },
        ],
        theirs: [
          { playerId: 'a', name: 'ania.k' },
          { playerId: 'e', name: 'ewa.m' },
        ],
      }),
    ).toBe('It’s a game! You and zofia.b against ania.k and ewa.m');
  });

  it('says singles as you against them, and a person with no name as the unknown mark', () => {
    expect(itsAGameSentence({ yours: [{ playerId: 'me' }], theirs: [{ playerId: 'gone' }] })).toBe(
      'It’s a game! You against ?',
    );
  });

  it('says the line under the word after the picture (Q110)', () => {
    const line = itsAGameLine({ until: { at: '2026-10-06T12:40:00Z', today: true } });
    expect(
      itsAGameSentence(
        { yours: [{ playerId: 'me' }], theirs: [{ playerId: 'k', name: 'kuba.w' }] },
        line.spoken,
      ),
    ).toBe(
      'It’s a game! You against kuba.w. Waiting for one payment until 14:40. Nobody pays until it’s in',
    );
  });
});

/** Tuesday 6 October 2026 in Warsaw. */
describe('It’s a game!’s line while one payment is missing (Q110)', () => {
  it('says until when, the hour alone that day, and never whose — drawn with dots, spoken in sentences', () => {
    expect(itsAGameLine({ until: { at: '2026-10-06T12:40:00Z', today: true } })).toEqual({
      drawn: 'Waiting for one payment · until 14:40 · Nobody pays until it’s in',
      spoken: 'Waiting for one payment until 14:40. Nobody pays until it’s in',
    });
  });

  it('names the weekday when the time falls on another day', () => {
    expect(itsAGameLine({ until: { at: '2026-10-06T22:15:00Z', today: false } }).drawn).toBe(
      'Waiting for one payment · until Wed 00:15 · Nobody pays until it’s in',
    );
  });
});

describe('the time to pay, where the payer confirms (Q109)', () => {
  it('names the time on the sheet, and on a To confirm row while it runs', () => {
    const by = { at: '2026-10-06T12:40:00Z', today: true } as const;
    const time = { by, window: 'PAY' } as const;
    expect(seatKeptBy(time, 'yours')).toBe('Confirm your payment by 14:40 to keep your seat');
    expect(toConfirmRowLine(time)).toBe('Confirm your payment by 14:40');
  });

  it('says the seat is open to others on a row whose time ran out', () => {
    expect(toConfirmRowLine(undefined)).toBe(
      'Your seat stays open until you confirm — or someone else takes it.',
    );
  });
});

describe('the time to fix the card, before the cut-off (Q113)', () => {
  const by = { at: '2026-10-06T12:40:00Z', today: true } as const;
  const fix = { by, window: 'FIX_THE_CARD' } as const;
  const pay = { by, window: 'PAY' } as const;

  it('names the window the server names — to fix the card before the cut-off, to pay after it', () => {
    expect(seatKeptBy(fix, 'yours')).toBe('Fix your card by 14:40 to keep your seat');
    expect(seatKeptBy(pay, 'yours')).toBe('Confirm your payment by 14:40 to keep your seat');
    expect(seatKeptBy({ by, window: 'UNNAMED' }, 'yours')).toBe(
      'Confirm your payment by 14:40 to keep your seat',
    );
    expect(toConfirmRowLine(fix)).toBe('Fix your card by 14:40');
    expect(toConfirmRowLine(pay)).toBe('Confirm your payment by 14:40');
  });

  it('says a rescuer’s seat is kept for them to take (#640), and the time alone where no seat is named', () => {
    expect(seatKeptBy(fix, 'aRescue')).toBe('Fix your card by 14:40 to take the seat');
    expect(seatKeptBy(pay, 'aRescue')).toBe('Confirm your payment by 14:40 to take the seat');
    expect(seatKeptBy(fix, undefined)).toBe('Fix your card by 14:40');
  });

  it('notes on the sheet whose seat it is, and that a rescuer’s is theirs until then', () => {
    expect(confirmNote(fix, 'yours')).toBe('Fix your card by 14:40 to keep your seat');
    expect(confirmNote(fix, 'aRescue')).toBe(
      'Fix your card by 14:40 to take the seat — it’s kept for you until then',
    );
    expect(confirmNote(pay, 'aRescue')).toBe(
      'Confirm your payment by 14:40 to take the seat — it’s kept for you until then',
    );
  });

  it('tells a card refused at the fill or on a rescue, by its window (the screens A2.4)', () => {
    expect(refusedToast('FIX_THE_CARD', 'yours')).toBe(
      'Your card didn’t go through — fix it to keep your seat. Nothing is paid now.',
    );
    expect(refusedToast('PAY', 'yours')).toBe(
      'Your payment didn’t go through — confirm it to keep your seat',
    );
    expect(refusedToast('UNNAMED', 'yours')).toBe(
      'Your payment didn’t go through — confirm it to keep your seat',
    );
    expect(refusedToast('FIX_THE_CARD', 'aRescue')).toBe(
      'Your card didn’t go through — fix it to take the seat. Nothing is paid now.',
    );
    expect(refusedToast('PAY', 'aRescue')).toBe(
      'Your payment didn’t go through — confirm it to take the seat',
    );
  });

  it('speaks a To confirm row’s button by its window — confirm, never pay, with none named', () => {
    const payment = {
      proposalId: 'p-1',
      groupId: 'group-1',
      sport: 'padel',
      kind: 'competitive',
      startsAt: '2026-10-03T13:00:00Z',
      deadline: '2026-10-03T11:00:00Z',
      club: { id: 'club-1', name: 'Bonarka Arena' },
      shareGrosze: 2800,
      waitingForTheClub: false,
      seatChargeId: 's-1',
      refusal: 'AUTHENTICATION_REQUIRED',
      confirmBy: '2026-10-01T08:30:00Z',
      timeTo: 'FIX_THE_CARD',
    } as const;
    const day = { kind: 'weekday', weekday: 6 } as const;
    expect(toConfirmLabel(payment, day, 'FIX_THE_CARD')).toBe(
      'Fix your card for Padel · Saturday 15:00 at Bonarka Arena, 28 zł',
    );
    expect(toConfirmLabel(payment, day, 'PAY')).toBe(
      'Confirm your payment for Padel · Saturday 15:00 at Bonarka Arena, 28 zł',
    );
    expect(toConfirmLabel(payment, day, 'UNNAMED')).toBe(
      'Confirm your payment for Padel · Saturday 15:00 at Bonarka Arena, 28 zł',
    );
  });
});

describe('a payment to confirm', () => {
  it('says the share and the seller, and the game it is for', () => {
    expect(chargeLine(3200, 'Bonarka Arena')).toBe('32 zł to Bonarka Arena');
    expect(chargeLine(2750, undefined)).toBe('27,50 zł to the club');
    // Wednesday 30 September 2026, 10:00 in Warsaw; the game Saturday 16:00.
    expect(
      chargeGameLine('padel', '2026-10-03T14:00:00Z', Date.parse('2026-09-30T08:00:00Z')),
    ).toBe('Padel · Saturday · 16:00');
  });
});
