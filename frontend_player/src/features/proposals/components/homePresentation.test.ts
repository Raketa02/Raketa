import { setDeviceZone } from '@/test-support/deviceZone';

import type { BookedGame, HomeGame } from '../domain/home';

import {
  clubsAnswer,
  homeCardLabel,
  leavingLine,
  leavingSheetBody,
  leftToast,
  moneyRow,
  moneySpoken,
  moneyWords,
  shortCodeSpoken,
  sportWords,
  statusSubline,
  whereAside,
} from './homePresentation';

/** Friday 2 October 2026, 16:00 in Warsaw — the club's cut-off. */
const CUT_OFF = '2026-10-02T14:00:00Z';
const BEFORE = Date.parse('2026-10-01T08:00:00Z');

/** Monday 28 September, 16:00 in Warsaw — a checked share's holding time, four days before it. */
const HOLDING = '2026-09-28T14:00:00Z';

/** The club's deadline to answer: 11:00 on the day of the read (Thursday, 10:00 in Warsaw). */
const ELEVEN = '2026-10-01T09:00:00Z';
const ELEVEN_TODAY = { at: ELEVEN, today: true } as const;
/** Sunday 4 October, 00:15 in Warsaw — still Saturday in UTC, and in New York. */
const SUNDAY_00_15 = { at: '2026-10-03T22:15:00Z', today: false } as const;

beforeAll(() => setDeviceZone('America/New_York'));

describe('moneyWords — the line under a Home card (the mechanics §14.1)', () => {
  it('reads the share, free to leave until the cut-off on the club’s clock, then Paid once taken (Q113)', () => {
    expect(
      moneyWords({ kind: 'booked', shareGrosze: 3000, paid: false, freeToLeaveUntil: CUT_OFF }),
    ).toBe('30 zł · free to leave until Fri 16:00');
    expect(moneyWords({ kind: 'booked', shareGrosze: 2750, paid: true })).toBe('Paid · 27,50 zł');
    expect(moneyWords({ kind: 'booked', shareGrosze: 2750, paid: false })).toBe('27,50 zł');
  });

  it('names the club a game waits for, or the club when the read no longer names it', () => {
    expect(moneyWords({ kind: 'waiting', club: 'Bonarka Arena' })).toBe(
      'Nobody pays until Bonarka Arena confirms',
    );
    expect(moneyWords({ kind: 'waiting' })).toBe('Nobody pays until the club confirms');
  });

  it('says when the club answers while it may — the hour alone today, the weekday on another day', () => {
    expect(moneyWords({ kind: 'waiting', club: 'Kazimierz Padel', answerBy: ELEVEN_TODAY })).toBe(
      'Kazimierz Padel answers by 11:00 · Nobody pays until it confirms',
    );
    expect(moneyWords({ kind: 'waiting', answerBy: ELEVEN_TODAY })).toBe(
      'The club answers by 11:00 · Nobody pays until it confirms',
    );
    expect(moneyWords({ kind: 'waiting', club: 'Bonarka Arena', answerBy: SUNDAY_00_15 })).toBe(
      'Bonarka Arena answers by Sun 00:15 · Nobody pays until it confirms',
    );
  });

  it('counts the seats open, before the cut-off and after it', () => {
    expect(moneyWords({ kind: 'seatOpen', seats: 1, fillsBy: CUT_OFF })).toBe(
      '1 seat open · fills by Fri 16:00 or the game is off and nothing is taken',
    );
    expect(moneyWords({ kind: 'seatOpen', seats: 2 })).toBe(
      '2 seats open · offered to others · the game goes ahead',
    );
  });

  /** A full game gone back to filling (Q106): mirroring a booked game's *Seat open*. */
  it('says the seats open on a game filling again, and how it is booked once full', () => {
    expect(
      moneyWords({ kind: 'fillingAgain', seats: 1, club: 'Kazimierz Padel', clubConfirms: true }),
    ).toBe('1 seat open · Kazimierz Padel is asked again when it’s full · nobody paid');
    expect(
      moneyWords({ kind: 'fillingAgain', seats: 1, club: 'Kazimierz Padel', clubConfirms: false }),
    ).toBe('1 seat open · books when it’s full · nobody paid');
    expect(moneyWords({ kind: 'fillingAgain', seats: 2, clubConfirms: true })).toBe(
      '2 seats open · the club is asked again when it’s full · nobody paid',
    );
  });

  it('says the refund, or that nobody paid', () => {
    expect(moneyWords({ kind: 'calledOff', refundedGrosze: 3000 })).toBe('Refunded 30 zł');
    expect(moneyWords({ kind: 'calledOff' })).toBe('Nobody paid');
  });

  it('says why a game is off before what came back (§14.1)', () => {
    expect(
      moneyWords({
        kind: 'calledOff',
        reason: 'CANCELLED_BY_THE_CLUB',
        club: 'Bonarka Arena',
        refundedGrosze: 3000,
      }),
    ).toBe('Bonarka Arena cancelled it · Refunded 30 zł');
  });

  /** Q113: the holds were let go — at the cut-off, or by the club's cancel before it. */
  it('says nothing was taken where the shares were held and let go', () => {
    expect(
      moneyWords({ kind: 'calledOff', reason: 'SHORT_AT_THE_CUT_OFF', club: 'Bonarka Arena' }),
    ).toBe('A seat was still empty at the cut-off · Nothing was taken');
    expect(
      moneyWords({
        kind: 'calledOff',
        reason: 'CANCELLED_BY_THE_CLUB',
        clubCancelReason: 'WEATHER',
        club: 'Bonarka Arena',
      }),
    ).toBe('Bonarka Arena cancelled it because of the weather · Nothing was taken');
  });

  /** The club's no and its silence, in the notice's and the email's words (Q105). */
  it('says the club said no, or didn’t answer in time — never the one for the other', () => {
    expect(moneyWords({ kind: 'calledOff', reason: 'REFUSED', club: 'Kazimierz Padel' })).toBe(
      'Kazimierz Padel said no · Nobody paid — you’ll get a new card first',
    );
    expect(moneyWords({ kind: 'calledOff', reason: 'NO_ANSWER', club: 'Kazimierz Padel' })).toBe(
      'Kazimierz Padel didn’t answer in time · Nobody paid — you’ll get a new card first',
    );
    expect(moneyWords({ kind: 'calledOff', reason: 'REFUSED' })).toBe(
      'The club said no · Nobody paid — you’ll get a new card first',
    );
    expect(moneyWords({ kind: 'calledOff', reason: 'NO_ANSWER' })).toBe(
      'The club didn’t answer in time · Nobody paid — you’ll get a new card first',
    );
  });

  /** A game gone back to filling that ends before it is full again (#624) — said of the game. */
  it('says a game filling again ran out of time, or lost its court', () => {
    expect(
      moneyWords({ kind: 'calledOff', reason: 'BOOK_BY_PASSED', club: 'Kazimierz Padel' }),
    ).toBe('A seat was open past its last moment to book · Nobody paid');
    expect(
      moneyWords({ kind: 'calledOff', reason: 'COURT_HOUR_LOST', club: 'Kazimierz Padel' }),
    ).toBe('Its court went to another game before it filled again · Nobody paid');
  });

  /** Q111: one payment awaited — until when, never whose; the payer reads their own time. */
  it('says a game waits for one payment, until when while it may, and the payer’s own time', () => {
    expect(moneyWords({ kind: 'paymentAwaited', until: ELEVEN_TODAY })).toBe(
      'Waiting for one payment · until 11:00 · Nobody pays until it’s in',
    );
    expect(moneyWords({ kind: 'paymentAwaited', until: SUNDAY_00_15 })).toBe(
      'Waiting for one payment · until Sun 00:15 · Nobody pays until it’s in',
    );
    expect(moneyWords({ kind: 'paymentAwaited' })).toBe(
      'Waiting for one payment · Nobody pays until it’s in',
    );
    expect(moneyWords({ kind: 'yourPayment', by: ELEVEN_TODAY })).toBe(
      'Confirm your payment by 11:00',
    );
  });

  it('says a payment didn’t go through in time, and nobody paid (#625)', () => {
    expect(
      moneyWords({ kind: 'calledOff', reason: 'PAYMENT_NOT_IN_TIME', club: 'Bonarka Arena' }),
    ).toBe('A payment didn’t go through in time · Nobody paid');
  });

  it('says a seat was empty on a game that started short', () => {
    expect(moneyWords({ kind: 'seatEmpty' })).toBe('A seat was empty · no Level moved');
  });

  /** The club's cancel (#547; the mechanics §16.9): the club named, its reason, the refund. */
  it('names the club that cancelled, and why, before the refund', () => {
    expect(
      moneyWords({
        kind: 'calledOff',
        reason: 'CANCELLED_BY_THE_CLUB',
        clubCancelReason: 'WEATHER',
        club: 'Bonarka Arena',
        refundedGrosze: 3000,
      }),
    ).toBe('Bonarka Arena cancelled it because of the weather · Refunded 30 zł');
    expect(
      moneyWords({
        kind: 'calledOff',
        reason: 'CANCELLED_BY_THE_CLUB',
        clubCancelReason: 'OTHER',
        club: 'Bonarka Arena',
        refundedGrosze: 3000,
      }),
    ).toBe('Bonarka Arena cancelled it · Refunded 30 zł');
  });

  /** Somebody didn't come (#560) — said to the player marked as theirs to answer. */
  it('tells the player marked that they were, and everybody else that somebody didn’t come', () => {
    expect(moneyWords({ kind: 'noShow', yours: true })).toBe(
      'You were marked as not coming · say so if you were there',
    );
    expect(moneyWords({ kind: 'noShow', yours: false })).toBe(
      'Somebody didn’t come · no Level moved',
    );
  });
});

describe('statusSubline — the details’ second line', () => {
  it('says a game waiting for one payment, lower case', () => {
    expect(statusSubline('padel', 'WAITING_FOR_A_PAYMENT')).toBe('Padel · waiting for one payment');
  });

  it('is the sport and the status, lower case: Padel · booked', () => {
    expect(statusSubline('padel', 'BOOKED')).toBe('Padel · booked');
    expect(statusSubline('tennis', 'WAITING_FOR_THE_CLUB')).toBe('Tennis · waiting for the club');
  });
});

describe('whereAside — the court and how far it is (details 8)', () => {
  const at = { status: 'BOOKED', courtName: 'Court 2' } as const;

  it('is the court, with the distance when the reader has a Location area', () => {
    expect(whereAside(at, 3.1)).toBe('Court 2 · 3,1 km');
    expect(whereAside(at, undefined)).toBe('Court 2');
  });

  it('names no court while the club has still to say yes (A4.2)', () => {
    const waiting = { ...at, status: 'WAITING_FOR_THE_CLUB' } as const;
    expect(whereAside(waiting, 3.1)).toBe('3,1 km');
    expect(whereAside(waiting, undefined)).toBeUndefined();
  });

  it('names no court the read does not hold', () => {
    expect(whereAside({ status: 'CALLED_OFF' }, 3.1)).toBe('3,1 km');
  });

  it('names no court on a game gone back to filling, though the read held one', () => {
    const filling = { ...at, status: 'SEAT_OPEN', fillingAgain: { clubConfirms: true } } as const;
    expect(whereAside(filling, 3.1)).toBe('3,1 km');
  });
});

describe('moneySpoken — the line aloud, its dots commas', () => {
  it('says each clause the line draws, and nothing it does not', () => {
    expect(
      moneySpoken({ kind: 'booked', shareGrosze: 3000, paid: false, freeToLeaveUntil: CUT_OFF }),
    ).toBe('30 zł, free to leave until Fri 16:00');
    expect(moneySpoken({ kind: 'seatOpen', seats: 1 })).toBe(
      '1 seat open, offered to others, the game goes ahead',
    );
    expect(moneySpoken({ kind: 'waiting', club: 'Kazimierz Padel', answerBy: ELEVEN_TODAY })).toBe(
      'Kazimierz Padel answers by 11:00, Nobody pays until it confirms',
    );
  });
});

describe('sportWords — a card’s sport word', () => {
  it('says the kind only when the game is a friendly', () => {
    expect(sportWords('padel', 'competitive')).toBe('Padel');
    expect(sportWords('padel', 'forFun')).toBe('Padel · For fun');
  });
});

describe('clubsAnswer — the club’s answer to a game it turned down (Q105)', () => {
  const where = { id: 'club-1', name: 'Kazimierz Padel' };

  it('says the club said no, or didn’t answer in time', () => {
    expect(clubsAnswer({ calledOffReason: 'REFUSED', where })).toBe('Kazimierz Padel said no');
    expect(clubsAnswer({ calledOffReason: 'NO_ANSWER', where })).toBe(
      'Kazimierz Padel didn’t answer in time',
    );
  });

  it('says it of the club when the read no longer names it', () => {
    expect(clubsAnswer({ calledOffReason: 'REFUSED', where: { id: 'club-1' } })).toBe(
      'The club said no',
    );
  });

  it.each([
    'SHORT_AT_THE_CUT_OFF',
    'CANCELLED_BY_THE_CLUB',
    'BOOK_BY_PASSED',
    'COURT_HOUR_LOST',
  ] as const)('is nothing for %s, which is no answer to a request', (calledOffReason) => {
    expect(clubsAnswer({ calledOffReason, where })).toBeUndefined();
  });

  it('is nothing for a game not called off', () => {
    expect(clubsAnswer({ where })).toBeUndefined();
  });
});

describe('shortCodeSpoken — the code for the desk, aloud', () => {
  it('is said a character at a time', () => {
    expect(shortCodeSpoken('K7M2QX')).toBe('Your check-in code: K 7 M 2 Q X');
  });
});

const booked = (extra: Partial<BookedGame> = {}): BookedGame => ({
  bookingId: 'b-1',
  gameId: 'g-1',
  groupId: 'group-1',
  sport: 'padel',
  kind: 'competitive',
  readAt: '2026-10-01T08:00:00Z',
  status: 'BOOKED',
  openSeats: 0,
  needsYou: false,
  startsAt: '2026-10-03T14:00:00Z',
  endsAt: '2026-10-03T15:00:00Z',
  where: { id: 'club-1', name: 'Bonarka Arena', distanceKm: 3.1 },
  courtName: 'Court 2',
  sides: { yours: [], theirs: [] },
  money: {
    shareGrosze: 2800,
    paid: false,
    shareState: 'HELD',
    takenAt: CUT_OFF,
    freeToLeaveUntil: CUT_OFF,
  },
  showsForecast: true,
  ...extra,
});

const bookedPaid = { shareGrosze: 2800, paid: true } as const;

describe('moneyRow — the details’ money row (A4.1)', () => {
  /** Q113: when the share is held and when it is taken — then PAID 28 zł over Paid. */
  it('is the share held on the card, when it is taken, and free to leave until then', () => {
    expect(moneyRow(booked(), BEFORE)).toEqual({
      label: 'Your share',
      value: '28 zł',
      below: 'Held on your card · taken Fri 16:00 · free to leave until then',
    });
    expect(moneyRow(booked(), Date.parse(CUT_OFF))).toEqual({
      label: 'Paid',
      value: '28 zł',
      below: 'Paid',
    });
  });

  it('is the share held from its holding time while it is only checked, then held', () => {
    const checked = booked({
      money: { ...booked().money, shareState: 'CHECKED', heldFrom: HOLDING },
    });
    expect(moneyRow(checked, Date.parse('2026-09-27T08:00:00Z'))).toEqual({
      label: 'Your share',
      value: '28 zł',
      below: 'Held from Mon 16:00 · taken Fri 16:00',
    });
    expect(moneyRow(checked, Date.parse(HOLDING))).toEqual({
      label: 'Your share',
      value: '28 zł',
      below: 'Held on your card · taken Fri 16:00 · free to leave until then',
    });
  });

  it('is PAID over Paid once the read says the share was taken', () => {
    expect(moneyRow(booked({ money: bookedPaid }), BEFORE)).toEqual({
      label: 'Paid',
      value: '28 zł',
      below: 'Paid',
    });
  });

  /** A full game gone back to filling (Q106): the Home card's line word for word under the share. */
  it('is the share nobody pays, over the seat open and how it is booked, on a game filling again', () => {
    const filling = (clubConfirms: boolean) =>
      booked({
        status: 'SEAT_OPEN',
        openSeats: 1,
        where: { id: 'club-1', name: 'Kazimierz Padel', distanceKm: 3.1 },
        money: { shareGrosze: 2500, paid: false },
        fillingAgain: { clubConfirms },
      });
    expect(moneyRow(filling(true), BEFORE)).toEqual({
      label: 'Your share',
      value: '25 zł',
      below: '1 seat open · Kazimierz Padel is asked again when it’s full · nobody paid',
    });
    expect(moneyRow(filling(false), BEFORE)).toEqual({
      label: 'Your share',
      value: '25 zł',
      below: '1 seat open · books when it’s full · nobody paid',
    });
  });

  it('is the share nobody pays yet while the club decides', () => {
    expect(
      moneyRow(
        booked({ status: 'WAITING_FOR_THE_CLUB', money: { shareGrosze: 2800, paid: false } }),
        BEFORE,
      ),
    ).toEqual({
      label: 'Your share',
      value: '28 zł',
      below: 'Nobody pays until Bonarka Arena confirms',
    });
  });

  it('says under it when the club answers, until that deadline passes (Q98)', () => {
    const waiting = booked({
      status: 'WAITING_FOR_THE_CLUB',
      money: { shareGrosze: 2500, paid: false },
      answerBy: ELEVEN,
    });
    expect(moneyRow(waiting, BEFORE)).toEqual({
      label: 'Your share',
      value: '25 zł',
      below: 'Bonarka Arena answers by 11:00 · Nobody pays until it confirms',
    });
    expect(moneyRow(waiting, Date.parse(ELEVEN))).toEqual({
      label: 'Your share',
      value: '25 zł',
      below: 'Nobody pays until Bonarka Arena confirms',
    });
  });

  /** Q111: the card's own line under the share nobody pays yet — and the payer's own time. */
  it('is the share nobody pays yet while one payment is awaited, over until when — or the payer’s time', () => {
    const waiting = booked({
      status: 'WAITING_FOR_A_PAYMENT',
      gameId: undefined,
      courtName: undefined,
      money: { shareGrosze: 4000, paid: false },
      paymentDueBy: ELEVEN,
    });
    expect(moneyRow(waiting, BEFORE)).toEqual({
      label: 'Your share',
      value: '40 zł',
      below: 'Waiting for one payment · until 11:00 · Nobody pays until it’s in',
    });
    expect(moneyRow({ ...waiting, yourPaymentDueBy: ELEVEN }, BEFORE)).toEqual({
      label: 'Your share',
      value: '40 zł',
      below: 'Confirm your payment by 11:00',
    });
    expect(moneyRow({ ...waiting, yourPaymentDueBy: ELEVEN }, Date.parse(ELEVEN))).toEqual({
      label: 'Your share',
      value: '40 zł',
      below: 'Waiting for one payment · Nobody pays until it’s in',
    });
  });

  it('is what came back, nothing taken, or nobody paid, once the game is called off', () => {
    expect(
      moneyRow(
        booked({
          status: 'CALLED_OFF',
          money: { shareGrosze: 2800, paid: true, refundedGrosze: 2800 },
        }),
        BEFORE,
      ),
    ).toEqual({ label: 'Refunded', value: '28 zł' });
    expect(
      moneyRow(booked({ status: 'CALLED_OFF', money: { shareGrosze: 2800, paid: false } }), BEFORE),
    ).toEqual({ label: 'Your share', value: '28 zł', below: 'nobody paid' });
    expect(
      moneyRow(
        booked({
          status: 'CALLED_OFF',
          calledOffReason: 'SHORT_AT_THE_CUT_OFF',
          money: { shareGrosze: 2800, paid: false },
        }),
        BEFORE,
      ),
    ).toEqual({
      label: 'Your share',
      value: '28 zł',
      below: 'A seat was still empty at the cut-off · nothing was taken',
    });
  });

  it('says the seat open and when it must fill, on a game a player left (§14.1)', () => {
    const open = booked({ status: 'SEAT_OPEN', openSeats: 1 });
    expect(moneyRow(open, BEFORE)).toEqual({
      label: 'Your share',
      value: '28 zł',
      below: '1 seat open · fills by Fri 16:00 or the game is off and nothing is taken',
    });
    expect(moneyRow(open, Date.parse(CUT_OFF))).toEqual({
      label: 'Paid',
      value: '28 zł',
      below: '1 seat open · offered to others · the game goes ahead',
    });
  });

  it('says why a game is off under what came back', () => {
    expect(
      moneyRow(
        booked({
          status: 'CALLED_OFF',
          calledOffReason: 'CANCELLED_BY_THE_CLUB',
          money: { shareGrosze: 2800, paid: true, refundedGrosze: 2800 },
        }),
        BEFORE,
      ),
    ).toEqual({
      label: 'Refunded',
      value: '28 zł',
      below: 'Bonarka Arena cancelled it',
    });
    expect(
      moneyRow(
        booked({
          status: 'CALLED_OFF',
          calledOffReason: 'REFUSED',
          money: { shareGrosze: 2800, paid: false },
        }),
        BEFORE,
      ),
    ).toEqual({
      label: 'Your share',
      value: '28 zł',
      below: 'Bonarka Arena said no · nobody paid — you’ll get a new card first',
    });
  });

  it('says a seat was empty on a game that started short', () => {
    expect(
      moneyRow(
        booked({ status: 'UNCOUNTED', uncountedReason: 'SEAT_EMPTY', money: bookedPaid }),
        BEFORE,
      ),
    ).toEqual({ label: 'Paid', value: '28 zł', below: 'A seat was empty · no Level moved' });
  });

  it('is the share I’m in would pay, and how long the seat is offered, on a rescue seen from outside', () => {
    const rescue = (fillsByTheCutOff: boolean) =>
      booked({
        status: 'SEAT_OPEN',
        openSeats: 1,
        money: { shareGrosze: 2700, paid: false },
        rescue: { deadline: CUT_OFF, fillsByTheCutOff },
      });
    expect(moneyRow(rescue(true), BEFORE)).toEqual({
      label: 'Your share',
      value: '27 zł',
      below: 'fills by Fri 16:00',
    });
    expect(moneyRow(rescue(false), BEFORE)).toEqual({
      label: 'Your share',
      value: '27 zł',
      below: 'offered until the start',
    });
  });
});

describe('homeCardLabel — a Home card, spoken as one element', () => {
  const game: HomeGame = {
    bookingId: 'b-1',
    gameId: 'g-1',
    groupId: 'group-1',
    sport: 'padel',
    kind: 'competitive',
    status: 'BOOKED',
    openSeats: 0,
    needsYou: false,
    startsAt: '2026-10-03T14:00:00Z',
    club: { id: 'club-1', name: 'Bonarka Arena' },
    courtName: 'Court 2',
    sides: { yours: [], theirs: [] },
    money: { shareGrosze: 3000, paid: false, freeToLeaveUntil: CUT_OFF },
  };

  it('says the status, new, the sport, where, when and the money — commas for the dots', () => {
    expect(
      homeCardLabel({
        game,
        fresh: true,
        day: { kind: 'weekday', weekday: 6 },
        money: { kind: 'booked', shareGrosze: 3000, paid: false, freeToLeaveUntil: CUT_OFF },
      }),
    ).toBe(
      'Booked, new. Padel. Bonarka Arena, Court 2. Saturday, 16:00 until 17:00. 30 zł, free to leave until Fri 16:00.',
    );
  });

  it('leaves out what the card does not draw', () => {
    expect(
      homeCardLabel({
        game: { ...game, status: 'COUNTED' },
        fresh: false,
        day: undefined,
        money: undefined,
      }),
    ).toBe('Counted. Padel. Bonarka Arena, Court 2. 16:00 until 17:00.');
  });

  it('says a game gone back to filling with no court, and its line', () => {
    expect(
      homeCardLabel({
        game: {
          ...game,
          status: 'SEAT_OPEN',
          club: { id: 'club-1', name: 'Kazimierz Padel' },
          fillingAgain: { clubConfirms: true },
        },
        fresh: false,
        day: { kind: 'weekday', weekday: 6 },
        money: { kind: 'fillingAgain', seats: 1, club: 'Kazimierz Padel', clubConfirms: true },
      }),
    ).toBe(
      'Seat open. Padel. Kazimierz Padel. Saturday, 16:00 until 17:00. 1 seat open, Kazimierz Padel is asked again when it’s full, nobody paid.',
    );
  });

  it('says when the club answers as part of the line', () => {
    expect(
      homeCardLabel({
        game: {
          ...game,
          status: 'WAITING_FOR_THE_CLUB',
          club: { id: 'club-1', name: 'Kazimierz Padel' },
        },
        fresh: false,
        day: { kind: 'weekday', weekday: 6 },
        money: { kind: 'waiting', club: 'Kazimierz Padel', answerBy: ELEVEN_TODAY },
      }),
    ).toBe(
      'Waiting for the club. Padel. Kazimierz Padel. Saturday, 16:00 until 17:00. Kazimierz Padel answers by 11:00, Nobody pays until it confirms.',
    );
  });
});

/**
 * ***Leave the game*** (the mechanics §13; Q113) — before the cut-off it is free and nothing is
 * taken, the hold let go when there is one; after it the share stays taken, and what comes back if
 * the seat is taken is #644's to say, so no figure is given here.
 */
describe('leavingLine, leavingSheetBody, leftToast — what leaving costs, said', () => {
  it('says leaving is free before the cut-off, and nothing is taken', () => {
    expect(leavingLine({ kind: 'BEFORE_THE_CUT_OFF' })).toBe(
      'Free to leave now — nothing is taken',
    );
    expect(leavingSheetBody({ kind: 'BEFORE_THE_CUT_OFF', letsAHoldGo: true })).toEqual([
      'Nothing is taken: the hold on your card is let go.',
      'Your seat is offered to others.',
      'On your record only if the game is then called off.',
    ]);
    expect(leftToast('BEFORE_THE_CUT_OFF')).toBe('You left the game. Nothing was taken.');
  });

  it('lets no hold go on a share only checked, which holds nothing yet', () => {
    expect(leavingSheetBody({ kind: 'BEFORE_THE_CUT_OFF', letsAHoldGo: false })).toEqual([
      'Nothing is taken.',
      'Your seat is offered to others.',
      'On your record only if the game is then called off.',
    ]);
  });

  it('keeps today’s shape after the cut-off, with no figure — and never an estimate', () => {
    expect(leavingLine({ kind: 'AFTER_THE_CUT_OFF' })).toBe(
      'Refunded only if someone takes your seat',
    );
    expect(leavingSheetBody({ kind: 'AFTER_THE_CUT_OFF' })).toEqual([
      'Your seat is offered to others.',
      'If someone takes it, you get your share back less what was kept on your payment; if nobody does, you won’t.',
      'On your record if nobody takes it.',
    ]);
    expect(leftToast('AFTER_THE_CUT_OFF')).toBe(
      'You left the game. Your seat is offered to others.',
    );
  });

  it('says nobody has paid while the club decides, and the yes is withdrawn', () => {
    expect(leavingLine({ kind: 'WHILE_WAITING_FOR_THE_CLUB' })).toBe('Nobody has paid yet');
    expect(leavingSheetBody({ kind: 'WHILE_WAITING_FOR_THE_CLUB' })).toEqual([
      'Nobody has paid yet.',
      'Leaving withdraws your yes.',
    ]);
    expect(leftToast('WHILE_WAITING_FOR_THE_CLUB')).toBe(
      'You left the game. Your yes is withdrawn.',
    );
  });
});
