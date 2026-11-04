/**
 * **Every sentence Bookings says** (the screens B4; the mechanics §16.7, §16.9 and §16.16), and
 * how a day, an hour, a game and a court are named.
 */

import { sportName, type Sport } from '@/features/club-details/mappers';
import { MONTHS } from '@/features/courts/copy';
import { formatZloty } from '@/ui/format';
import { sentenceAbout } from '@/ui/forms';

import type {
  BookingStatus,
  BookingsFilter,
  CalledOffReason,
  CancelGivesBack,
  CancelReason,
  ClubHour,
  GameCourt,
  Kind,
  Share,
} from './mappers';
import { dayAfter, type ActRefused } from './schemas';

const WEEKDAYS = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];

/** *Sat 3 Oct*, from a local day `2026-10-03`. */
export function shortDay(day: string): string {
  const [year = 0, month = 1, date = 1] = day.split('-').map(Number);
  const weekday = new Date(Date.UTC(year, month - 1, date)).getUTCDay();
  return `${WEEKDAYS[weekday]} ${date} ${MONTHS[month - 1]}`;
}

/** *Today · Fri 2 Oct*, *Tomorrow · Sat 3 Oct*, *Yesterday · Thu 1 Oct*, or *Mon 12 Oct*. */
export function dayTitle(day: string, today: string): string {
  const near: Readonly<Record<string, string>> = {
    [today]: 'Today',
    [dayAfter(today, 1)]: 'Tomorrow',
    [dayAfter(today, -1)]: 'Yesterday',
  };
  const name = near[day];
  return name === undefined ? shortDay(day) : `${name} · ${shortDay(day)}`;
}

/** **A game, as a sentence names it**: *the 19:00 game on Sat 3 Oct*. */
export function gameName(hour: ClubHour): string {
  return `the ${hour.from} game on ${shortDay(hour.day)}`;
}

/** A sentence's first word, as it opens one. */
function opening(words: string): string {
  return words.charAt(0).toUpperCase() + words.slice(1);
}

/**
 * **A sum of the club's money, or *Not yet known*** while Stripe has not said a fee it depends on
 * (#641). Never an estimate.
 */
export function knownZloty(grosze: number | null): string {
  return grosze === null ? 'Not yet known' : formatZloty(grosze);
}

/** *Padel · Competitive*, *Tennis · Friendly*. */
export function sportAndKind(sport: Sport, kind: Kind): string {
  return `${sportName(sport)} · ${BOOKINGS_COPY.kinds[kind]}`;
}

/**
 * **A court as the players read it**, with its kind of court: *Court 3 · indoor* (Q122). Not a
 * game's kind, which is competitive or friendly.
 */
export function courtWithKind(court: GameCourt): string {
  return `${court.name} · ${court.indoor ? 'indoor' : 'outdoor'}`;
}

/** What came of the players' money, once a cancel called the game off. */
const CANCELLED_MONEY = {
  HOLDS_LET_GO: 'Every hold is let go: nobody pays.',
  REFUNDED_IN_FULL: 'Everyone is refunded in full.',
} as const satisfies Record<CancelGivesBack, string>;

/** What calling a game off does with the players' money, either side of the cut-off (§16.9). */
const CALLED_OFF_MONEY = {
  HOLDS_LET_GO: 'every hold is let go and nobody pays a fee',
  REFUNDED_IN_FULL: 'everyone is refunded in full; the card fees are not returned',
} as const satisfies Record<CancelGivesBack, string>;

/** What a cancel comes to beyond the money, either side of the cut-off (the mechanics §16.9). */
const CANCEL_AFTERMATH =
  'It goes on nobody’s record, the players are offered another game first, and the hour is ' +
  'yours to sell again.';

/** What a move by cancel comes to: nothing about the money changes (Q122). */
const MOVED_BY_CANCEL = 'the players are told, and nobody is refunded.';

/** What a cancel came to, beyond the game it was about. */
function cancelledMoney(givesBack: CancelGivesBack | null): string {
  return givesBack === null ? '' : ` ${CANCELLED_MONEY[givesBack]}`;
}

/** The button that calls a game off though another court would take it. */
const ANYWAY = 'Cancel the game anyway';

export const BOOKINGS_COPY = {
  caption: 'Raketa games at your courts',
  title: 'Bookings',
  day: {
    /** The day's controls, as a screen reader names them. */
    label: 'Day',
    previous: 'Previous day',
    next: 'Next day',
    today: 'Today',
    pick: 'Go to a day',
    show: 'Show',
  },
  filters: {
    label: 'Filter bookings',
    names: {
      ALL: 'All',
      SEAT_OPEN: 'Seat open',
      CALLED_OFF: 'Called off',
    } satisfies Record<BookingsFilter, string>,
  },
  empty: {
    ALL: 'No Raketa bookings on this day.',
    SEAT_OPEN: 'No game on this day has a seat open.',
    CALLED_OFF: 'No game on this day was called off.',
  } satisfies Record<BookingsFilter, string>,
  columns: {
    when: 'When · court',
    sport: 'Sport · kind',
    players: 'Players',
    status: 'Status',
    money: 'Money',
    from: 'Where it came from',
    actions: 'Actions',
  },
  kinds: { COMPETITIVE: 'Competitive', FOR_FUN: 'Friendly' } satisfies Record<Kind, string>,
  statuses: {
    BOOKED: 'Booked',
    SEAT_OPEN: 'Seat open',
    CALLED_OFF: 'Called off',
    PLAYED: 'Played',
  } satisfies Record<BookingStatus, string>,
  calledOff: {
    SHORT_AT_THE_CUT_OFF: 'Short at the cut-off',
    CANCELLED_BY_THE_CLUB: 'Cancelled by you',
  } satisfies Record<CalledOffReason, string>,
  cancelReasons: {
    WEATHER: 'Weather',
    REPAIR: 'Repair',
    DOUBLE_BOOKING: 'Double booking',
    OTHER: 'Other',
  } satisfies Record<CancelReason, string>,
  /**
   * A player's share, under their nickname (Q113): held on their card until the cut-off, or
   * taken.
   */
  shares: { HELD: 'held', TAKEN: 'taken' } satisfies Record<Share, string>,
  openSeat: 'Open seat',
  /** A player whose account can no longer be named. */
  nameless: 'A player',
  money: { price: 'Price', collected: 'Collected', refunded: 'Refunded' },
  from: {
    official: 'Official group',
    player: 'Player group',
    gone: 'A group that’s gone',
  },
  move: 'Move',
  cancel: 'Cancel',
  moveDialog: {
    title: (game: string) => `Move ${game}`,
    lead: (court: string) =>
      `It is on ${court}. The players are told the new court; nothing else about the game ` +
      'changes.',
    to: 'Move it to',
    reading: 'Finding the free courts…',
    /** An indoor game goes only indoors; an outdoor one to any court of its sport. */
    none: (sport: string, clock: string, indoor: boolean) =>
      `No other ${indoor ? 'indoor ' : ''}${sport} court is free at ${clock}. If the court ` +
      'can’t be played, cancel the game with “Repair”.',
    back: 'Back',
    confirm: 'Move',
  },
  cancelDialog: {
    title: (game: string) => `Cancel ${game}?`,
    reason: 'Why',
    reasonHint: 'The players are told it, with what comes of their game.',
    reading: 'Finding what this cancel would do…',
    /** Another of the club's courts takes the game (Q122). */
    moves: (court: string) =>
      `This game moves to ${court} · the players are told, nobody is refunded.`,
    anyway: (givesBack: CancelGivesBack) =>
      `“${ANYWAY}” calls it off instead, for an hour you’re closing whole: ` +
      `${CALLED_OFF_MONEY[givesBack]}.`,
    /** No court takes it: before the cut-off, and after it (the mechanics §16.9). */
    calledOff: (givesBack: CancelGivesBack) =>
      `This game is called off: ${CALLED_OFF_MONEY[givesBack]}. ${CANCEL_AFTERMATH}`,
    back: 'Keep the game',
    confirm: 'Cancel the booking',
    confirmAnyway: ANYWAY,
  },
  /**
   * What landed. A cancel decides afresh when the desk confirms, so what it came to is said
   * against what the dialog said: a court taken, or come free, in between.
   */
  done: {
    moved: (game: string, court: string) =>
      `${opening(game)} is on ${court} now, and the players are told.`,
    movedByCancel: (game: string, court: string) =>
      `${opening(game)} moved to ${court}: ${MOVED_BY_CANCEL}`,
    /** The court the dialog named went to another game, and another took this one. */
    movedInstead: (said: string, game: string, court: string) =>
      `${said} was taken a moment ago, so ${game} moved to ${court}: ${MOVED_BY_CANCEL}`,
    /** The dialog said called off, and a court came free. */
    movedAfterAll: (game: string, court: string) =>
      `A court came free a moment ago, so ${game} moved to ${court}: ${MOVED_BY_CANCEL}`,
    /** With what the dialog said of the money, when the page said it. */
    calledOff: (game: string, givesBack: CancelGivesBack | null) =>
      `${opening(game)} is called off.${cancelledMoney(givesBack)}`,
    /** The court the dialog named went to another game, and none took this one. */
    calledOffInstead: (said: string, game: string, givesBack: CancelGivesBack | null) =>
      `${said} was taken a moment ago, so ${game} is called off.${cancelledMoney(givesBack)}`,
  },
} as const;

/** What can be refused about an act on a game, said about the game the desk saw. */
const ACT_REFUSALS: Readonly<Record<string, (game: string) => string>> = {
  booking_not_found: (game) => `${opening(game)} isn’t one of your bookings any more.`,
  booking_is_called_off: (game) => `${opening(game)} is called off already.`,
  game_has_started: (game) =>
    `${opening(game)} has started, so it can’t be moved or cancelled any more.`,
  court_not_free: (game) => `That court isn’t free for ${game} any more. Choose another.`,
  court_just_taken: (game) =>
    `Another game took that court a moment ago. Move ${game} again to see the courts still free.`,
  court_required: () => 'Choose the court to move it to.',
  cancel_reason_required: () => 'Choose why you’re cancelling: the players are told it.',
};

/** A cancel's own: the court it found is the one taken, not one the desk chose. */
const CANCEL_REFUSALS: Readonly<Record<string, (game: string) => string>> = {
  ...ACT_REFUSALS,
  court_just_taken: (game) =>
    `The court that would have taken ${game} went to another game a moment ago. Cancel it ` +
    'again to see what a cancel does now.',
};

/** The sentence for a refusal of an act on a game. */
export function actRefusal(refusal: ActRefused): string {
  return sentenceAbout(refusal, refusal.act === 'cancel' ? CANCEL_REFUSALS : ACT_REFUSALS);
}
