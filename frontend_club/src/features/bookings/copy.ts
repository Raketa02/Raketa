/**
 * **Every sentence Bookings says** (the screens B4; the mechanics §16.7–§16.9), Overview's
 * *waiting for your answer* (B2), and how a day, an hour and a game are named.
 */

import { sportName, type Sport } from '@/features/club-details/mappers';
import { MONTHS } from '@/features/courts/copy';
import { sentenceAbout, type RefusalAbout } from '@/ui/forms';
import type { NavItem } from '@/ui/NavLinks';

import type {
  BookingStatus,
  BookingsFilter,
  CalledOffReason,
  CancelReason,
  ClubHour,
  Kind,
} from './mappers';
import { dayAfter, REFUSAL_NOTE_MOST } from './schemas';

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

/** *24:13*: what is left of a countdown, in minutes and seconds, never below nothing. */
export function countdown(ms: number): string {
  const seconds = Math.max(0, Math.ceil(ms / 1000));
  return `${Math.floor(seconds / 60)}:${String(seconds % 60).padStart(2, '0')}`;
}

/** *Padel · Competitive*, *Tennis · Friendly*. */
export function sportAndKind(sport: Sport, kind: Kind): string {
  return `${sportName(sport)} · ${BOOKINGS_COPY.kinds[kind]}`;
}

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
      WAITING_FOR_YOU: 'Waiting for you',
      SEAT_OPEN: 'Seat open',
      CALLED_OFF: 'Called off',
    } satisfies Record<BookingsFilter, string>,
  },
  empty: {
    ALL: 'No Raketa bookings on this day.',
    WAITING_FOR_YOU: 'Nothing on this day is waiting for your answer.',
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
    WAITING_FOR_YOU: 'Waiting for you',
    BOOKED: 'Booked',
    SEAT_OPEN: 'Seat open',
    CALLED_OFF: 'Called off',
    PLAYED: 'Played',
  } satisfies Record<BookingStatus, string>,
  calledOff: {
    REFUSED: 'Refused',
    NO_ANSWER: 'No answer',
    SHORT_AT_THE_CUT_OFF: 'Short at the cut-off',
    CANCELLED_BY_THE_CLUB: 'Cancelled by you',
  } satisfies Record<CalledOffReason, string>,
  cancelReasons: {
    WEATHER: 'Weather',
    REPAIR: 'Repair',
    DOUBLE_BOOKING: 'Double booking',
    OTHER: 'Other',
  } satisfies Record<CancelReason, string>,
  paid: 'paid ✓',
  checkedIn: 'checked in ✓',
  openSeat: 'Open seat',
  /** A player whose account can no longer be named. */
  nameless: 'A player',
  money: { price: 'Price', collected: 'Collected', refunded: 'Refunded' },
  from: {
    official: 'Official group',
    player: 'Player group',
    gone: 'A group that’s gone',
  },
  request: {
    accept: 'Accept',
    refuse: 'Refuse',
    /** The countdown, as it runs. */
    left: (clock: string) => `${clock} left to answer`,
    over: 'Time to answer is over',
  },
  move: 'Move',
  cancel: 'Cancel',
  refuseDialog: {
    title: (game: string) => `Refuse ${game}?`,
    lead:
      'Nobody has paid. The players read “Called off · refused” and are offered another game ' +
      'first, never at this court hour. The hour is yours to sell again.',
    note: 'Note',
    noteHint: 'For your own records: the players never see it.',
    back: 'Back',
    confirm: 'Refuse',
  },
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
    reasonHint: 'The players are told it, with their refund.',
    consequence:
      'Everyone is refunded in full; the card fees are not returned. It goes on nobody’s ' +
      'record, the players are offered another game first, and the hour is yours to sell again.',
    back: 'Keep the game',
    confirm: 'Cancel the booking',
  },
  done: {
    accepted: (game: string, court: string) =>
      `${opening(game)} is booked on ${court}. Everybody paid.`,
    seatOpened: (game: string) =>
      `A player’s payment didn’t go through for ${game}, so nobody paid. It is looking for a ` +
      'player again, and you’ll be asked again once it’s full.',
    refused: (game: string) =>
      `You refused ${game}. Nobody paid, and the hour is yours to sell again.`,
    moved: (game: string, court: string) =>
      `${opening(game)} is on ${court} now. The players see the new court.`,
    cancelled: (game: string) => `You cancelled ${game}. Everyone is refunded in full.`,
  },
  waiting: {
    title: 'Waiting for your answer',
    lead:
      'Full games asking for one of your courts. Nobody pays until you accept, and a request ' +
      'not answered in time is called off.',
    none: 'Nothing is waiting for you.',
    /** *140 zł · 35 zł each*. */
    price: (price: string, share: string) => `${price} · ${share} each`,
  },
} as const;

/**
 * **The top bar's coral count on Bookings**, while requests wait for an answer (the screens B1),
 * with what it counts as a screen reader reads it; nothing while none waits.
 */
export function requestsBadge(count: number): Pick<NavItem, 'badge'> {
  return count > 0 ? { badge: { count, label: `${count} waiting for your answer` } } : {};
}

/** What can be refused about an act on a game, said about the game the desk saw. */
const ACT_REFUSALS: Readonly<Record<string, (game: string) => string>> = {
  booking_not_found: (game) => `${opening(game)} isn’t one of your bookings any more.`,
  request_not_waiting: (game) =>
    `${opening(game)} isn’t waiting for your answer any more: it was answered already, or a ` +
    'player left and it is looking for a player again.',
  request_timed_out: (game) =>
    `Your time to answer ${game} ran out: it was called off as unanswered.`,
  payments_unavailable: (game) =>
    `We couldn’t reach the payment provider to charge the players for ${game}. Nothing was ` +
    'recorded; try again.',
  booking_not_booked: (game) => `${opening(game)} is waiting for your answer: accept or refuse it.`,
  booking_is_called_off: (game) => `${opening(game)} is called off already.`,
  game_has_started: (game) =>
    `${opening(game)} has started, so it can’t be moved or cancelled any more.`,
  court_not_free: (game) => `That court isn’t free for ${game} any more. Choose another.`,
  court_just_taken: (game) =>
    `Another game took that court a moment ago. Move ${game} again to see the courts still free.`,
  court_required: () => 'Choose the court to move it to.',
  cancel_reason_required: () => 'Choose why you’re cancelling: the players are told it.',
  refusal_note_too_long: () => `Keep the note to ${REFUSAL_NOTE_MOST} characters.`,
};

/** The sentence for a refusal of an act on a game. */
export function actRefusal(refusal: RefusalAbout): string {
  return sentenceAbout(refusal, ACT_REFUSALS);
}
