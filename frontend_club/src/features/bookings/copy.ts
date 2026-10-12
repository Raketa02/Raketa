/**
 * **Every sentence Bookings says** (the screens B4; the mechanics §16.7–§16.9), Overview's
 * *waiting for your answer* (B2), and how a day, an hour and a game are named.
 */

import { sportName, type Sport } from '@/features/club-details/mappers';
import { MONTHS } from '@/features/courts/copy';
import { formatZloty } from '@/ui/format';
import { sentenceAbout, type RefusalAbout } from '@/ui/forms';
import type { NavItem } from '@/ui/NavLinks';

import type {
  BookingStatus,
  BookingsFilter,
  CalledOffReason,
  CancelGivesBack,
  CancelReason,
  ClubHour,
  Kind,
  Share,
  TimeTo,
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
    WAITING_FOR_A_PAYMENT: 'Accepted',
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
    PAYMENT_NOT_IN_TIME: 'Payment didn’t come in time',
  } satisfies Record<CalledOffReason, string>,
  /**
   * Under *Accepted*, while the club's yes waits on one player, never whose: their card to be
   * fixed before the cut-off, their payment after it (the mechanics §16.8).
   */
  waitingFor: {
    FIX_THE_CARD: (until: string) => `Waiting for one player’s card until ${until}`,
    PAY: (until: string) => `Waiting for one player’s payment until ${until}`,
  } satisfies Record<TimeTo, (until: string) => string>,
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
    /** What the players read, word for word (the mechanics §16.8). */
    lead: (clubName: string) =>
      `Nobody has paid. The players read “${clubName} said no” and “Nobody paid — you’ll get a ` +
      'new card first”: they are offered another game first, never at this court hour. The ' +
      'hour is yours to sell again.',
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
    /** The reply names no cut-off, so the sentence is true on either side of it (Q113). */
    accepted: (game: string, court: string) =>
      `${opening(game)} is booked on ${court}. The shares are held now and taken at your ` +
      'cut-off, or taken at once if it has passed.',
    /**
     * A yes that met a refused card: the court is kept for that player's time to fix it (before
     * the cut-off) or to pay (after it).
     */
    acceptedWaitingFor: {
      FIX_THE_CARD: (game: string, until: string) =>
        `You accepted ${game}. One player’s card is still to be fixed, until ${until}: the ` +
        'court is kept for it, and once it’s fixed the game is booked. If it isn’t, the game is ' +
        'called off and you’re emailed.',
      PAY: (game: string, until: string) =>
        `You accepted ${game}. One player’s payment is still to come, until ${until}: the court ` +
        'is kept for it, and once it’s in the game is booked. If it doesn’t come, the game is ' +
        'called off and you’re emailed.',
    } satisfies Record<TimeTo, (game: string, until: string) => string>,
    /** A yes that met a refused payment when the game's last moment to book had come. */
    noTimeToPay: (game: string) =>
      `A player’s payment didn’t go through for ${game}, and there was no time left to pay, so ` +
      'it is called off. Nobody paid, and the hour is yours to sell again.',
    seatOpened: (game: string) =>
      `One of the players can no longer play ${game}, so nobody paid. It is looking for a ` +
      'player again, and you’ll be asked again once it’s full.',
    refused: (game: string) =>
      `You refused ${game}. Nobody paid, and the hour is yours to sell again.`,
    moved: (game: string, court: string) =>
      `${opening(game)} is on ${court} now. The players see the new court.`,
    /** With what the dialog said of the money, when the page said it. */
    cancelled: (game: string, givesBack: CancelGivesBack | null) =>
      `You cancelled ${game}.${givesBack === null ? '' : ` ${CANCELLED_MONEY[givesBack]}`}`,
  },
  waiting: {
    title: 'Waiting for your answer',
    /** What a request left unanswered comes to, in the players' own words (the mechanics §16.8). */
    lead: (clubName: string) =>
      'Full games asking for one of your courts. Nobody has paid: the shares are held when you ' +
      'accept and taken at your cut-off. A request not answered in time is called off: the ' +
      `players read “${clubName} didn’t answer in time”.`,
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

/**
 * What can be refused about an act on a game, said about the game the desk saw, by the club
 * whose name the players read.
 */
const actRefusals = (clubName: string): Readonly<Record<string, (game: string) => string>> => ({
  booking_not_found: (game) => `${opening(game)} isn’t one of your bookings any more.`,
  request_not_waiting: (game) =>
    `${opening(game)} isn’t waiting for your answer any more: it was answered already, or a ` +
    'player left and it is looking for a player again.',
  request_timed_out: (game) =>
    `Your time to answer ${game} ran out: it was called off as unanswered, and the players ` +
    `read “${clubName} didn’t answer in time”.`,
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
});

/** The sentence for a refusal of an act on a game, at the club named `clubName`. */
export function actRefusal(refusal: RefusalAbout, clubName: string): string {
  return sentenceAbout(refusal, actRefusals(clubName));
}
