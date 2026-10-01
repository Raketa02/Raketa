import type { DeckPerson } from './deck';
import {
  ENDED_HOME_SHELF_LIFE_MS,
  chatIsOpen,
  isNew,
  moneyLineOf,
  onHome,
  openedFrom,
  openedToKeep,
  resultActOf,
  type HomeGame,
} from './home';
import type { HomeStatus } from './vocabulary';

const STARTS_AT = '2026-10-03T14:00:00Z';
const BEFORE_CUT_OFF = Date.parse('2026-10-02T10:00:00Z');
const CUT_OFF = '2026-10-02T14:00:00Z';

const person = (playerId: string, extra: Partial<DeckPerson> = {}): DeckPerson => ({
  playerId,
  isYou: false,
  isIn: false,
  paid: true,
  ...extra,
});

function game(extra: Partial<HomeGame> = {}): HomeGame {
  return {
    bookingId: 'booking-1',
    gameId: 'game-1',
    groupId: 'group-1',
    sport: 'padel',
    kind: 'competitive',
    status: 'BOOKED',
    needsYou: false,
    startsAt: STARTS_AT,
    club: { id: 'club-1', name: 'Bonarka Arena' },
    courtName: 'Court 2',
    sides: {
      yours: [person('me', { isYou: true }), person('piotr')],
      theirs: [person('ines'), person('bartek')],
    },
    money: { shareGrosze: 3000, paid: true, freeToLeaveUntil: CUT_OFF },
    ...extra,
  };
}

describe('moneyLineOf — the line under a Home card (the mechanics §14.1)', () => {
  it('reads Paid with the share and free to leave until the cut-off while it is ahead', () => {
    expect(moneyLineOf(game(), 4, BEFORE_CUT_OFF)).toEqual({
      kind: 'booked',
      shareGrosze: 3000,
      paid: true,
      freeToLeaveUntil: CUT_OFF,
    });
  });

  it('drops the free-to-leave clause at the cut-off itself — the line switches by itself', () => {
    expect(moneyLineOf(game(), 4, Date.parse(CUT_OFF))).toEqual({
      kind: 'booked',
      shareGrosze: 3000,
      paid: true,
    });
  });

  it('has no free-to-leave clause once the read says the cut-off has passed', () => {
    const late = game({ money: { shareGrosze: 3000, paid: true } });
    expect(moneyLineOf(late, 4, BEFORE_CUT_OFF)).toEqual({
      kind: 'booked',
      shareGrosze: 3000,
      paid: true,
    });
  });

  it('waits for the club by name, and nobody pays', () => {
    const waiting = game({
      status: 'WAITING_FOR_THE_CLUB',
      money: { shareGrosze: 3000, paid: false },
    });
    expect(moneyLineOf(waiting, 4, BEFORE_CUT_OFF)).toEqual({
      kind: 'waiting',
      club: 'Bonarka Arena',
    });
  });

  it('counts the open seats off the court, and fills by the cut-off while it is ahead', () => {
    const open = game({
      status: 'SEAT_OPEN',
      sides: { yours: [person('me', { isYou: true }), person('piotr')], theirs: [person('ines')] },
    });
    expect(moneyLineOf(open, 4, BEFORE_CUT_OFF)).toEqual({
      kind: 'seatOpen',
      seats: 1,
      fillsBy: CUT_OFF,
    });
    expect(moneyLineOf(open, 4, Date.parse(CUT_OFF))).toEqual({ kind: 'seatOpen', seats: 1 });
  });

  it('says one seat at the least while a seat is open, whatever the sides still hold', () => {
    expect(moneyLineOf(game({ status: 'SEAT_OPEN' }), 4, BEFORE_CUT_OFF)).toMatchObject({
      seats: 1,
    });
  });

  it('is refunded when the shares were taken and nobody paid when they were not', () => {
    expect(moneyLineOf(game({ status: 'CALLED_OFF' }), 4, BEFORE_CUT_OFF)).toEqual({
      kind: 'calledOff',
      refundedGrosze: 3000,
    });
    const unpaid = game({ status: 'CALLED_OFF', money: { shareGrosze: 3000, paid: false } });
    expect(moneyLineOf(unpaid, 4, BEFORE_CUT_OFF)).toEqual({ kind: 'calledOff' });
  });

  it.each<HomeStatus>([
    'NEEDS_RESULT',
    'CONFIRM_THE_RESULT',
    'COUNTED',
    'UNCOUNTED',
    'NEVER_PLAYED',
  ])('draws no money line on %s — the result states are as today', (status) => {
    expect(moneyLineOf(game({ status }), 4, BEFORE_CUT_OFF)).toBeUndefined();
  });
});

describe('onHome — how long an ended game keeps its card', () => {
  const hourEnds = Date.parse(STARTS_AT) + 3_600_000;

  it.each<HomeStatus>([
    'WAITING_FOR_THE_CLUB',
    'BOOKED',
    'SEAT_OPEN',
    'NEEDS_RESULT',
    'CONFIRM_THE_RESULT',
  ])('keeps a live %s card whatever the clock says', (status) => {
    expect(onHome(game({ status }), hourEnds + 30 * ENDED_HOME_SHELF_LIFE_MS)).toBe(true);
  });

  it.each<HomeStatus>(['COUNTED', 'UNCOUNTED', 'NEVER_PLAYED', 'CALLED_OFF'])(
    'keeps an ended %s card for a day after its hour, and not a moment more',
    (status) => {
      expect(onHome(game({ status }), hourEnds + ENDED_HOME_SHELF_LIFE_MS - 1)).toBe(true);
      expect(onHome(game({ status }), hourEnds + ENDED_HOME_SHELF_LIFE_MS)).toBe(false);
    },
  );

  it('keeps a game called off before its hour until a day after the hour it was for', () => {
    expect(onHome(game({ status: 'CALLED_OFF' }), BEFORE_CUT_OFF)).toBe(true);
  });
});

describe('isNew — marked until opened (the mechanics §11.4)', () => {
  it('is new while its details have never been opened on this phone', () => {
    expect(isNew(game(), new Set())).toBe(true);
    expect(isNew(game(), new Set(['booking-1']))).toBe(false);
  });

  it('is new only while the game is still ahead of its result', () => {
    expect(isNew(game({ status: 'WAITING_FOR_THE_CLUB' }), new Set())).toBe(true);
    expect(isNew(game({ status: 'SEAT_OPEN' }), new Set())).toBe(true);
    expect(isNew(game({ status: 'NEEDS_RESULT' }), new Set())).toBe(false);
    expect(isNew(game({ status: 'CALLED_OFF' }), new Set())).toBe(false);
  });

  it('marks nothing new until the phone has said what was opened', () => {
    expect(isNew(game(), undefined)).toBe(false);
  });
});

describe('openedFrom / openedToKeep — what the phone keeps', () => {
  it('reads the kept list, and nothing for a value it cannot read', () => {
    expect(openedFrom('["a","b"]')).toEqual(['a', 'b']);
    expect(openedFrom(undefined)).toEqual([]);
    expect(openedFrom('not json')).toEqual([]);
    expect(openedFrom('{"a":1}')).toEqual([]);
    expect(openedFrom('["a",2]')).toEqual(['a']);
  });

  it('keeps the game just opened and only the games Home still holds', () => {
    expect(openedToKeep(['gone', 'kept'], 'new', ['kept', 'new', 'other'])).toEqual([
      'kept',
      'new',
    ]);
  });

  it('keeps everything it had when Home has not been read', () => {
    expect(openedToKeep(['a'], 'b', undefined)).toEqual(['a', 'b']);
  });

  it('does not keep one game twice', () => {
    expect(openedToKeep(['a'], 'a', ['a'])).toEqual(['a']);
  });
});

describe('chatIsOpen — the Chat door while you are in the game and it is not over', () => {
  it.each<[HomeStatus, boolean]>([
    ['WAITING_FOR_THE_CLUB', false],
    ['BOOKED', true],
    ['SEAT_OPEN', true],
    ['NEEDS_RESULT', true],
    ['CONFIRM_THE_RESULT', true],
    ['COUNTED', false],
    ['UNCOUNTED', false],
    ['NEVER_PLAYED', false],
    ['CALLED_OFF', false],
  ])('%s → %s', (status, open) => {
    expect(chatIsOpen(status)).toBe(open);
  });
});

describe('resultActOf — the result, reached from the details as today', () => {
  it('asks for the result once the hour has come, and its answer once a score is told', () => {
    expect(resultActOf('NEEDS_RESULT')).toBe('we-played');
    expect(resultActOf('CONFIRM_THE_RESULT')).toBe('confirm');
  });

  it.each<HomeStatus>([
    'WAITING_FOR_THE_CLUB',
    'BOOKED',
    'SEAT_OPEN',
    'COUNTED',
    'UNCOUNTED',
    'NEVER_PLAYED',
    'CALLED_OFF',
  ])('offers nothing on %s', (status) => {
    expect(resultActOf(status)).toBeUndefined();
  });
});
