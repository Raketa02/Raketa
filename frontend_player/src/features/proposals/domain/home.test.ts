import type { DeckPerson } from './deck';
import {
  ENDED_HOME_SHELF_LIFE_MS,
  answerByAhead,
  chatIsOpen,
  completesTheRescue,
  courtIsGiven,
  isFillingAgain,
  isNew,
  leavingAt,
  lineCanRunOut,
  moneyLineOf,
  onHome,
  openedFrom,
  openedToKeep,
  paymentOf,
  resultActOf,
  shareAt,
  type BookedMoney,
  type HomeGame,
} from './home';
import type { HomeStatus } from './vocabulary';

const STARTS_AT = '2026-10-03T14:00:00Z';
const BEFORE_CUT_OFF = Date.parse('2026-10-02T10:00:00Z');
const CUT_OFF = '2026-10-02T14:00:00Z';

/** Held on the card until the cut-off, which is still ahead at the read (Q113). */
const HELD: BookedMoney = {
  shareGrosze: 3000,
  paid: false,
  shareState: 'HELD',
  takenAt: CUT_OFF,
  freeToLeaveUntil: CUT_OFF,
};

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
    money: HELD,
    ...extra,
  };
}

describe('moneyLineOf — the line under a Home card (the mechanics §14.1)', () => {
  /**
   * **Held until the cut-off, taken at it** (Q113): the share alone with *free to leave until* the
   * club's cut-off, whether it is held yet or only checked — then *Paid* once it is taken.
   */
  it('reads the share, free to leave until the cut-off, while the share is held', () => {
    expect(moneyLineOf(game(), BEFORE_CUT_OFF)).toEqual({
      kind: 'booked',
      shareGrosze: 3000,
      paid: false,
      freeToLeaveUntil: CUT_OFF,
    });
  });

  it('reads the same while the reader’s share is only checked, to be held later', () => {
    const checked = game({
      money: { ...HELD, shareState: 'CHECKED', heldFrom: '2026-09-28T14:00:00Z' },
    });
    expect(moneyLineOf(checked, Date.parse('2026-09-27T10:00:00Z'))).toEqual({
      kind: 'booked',
      shareGrosze: 3000,
      paid: false,
      freeToLeaveUntil: CUT_OFF,
    });
  });

  it('reads Paid from the cut-off itself — the share is taken there, and the line switches by itself', () => {
    expect(moneyLineOf(game(), Date.parse(CUT_OFF))).toEqual({
      kind: 'booked',
      shareGrosze: 3000,
      paid: true,
    });
  });

  it('reads Paid once the read says the share was taken', () => {
    const taken = game({
      money: { shareGrosze: 3000, paid: true, shareState: 'TAKEN', takenAt: CUT_OFF },
    });
    expect(moneyLineOf(taken, Date.parse(CUT_OFF) + 60_000)).toEqual({
      kind: 'booked',
      shareGrosze: 3000,
      paid: true,
    });
  });

  it('has no clause once the read says the cut-off has passed, though nothing says taken', () => {
    const older = game({ money: { shareGrosze: 3000, paid: false } });
    expect(moneyLineOf(older, BEFORE_CUT_OFF)).toEqual({
      kind: 'booked',
      shareGrosze: 3000,
      paid: false,
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

  /**
   * **A full game gone back to filling** (#624, Q106): *Seat open*, the seats nobody is In on, and
   * how it is booked once full again — the club asked again, or at once. Nobody paid, so no cut-off.
   */
  describe('a full game gone back to filling', () => {
    const filling = (clubConfirms: boolean) =>
      game({
        status: 'SEAT_OPEN',
        openSeats: 1,
        gameId: undefined,
        courtName: undefined,
        club: { id: 'club-1', name: 'Kazimierz Padel' },
        money: { shareGrosze: 2500, paid: false },
        fillingAgain: { clubConfirms },
      });

    it('is a seat open, the club asked again when it is full, nobody paid', () => {
      expect(moneyLineOf(filling(true), BEFORE_CUT_OFF)).toEqual({
        kind: 'fillingAgain',
        seats: 1,
        club: 'Kazimierz Padel',
        clubConfirms: true,
      });
    });

    it('books when it is full at a club that books at once', () => {
      expect(moneyLineOf(filling(false), BEFORE_CUT_OFF)).toEqual({
        kind: 'fillingAgain',
        seats: 1,
        club: 'Kazimierz Padel',
        clubConfirms: false,
      });
    });

    it('says it of the club when the read no longer names it', () => {
      expect(moneyLineOf({ ...filling(true), club: { id: 'club-1' } }, BEFORE_CUT_OFF)).toEqual({
        kind: 'fillingAgain',
        seats: 1,
        clubConfirms: true,
      });
    });

    it('is called off with why once its last moment to book passes, or its court goes', () => {
      for (const reason of ['BOOK_BY_PASSED', 'COURT_HOUR_LOST'] as const) {
        expect(
          moneyLineOf(
            { ...filling(true), status: 'CALLED_OFF', calledOffReason: reason, openSeats: 0 },
            BEFORE_CUT_OFF,
          ),
        ).toEqual({ kind: 'calledOff', reason, club: 'Kazimierz Padel' });
      }
    });
  });

  /**
   * **Waiting for one payment** (#625, #626; Q111): one player's share was refused, and their time
   * to pay runs. Everybody reads until when, and never whose; the payer reads their own time.
   */
  describe('a full game waiting for one payment', () => {
    /** Tuesday 6 October, 14:10 in Warsaw — the read; the time runs to 14:40. */
    const READ = Date.parse('2026-10-06T12:10:00Z');
    const TWENTY_TO_THREE = '2026-10-06T12:40:00Z';
    const waiting = (extra: Partial<HomeGame> = {}) =>
      game({
        status: 'WAITING_FOR_A_PAYMENT',
        gameId: undefined,
        courtName: undefined,
        money: { shareGrosze: 4000, paid: false },
        paymentDueBy: TWENTY_TO_THREE,
        ...extra,
      });

    it('says until when, while the time is ahead', () => {
      expect(moneyLineOf(waiting(), READ)).toEqual({
        kind: 'paymentAwaited',
        until: { at: TWENTY_TO_THREE, today: true },
      });
    });

    it('drops the time at the deadline itself — the line switches by itself', () => {
      expect(moneyLineOf(waiting(), Date.parse(TWENTY_TO_THREE))).toEqual({
        kind: 'paymentAwaited',
      });
    });

    it('is the payer’s own time to them — Confirm your payment by … — while it runs', () => {
      const yours = waiting({ yourPaymentDueBy: TWENTY_TO_THREE });
      expect(moneyLineOf(yours, READ)).toEqual({
        kind: 'yourPayment',
        by: { at: TWENTY_TO_THREE, today: true },
      });
      expect(moneyLineOf(yours, Date.parse(TWENTY_TO_THREE))).toEqual({
        kind: 'paymentAwaited',
      });
    });

    /** A leave in the wait falls the game back, and the payer's time runs on (#625). */
    it('names the payer’s time on a game gone back to filling meanwhile', () => {
      const fellBack = game({
        status: 'SEAT_OPEN',
        openSeats: 1,
        money: { shareGrosze: 4000, paid: false },
        fillingAgain: { clubConfirms: false },
        yourPaymentDueBy: TWENTY_TO_THREE,
      });
      expect(moneyLineOf(fellBack, READ)).toEqual({
        kind: 'yourPayment',
        by: { at: TWENTY_TO_THREE, today: true },
      });
      expect(moneyLineOf(fellBack, Date.parse(TWENTY_TO_THREE))).toEqual({
        kind: 'fillingAgain',
        seats: 1,
        club: 'Bonarka Arena',
        clubConfirms: false,
      });
    });

    it('is called off with why when the payment did not come in before its last moment to book', () => {
      expect(
        moneyLineOf(
          waiting({ status: 'CALLED_OFF', calledOffReason: 'PAYMENT_NOT_IN_TIME' }),
          READ,
        ),
      ).toEqual({ kind: 'calledOff', reason: 'PAYMENT_NOT_IN_TIME', club: 'Bonarka Arena' });
    });
  });

  it('says why a game was called off, and what came back', () => {
    const short = game({
      status: 'CALLED_OFF',
      calledOffReason: 'SHORT_AT_THE_CUT_OFF',
      money: { shareGrosze: 3000, paid: false },
    });
    expect(moneyLineOf(short, BEFORE_CUT_OFF)).toEqual({
      kind: 'calledOff',
      reason: 'SHORT_AT_THE_CUT_OFF',
      club: 'Bonarka Arena',
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
    'WAITING_FOR_A_PAYMENT',
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

  it('keeps a full game gone back to filling, which is live (Q106)', () => {
    const filling = game({ status: 'SEAT_OPEN', fillingAgain: { clubConfirms: true } });
    expect(onHome(filling, hourEnds + 30 * ENDED_HOME_SHELF_LIFE_MS)).toBe(true);
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

  it('runs out while a checked share is still to be held — the details’ row switches then', () => {
    const checked = game({
      money: { shareGrosze: 3000, paid: false, shareState: 'CHECKED', heldFrom: CUT_OFF },
    });
    expect(lineCanRunOut(checked)).toBe(true);
    expect(lineCanRunOut(game({ money: { shareGrosze: 3000, paid: true } }))).toBe(false);
  });

  it('runs out while a time to pay is there to pass — everybody’s, or the payer’s own', () => {
    const paying = game({
      status: 'WAITING_FOR_A_PAYMENT',
      money: { shareGrosze: 4000, paid: false },
    });
    expect(lineCanRunOut(paying)).toBe(false);
    expect(lineCanRunOut({ ...paying, paymentDueBy: '2026-10-06T12:40:00Z' })).toBe(true);
    const fellBack = game({
      status: 'SEAT_OPEN',
      money: { shareGrosze: 4000, paid: false },
      fillingAgain: { clubConfirms: false },
    });
    expect(lineCanRunOut({ ...fellBack, yourPaymentDueBy: '2026-10-06T12:40:00Z' })).toBe(true);
  });
});

/**
 * **Where the reader's share stands, on the read's clock** (Q113) — the details' money row says
 * when it is held and when it is taken. The read's state is folded at the two instants it names:
 * a checked share is held at `heldFrom`, and every share is taken at `takenAt`, the cut-off.
 */
describe('shareAt — held, checked or taken (the mechanics §12.2)', () => {
  /** Monday 28 September, 16:00 in Warsaw: four days before the cut-off, the Holding time. */
  const HOLDING = '2026-09-28T14:00:00Z';
  const CHECKED: BookedMoney = { ...HELD, shareState: 'CHECKED', heldFrom: HOLDING };

  it('is held until the cut-off, taken then', () => {
    expect(shareAt(HELD, BEFORE_CUT_OFF)).toEqual({ kind: 'held', takenAt: CUT_OFF });
    expect(shareAt(HELD, Date.parse(CUT_OFF))).toEqual({ kind: 'taken' });
  });

  it('is checked until its holding time, held from it, and taken at the cut-off', () => {
    expect(shareAt(CHECKED, Date.parse(HOLDING) - 1)).toEqual({
      kind: 'checked',
      heldFrom: HOLDING,
      takenAt: CUT_OFF,
    });
    expect(shareAt(CHECKED, Date.parse(HOLDING))).toEqual({ kind: 'held', takenAt: CUT_OFF });
    expect(shareAt(CHECKED, Date.parse(CUT_OFF))).toEqual({ kind: 'taken' });
  });

  it('is taken whenever the read says so', () => {
    expect(shareAt({ shareGrosze: 3000, paid: true }, BEFORE_CUT_OFF)).toEqual({ kind: 'taken' });
    expect(
      shareAt({ shareGrosze: 3000, paid: false, shareState: 'TAKEN', takenAt: CUT_OFF }, 0),
    ).toEqual({ kind: 'taken' });
  });

  it('is nothing while nobody’s money is on the game', () => {
    expect(shareAt({ shareGrosze: 3000, paid: false }, BEFORE_CUT_OFF)).toBeUndefined();
  });
});

/**
 * ***Leave the game* before the cut-off takes nothing** (Q113, the mechanics §13) — and lets go of
 * the hold on the card when there is one: not while the share is only checked, which holds nothing.
 */
describe('leavingAt — what leaving lets go of, now', () => {
  const booked = (money: BookedMoney) => ({
    money,
    leaving: { kind: 'BEFORE_THE_CUT_OFF' as const },
  });

  it('lets the hold go while the share is held', () => {
    expect(leavingAt(booked(HELD), BEFORE_CUT_OFF)).toEqual({
      kind: 'BEFORE_THE_CUT_OFF',
      letsAHoldGo: true,
    });
  });

  it('lets nothing go while the share is only checked — and the hold once it is placed', () => {
    const checked = booked({ ...HELD, shareState: 'CHECKED', heldFrom: '2026-09-28T14:00:00Z' });
    expect(leavingAt(checked, Date.parse('2026-09-27T10:00:00Z'))).toEqual({
      kind: 'BEFORE_THE_CUT_OFF',
      letsAHoldGo: false,
    });
    expect(leavingAt(checked, BEFORE_CUT_OFF)).toEqual({
      kind: 'BEFORE_THE_CUT_OFF',
      letsAHoldGo: true,
    });
  });

  /** The money row turns to *Paid* at the cut-off by itself; what leaving costs turns with it. */
  it('is after the cut-off from the cut-off itself, as the server will say', () => {
    expect(leavingAt(booked(HELD), Date.parse(CUT_OFF))).toEqual({ kind: 'AFTER_THE_CUT_OFF' });
  });

  it('is the read’s own after the cut-off, while the club decides, and where there is no button', () => {
    const late = { money: HELD, leaving: { kind: 'AFTER_THE_CUT_OFF' as const } };
    expect(leavingAt(late, BEFORE_CUT_OFF)).toEqual({ kind: 'AFTER_THE_CUT_OFF' });
    expect(leavingAt({ money: HELD }, BEFORE_CUT_OFF)).toBeUndefined();
  });
});

/** Ivan's 40 zł, 1,76 zł kept on it: what comes back and what was kept make the payment (Q113). */
describe('paymentOf — the payment a late refund is less of', () => {
  it('is what comes back and what was kept, together', () => {
    expect(paymentOf({ backGrosze: 3824, keptGrosze: 176 })).toBe(4000);
  });
});

describe('isNew — marked until opened (the mechanics §11.4)', () => {
  it('is new while its details have never been opened on this phone', () => {
    expect(isNew(game(), new Set())).toBe(true);
    expect(isNew(game(), new Set(['booking-1']))).toBe(false);
  });

  it('is new only while the game is still ahead of its result', () => {
    expect(isNew(game({ status: 'WAITING_FOR_THE_CLUB' }), new Set())).toBe(true);
    expect(isNew(game({ status: 'WAITING_FOR_A_PAYMENT' }), new Set())).toBe(true);
    expect(isNew(game({ status: 'SEAT_OPEN' }), new Set())).toBe(true);
    expect(isNew(game({ status: 'NEEDS_RESULT' }), new Set())).toBe(false);
    expect(isNew(game({ status: 'CALLED_OFF' }), new Set())).toBe(false);
  });

  it('marks nothing new until the phone has said what was opened', () => {
    expect(isNew(game(), undefined)).toBe(false);
  });

  /** *New* marks a game that filled; one gone back to filling is not full any more. */
  it('is not new while the game is filling again, and new once it is full again', () => {
    const fillingAgain = { clubConfirms: true };
    expect(isNew(game({ status: 'SEAT_OPEN', fillingAgain }), new Set())).toBe(false);
    expect(isNew(game({ status: 'WAITING_FOR_THE_CLUB' }), new Set())).toBe(true);
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
    // Nobody paid and nothing is booked yet: the chat opens when it is (Q111).
    ['WAITING_FOR_A_PAYMENT', false],
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
    expect(chatIsOpen({ status })).toBe(open);
  });

  /** No Game and no room: the chat opens when the game is booked, as on *Waiting for the club*. */
  it('has no room on a full game gone back to filling', () => {
    expect(chatIsOpen({ status: 'SEAT_OPEN', fillingAgain: { clubConfirms: true } })).toBe(false);
  });
});

describe('courtIsGiven — a court number once the club has said yes (A4.2)', () => {
  it.each<[HomeStatus, boolean]>([
    ['WAITING_FOR_THE_CLUB', false],
    ['WAITING_FOR_A_PAYMENT', false],
    ['BOOKED', true],
    ['SEAT_OPEN', true],
    ['NEEDS_RESULT', true],
    ['CALLED_OFF', true],
  ])('%s → %s', (status, given) => {
    expect(courtIsGiven({ status })).toBe(given);
  });

  it('gives no court to a full game gone back to filling', () => {
    expect(courtIsGiven({ status: 'SEAT_OPEN', fillingAgain: { clubConfirms: false } })).toBe(
      false,
    );
  });
});

describe('isFillingAgain — a full game gone back to filling, while it fills (Q106)', () => {
  const fillingAgain = { clubConfirms: true };

  it('is a Seat open the read marks filling again', () => {
    expect(isFillingAgain({ status: 'SEAT_OPEN', fillingAgain })).toBe(true);
    expect(isFillingAgain({ status: 'SEAT_OPEN' })).toBe(false);
  });

  /** The wire keeps the mark once it is called off; its way out has gone with it. */
  it('is not one called off before it filled again', () => {
    expect(isFillingAgain({ status: 'CALLED_OFF', fillingAgain })).toBe(false);
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
