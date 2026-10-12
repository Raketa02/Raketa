/**
 * **Every sentence Bookings says** (the screens B4; the mechanics §16.7, §16.9 and §16.16), and
 * how a day, an hour and a game are named.
 */

import { sportName, type Sport } from '@/features/club-details/mappers';
import { MONTHS } from '@/features/courts/copy';
import { formatZloty } from '@/ui/format';
import { sentenceAbout, type RefusalAbout } from '@/ui/forms';

import type {
  BookingStatus,
  BookingsFilter,
  CalledOffReason,
  CancelGivesBack,
  CancelReason,
  ClubHour,
  Kind,
  Share,
} from './mappers';
import { dayAfter } from './schemas';

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

/** What came of the players' money, once a cancel landed. */
const CANCELLED_MONEY = {
  HOLDS_LET_GO: 'Every hold is let go: nobody pays.',
  REFUNDED_IN_FULL: 'Everyone is refunded in full.',
} as const satisfies Record<CancelGivesBack, string>;

/** What a cancel comes to beyond the money, either side of the cut-off (the mechanics §16.9). */
const CANCEL_AFTERMATH =
  'It goes on nobody’s record, the players are offered another game first, and the hour is ' +
  'yours to sell again.';

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
  /** A player's share, under their name (Q113): held on their card until the cut-off, or taken. */
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
      `It is on ${court}. The players see the new court; nothing else about the game changes.`,
    to: 'Move it to',
    reading: 'Finding the free courts…',
    none: (sport: string, clock: string) =>
      `No other ${sport} court is free at ${clock}. If the court can’t be played, cancel the ` +
      'game with “Repair”.',
    back: 'Back',
    confirm: 'Move',
  },
  cancelDialog: {
    title: (game: string) => `Cancel ${game}?`,
    reason: 'Why',
    reasonHint: 'The players are told it, with what comes of their money.',
    /** Before the cut-off, and after it (the mechanics §16.9). */
    consequence: {
      HOLDS_LET_GO: `Every hold is let go and nobody pays a fee. ${CANCEL_AFTERMATH}`,
      REFUNDED_IN_FULL: `Everyone is refunded in full; the card fees are not returned. ${CANCEL_AFTERMATH}`,
    } satisfies Record<CancelGivesBack, string>,
    back: 'Keep the game',
    confirm: 'Cancel the booking',
  },
  done: {
    moved: (game: string, court: string) =>
      `${opening(game)} is on ${court} now. The players see the new court.`,
    /** With what the dialog said of the money, when the page said it. */
    cancelled: (game: string, givesBack: CancelGivesBack | null) =>
      `You cancelled ${game}.${givesBack === null ? '' : ` ${CANCELLED_MONEY[givesBack]}`}`,
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

/** The sentence for a refusal of an act on a game. */
export function actRefusal(refusal: RefusalAbout): string {
  return sentenceAbout(refusal, ACT_REFUSALS);
}
