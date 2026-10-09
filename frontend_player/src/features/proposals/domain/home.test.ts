import type { DeckPerson } from './deck';
import {
  ENDED_HOME_SHELF_LIFE_MS,
  answerByAhead,
  chatIsOpen,
  completesTheRescue,
  courtIsGiven,
  isNew,
  lineCanRunOut,
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
    openSeats: 0,
    sides: {
      yours: [person('me', { isYou: true }), person('piotr')],
      theirs: [person('ines'), person('bartek')],
    },
    money: { shareGrosze: 3000, paid: true, freeToLeaveUntil: CUT_OFF, backIfYouLeaveGrosze: 2855 },
    ...extra,
  };
}

describe('moneyLineOf — the line under a Home card (the mechanics §14.1)', () => {
  it('reads Paid with the share, and what comes back if you leave by the cut-off while it is ahead (Q99)', () => {
    expect(moneyLineOf(game(), BEFORE_CUT_OFF)).toEqual({
      kind: 'booked',
      shareGrosze: 3000,
      paid: true,
      backIfYouLeave: { grosze: 2855, by: CUT_OFF },
    });
  });

  it('drops the clause at the cut-off itself — the line switches by itself', () => {
    expect(moneyLineOf(game(), Date.parse(CUT_OFF))).toEqual({
      kind: 'booked',
      shareGrosze: 3000,
      paid: true,
    });
  });

  it('has no clause once the read says the cut-off has passed', () => {
    const late = game({ money: { shareGrosze: 3000, paid: true } });
    expect(moneyLineOf(late, BEFORE_CUT_OFF)).toEqual({
      kind: 'booked',
      shareGrosze: 3000,
      paid: true,
    });
  });

  /**
   * **The figure is the server's** (Q99): the card fee kept back is the payments' estimate, so the
   * phone never works one out — with no figure, as from a server older than it, there is no clause,
   * and never *free to leave* in its place.
   */
  it('leaves the clause out with the figure missing, though the cut-off is ahead', () => {
    const older = game({ money: { shareGrosze: 3000, paid: true, freeToLeaveUntil: CUT_OFF } });
    expect(moneyLineOf(older, BEFORE_CUT_OFF)).toEqual({
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
    expect(moneyLineOf(waiting, BEFORE_CUT_OFF)).toEqual({
      kind: 'waiting',
      club: 'Bonarka Arena',
    });
  });

  /**
   * **When the club answers** (Q98; the screens A8): the deadline the desk is given, while it is
   * ahead of `now` — and the hour alone when it falls on the read's day, on the club's calendar.
   */
  describe('the club’s deadline to answer', () => {
    /** Thursday 1 October, 10:00 in Warsaw — the read. */
    const READ = Date.parse('2026-10-01T08:00:00Z');
    /** 11:00 the same day. */
    const ELEVEN = '2026-10-01T09:00:00Z';
    const waiting = (extra: Partial<HomeGame> = {}) =>
      game({
        status: 'WAITING_FOR_THE_CLUB',
        money: { shareGrosze: 3000, paid: false },
        answerBy: ELEVEN,
        ...extra,
      });

    it('says when the club answers while the deadline is ahead', () => {
      expect(moneyLineOf(waiting(), READ)).toEqual({
        kind: 'waiting',
        club: 'Bonarka Arena',
        answerBy: { at: ELEVEN, today: true },
      });
    });

    it('drops it at the deadline itself — the line reads as it did before', () => {
      expect(moneyLineOf(waiting(), Date.parse(ELEVEN))).toEqual({
        kind: 'waiting',
        club: 'Bonarka Arena',
      });
      expect(moneyLineOf(waiting(), Date.parse(ELEVEN) + 60_000)).toEqual({
        kind: 'waiting',
        club: 'Bonarka Arena',
      });
    });

    it('says it of the club when the read no longer names it', () => {
      expect(moneyLineOf(waiting({ club: { id: 'club-1' } }), READ)).toEqual({
        kind: 'waiting',
        answerBy: { at: ELEVEN, today: true },
      });
    });

    it('is today by the club’s calendar, and another day past its midnight', () => {
      // 23:30 and 00:15 in Warsaw: the second is Friday, though it is still Thursday in UTC.
      expect(answerByAhead({ answerBy: '2026-10-01T21:30:00Z' }, READ)).toEqual({
        at: '2026-10-01T21:30:00Z',
        today: true,
      });
      expect(answerByAhead({ answerBy: '2026-10-01T22:15:00Z' }, READ)).toEqual({
        at: '2026-10-01T22:15:00Z',
        today: false,
      });
    });

    it('is nothing for a value that is not an instant', () => {
      expect(answerByAhead({ answerBy: 'soon' }, READ)).toBeUndefined();
    });
  });

  it('counts the open seats the read says, and fills by the cut-off while it is ahead', () => {
    const open = game({ status: 'SEAT_OPEN', openSeats: 2 });
    expect(moneyLineOf(open, BEFORE_CUT_OFF)).toEqual({
      kind: 'seatOpen',
      seats: 2,
      fillsBy: CUT_OFF,
    });
    expect(moneyLineOf(open, Date.parse(CUT_OFF))).toEqual({ kind: 'seatOpen', seats: 2 });
  });

  it('says why a game was called off, and what came back', () => {
    const short = game({
      status: 'CALLED_OFF',
      calledOffReason: 'SHORT_AT_THE_CUT_OFF',
      money: { shareGrosze: 3000, paid: true, refundedGrosze: 3000 },
    });
    expect(moneyLineOf(short, BEFORE_CUT_OFF)).toEqual({
      kind: 'calledOff',
      reason: 'SHORT_AT_THE_CUT_OFF',
      club: 'Bonarka Arena',
      refundedGrosze: 3000,
    });
    const refused = game({
      status: 'CALLED_OFF',
      calledOffReason: 'REFUSED',
      money: { shareGrosze: 3000, paid: false },
    });
    expect(moneyLineOf(refused, BEFORE_CUT_OFF)).toEqual({
      kind: 'calledOff',
      reason: 'REFUSED',
      club: 'Bonarka Arena',
    });
  });

  it('says nobody paid when nothing came back, whatever the reason', () => {
    const unpaid = game({ status: 'CALLED_OFF', money: { shareGrosze: 3000, paid: false } });
    expect(moneyLineOf(unpaid, BEFORE_CUT_OFF)).toEqual({
      kind: 'calledOff',
      club: 'Bonarka Arena',
    });
  });

  /** The club's cancel (#547): why, as the club gave it, and the full refund. */
  it('carries the club’s reason for a game it cancelled', () => {
    const cancelled = game({
      status: 'CALLED_OFF',
      calledOffReason: 'CANCELLED_BY_THE_CLUB',
      clubCancelReason: 'WEATHER',
      money: { shareGrosze: 3000, paid: true, refundedGrosze: 3000 },
    });
    expect(moneyLineOf(cancelled, BEFORE_CUT_OFF)).toEqual({
      kind: 'calledOff',
      reason: 'CANCELLED_BY_THE_CLUB',
      clubCancelReason: 'WEATHER',
      club: 'Bonarka Arena',
      refundedGrosze: 3000,
    });
  });

  /**
   * **Somebody didn't come** (#560): uncounted, and the line says which of the two it is to this
   * reader — marked themselves with a day to answer (the read's *needs you*), or anybody else.
   */
  it('says somebody didn’t come, and to the player marked, that they were', () => {
    const marked = game({ status: 'UNCOUNTED', uncountedReason: 'NO_SHOW', needsYou: true });
    const other = game({ status: 'UNCOUNTED', uncountedReason: 'NO_SHOW' });
    expect(moneyLineOf(marked, BEFORE_CUT_OFF)).toEqual({ kind: 'noShow', yours: true });
    expect(moneyLineOf(other, BEFORE_CUT_OFF)).toEqual({ kind: 'noShow', yours: false });
  });

  it('says a seat was empty on a game uncounted for it (§14.1)', () => {
    const short = game({ status: 'UNCOUNTED', uncountedReason: 'SEAT_EMPTY' });
    expect(moneyLineOf(short, BEFORE_CUT_OFF)).toEqual({ kind: 'seatEmpty' });
  });

  it.each<HomeStatus>([
    'NEEDS_RESULT',
    'CONFIRM_THE_RESULT',
    'COUNTED',
    'UNCOUNTED',
    'NEVER_PLAYED',
  ])('draws no money line on %s — the result states are as today', (status) => {
    expect(moneyLineOf(game({ status }), BEFORE_CUT_OFF)).toBeUndefined();
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

describe('lineCanRunOut — a clause that leaves the line by itself', () => {
  it('runs out while the cut-off or the club’s deadline is there to pass', () => {
    expect(lineCanRunOut(game())).toBe(true);
    const waiting = game({
      status: 'WAITING_FOR_THE_CLUB',
      money: { shareGrosze: 3000, paid: false },
    });
    expect(lineCanRunOut({ ...waiting, answerBy: '2026-10-01T09:00:00Z' })).toBe(true);
    expect(lineCanRunOut(waiting)).toBe(false);
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

describe('chatIsOpen — the room lives its own life once booked, and closes as today (§14.3)', () => {
  it.each<[HomeStatus, boolean]>([
    ['WAITING_FOR_THE_CLUB', false],
    ['BOOKED', true],
    ['SEAT_OPEN', true],
    ['NEEDS_RESULT', true],
    ['CONFIRM_THE_RESULT', true],
    // 48 hours after *we played*: a counted game's room can outlive the result by a day or two.
    ['COUNTED', true],
    ['UNCOUNTED', true],
    ['NEVER_PLAYED', true],
    ['CALLED_OFF', false],
  ])('%s → %s', (status, open) => {
    expect(chatIsOpen(status)).toBe(open);
  });
});

describe('courtIsGiven — a court number once the club has said yes (A4.2)', () => {
  it.each<[HomeStatus, boolean]>([
    ['WAITING_FOR_THE_CLUB', false],
    ['BOOKED', true],
    ['SEAT_OPEN', true],
    ['NEEDS_RESULT', true],
    ['CALLED_OFF', true],
  ])('%s → %s', (status, given) => {
    expect(courtIsGiven(status)).toBe(given);
  });
});

describe('resultActOf — the result, reached from the details as today', () => {
  it('asks for the result once the hour has come, and its answer once a score is told', () => {
    expect(resultActOf(game({ status: 'NEEDS_RESULT' }))).toBe('we-played');
    expect(resultActOf(game({ status: 'CONFIRM_THE_RESULT' }))).toBe('confirm');
  });

  /** The marked player's day to dispute it (#560) — the read's *needs you*, and theirs alone. */
  it('opens the dispute to the player marked as not coming, while it needs them', () => {
    const noShow = { status: 'UNCOUNTED', uncountedReason: 'NO_SHOW' } as const;
    expect(resultActOf(game({ ...noShow, needsYou: true }))).toBe('dispute');
    expect(resultActOf(game({ ...noShow, needsYou: false }))).toBeUndefined();
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
    expect(resultActOf(game({ status }))).toBeUndefined();
  });
});

describe('completesTheRescue — You complete it on a rescue seen from outside', () => {
  const offer = { deadline: CUT_OFF, fillsByTheCutOff: true };

  it('is the last open seat, offered to the reader', () => {
    expect(completesTheRescue({ rescue: offer, openSeats: 1 })).toBe(true);
    expect(completesTheRescue({ rescue: offer, openSeats: 2 })).toBe(false);
    expect(completesTheRescue({ openSeats: 1 })).toBe(false);
  });
});
