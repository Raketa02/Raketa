import { setDeviceZone } from '@/test-support/deviceZone';

import type { BookedGame, HomeGame } from '../domain/home';

import {
  homeCardLabel,
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

beforeAll(() => setDeviceZone('America/New_York'));

describe('moneyWords — the line under a Home card (the mechanics §14.1)', () => {
  it('reads Paid with the share, and free to leave until the cut-off on the club’s clock', () => {
    expect(
      moneyWords({ kind: 'booked', shareGrosze: 3000, paid: true, freeToLeaveUntil: CUT_OFF }),
    ).toBe('Paid · 30 zł · free to leave until Fri 16:00');
    expect(moneyWords({ kind: 'booked', shareGrosze: 2750, paid: true })).toBe('Paid · 27,50 zł');
  });

  it('names the club a game waits for, or the club when the read no longer names it', () => {
    expect(moneyWords({ kind: 'waiting', club: 'Bonarka Arena' })).toBe(
      'Nobody pays until Bonarka Arena confirms',
    );
    expect(moneyWords({ kind: 'waiting' })).toBe('Nobody pays until the club confirms');
  });

  it('counts the seats open, before the cut-off and after it', () => {
    expect(moneyWords({ kind: 'seatOpen', seats: 1, fillsBy: CUT_OFF })).toBe(
      '1 seat open · fills by Fri 16:00 or the game is off and everyone is refunded',
    );
    expect(moneyWords({ kind: 'seatOpen', seats: 2 })).toBe(
      '2 seats open · offered to others · the game goes ahead',
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
        reason: 'SHORT_AT_THE_CUT_OFF',
        club: 'Bonarka Arena',
        refundedGrosze: 3000,
      }),
    ).toBe('A seat was still empty at the cut-off · Refunded 30 zł');
    expect(moneyWords({ kind: 'calledOff', reason: 'REFUSED', club: 'Kazimierz Padel' })).toBe(
      'Kazimierz Padel couldn’t take it · Nobody paid',
    );
    expect(moneyWords({ kind: 'calledOff', reason: 'NO_ANSWER' })).toBe(
      'The club didn’t answer in time · Nobody paid',
    );
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
});

describe('moneySpoken — the line aloud, its dots commas', () => {
  it('says each clause the line draws, and nothing it does not', () => {
    expect(
      moneySpoken({ kind: 'booked', shareGrosze: 3000, paid: true, freeToLeaveUntil: CUT_OFF }),
    ).toBe('Paid, 30 zł, free to leave until Fri 16:00');
    expect(moneySpoken({ kind: 'seatOpen', seats: 1 })).toBe(
      '1 seat open, offered to others, the game goes ahead',
    );
  });
});

describe('sportWords — a card’s sport word', () => {
  it('says the kind only when the game is a friendly', () => {
    expect(sportWords('padel', 'competitive')).toBe('Padel');
    expect(sportWords('padel', 'forFun')).toBe('Padel · For fun');
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
  money: { shareGrosze: 2800, paid: true, freeToLeaveUntil: CUT_OFF },
  showsForecast: true,
  ...extra,
});

const bookedPaid = { shareGrosze: 2800, paid: true } as const;

describe('moneyRow — the details’ money row (A4.1)', () => {
  it('is PAID · 28 zł · your share · to the club, free to leave until the cut-off while ahead', () => {
    expect(moneyRow(booked(), BEFORE)).toEqual({
      label: 'Paid',
      value: '28 zł',
      aside: 'your share · to the club · free to leave until Fri 16:00',
    });
    expect(moneyRow(booked(), Date.parse(CUT_OFF))).toEqual({
      label: 'Paid',
      value: '28 zł',
      aside: 'your share · to the club',
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
      aside: 'nobody pays until Bonarka Arena confirms',
    });
  });

  it('is what came back, or nobody paid, once the game is called off', () => {
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
    ).toEqual({ label: 'Your share', value: '28 zł', aside: 'nobody paid' });
  });

  it('says the seat open and when it must fill, on a game a player left (§14.1)', () => {
    const open = booked({ status: 'SEAT_OPEN', openSeats: 1 });
    expect(moneyRow(open, BEFORE)).toEqual({
      label: 'Paid',
      value: '28 zł',
      aside: '1 seat open · fills by Fri 16:00 or the game is off and everyone is refunded',
    });
    expect(moneyRow(open, Date.parse(CUT_OFF))).toEqual({
      label: 'Paid',
      value: '28 zł',
      aside: '1 seat open · offered to others · the game goes ahead',
    });
  });

  it('says why a game is off beside what came back', () => {
    expect(
      moneyRow(
        booked({
          status: 'CALLED_OFF',
          calledOffReason: 'SHORT_AT_THE_CUT_OFF',
          money: { shareGrosze: 2800, paid: true, refundedGrosze: 2800 },
        }),
        BEFORE,
      ),
    ).toEqual({
      label: 'Refunded',
      value: '28 zł',
      aside: 'A seat was still empty at the cut-off',
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
      aside: 'Bonarka Arena couldn’t take it · nobody paid',
    });
  });

  it('says a seat was empty on a game that started short', () => {
    expect(
      moneyRow(
        booked({ status: 'UNCOUNTED', uncountedReason: 'SEAT_EMPTY', money: bookedPaid }),
        BEFORE,
      ),
    ).toEqual({ label: 'Paid', value: '28 zł', aside: 'A seat was empty · no Level moved' });
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
      aside: 'fills by Fri 16:00',
    });
    expect(moneyRow(rescue(false), BEFORE)).toEqual({
      label: 'Your share',
      value: '27 zł',
      aside: 'offered until the start',
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
    money: { shareGrosze: 3000, paid: true, freeToLeaveUntil: CUT_OFF },
  };

  it('says the status, new, the sport, where, when, the money and the chat — commas for the dots', () => {
    expect(
      homeCardLabel({
        game,
        fresh: true,
        day: { kind: 'weekday', weekday: 6 },
        money: { kind: 'booked', shareGrosze: 3000, paid: true, freeToLeaveUntil: CUT_OFF },
        chat: true,
      }),
    ).toBe(
      'Booked, new. Padel. Bonarka Arena, Court 2. Saturday, 16:00 until 17:00. Paid, 30 zł, free to leave until Fri 16:00. Chat open.',
    );
  });

  it('leaves out what the card does not draw', () => {
    expect(
      homeCardLabel({
        game: { ...game, status: 'COUNTED' },
        fresh: false,
        day: undefined,
        money: undefined,
        chat: false,
      }),
    ).toBe('Counted. Padel. Bonarka Arena, Court 2. 16:00 until 17:00.');
  });
});
