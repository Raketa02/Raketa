import { setDeviceZone } from '@/test-support/deviceZone';

import type { BookedGame, HomeGame } from '../domain/home';

import { homeCardLabel, moneyRow, moneyWords, statusSubline, whereAside } from './homePresentation';

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
});

describe('statusSubline — the details’ second line', () => {
  it('is the sport and the status, lower case: Padel · booked', () => {
    expect(statusSubline('padel', 'BOOKED')).toBe('Padel · booked');
    expect(statusSubline('tennis', 'WAITING_FOR_THE_CLUB')).toBe('Tennis · waiting for the club');
  });
});

describe('whereAside — the court and how far it is (details 8)', () => {
  it('is the court, with the distance when the reader has a Location area', () => {
    expect(whereAside('Court 2', 3.1)).toBe('Court 2 · 3,1 km');
    expect(whereAside('Court 2', undefined)).toBe('Court 2');
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

  it('is refunded, or nobody paid, once the game is called off', () => {
    expect(moneyRow(booked({ status: 'CALLED_OFF' }), BEFORE)).toEqual({
      label: 'Refunded',
      value: '28 zł',
    });
    expect(
      moneyRow(booked({ status: 'CALLED_OFF', money: { shareGrosze: 2800, paid: false } }), BEFORE),
    ).toEqual({ label: 'Your share', value: '28 zł', aside: 'nobody paid' });
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
        day: 'Saturday',
        money: 'Paid · 30 zł · free to leave until Fri 16:00',
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
