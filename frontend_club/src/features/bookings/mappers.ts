/**
 * **The club's bookings, wire to view and back.** The only file in this feature that imports a
 * generated type (ADR-0187 §6); everything else reads the view models it makes.
 */

import type { components } from '@/generated/schema';
import type { Sport } from '@/features/club-details/mappers';
import { CLUB_ZONE, clubDay } from '@/features/courts/mappers';

type WireDay = components['schemas']['ClubBookingsResponse'];
type WireBooking = components['schemas']['ClubBookingSchema'];
type WireWaitingList = components['schemas']['WaitingBookingsResponse'];
type WireWaiting = components['schemas']['WaitingBookingSchema'];
type WireAcceptance = components['schemas']['AcceptanceResponse'];
type WireFreeCourts = components['schemas']['FreeCourtsResponse'];
type WireRefusalBody = components['schemas']['RefusalRequest'];
type WireMoveBody = components['schemas']['MoveRequest'];
type WireCancelBody = components['schemas']['CancelRequest'];

/** What a booking is to the club right now (the mechanics §16.7). */
export type BookingStatus = components['schemas']['ClubStatus'];

/** Competitive, or for fun: a friendly. */
export type Kind = components['schemas']['SearchMode'];

/** Why a game will not be played. */
export type CalledOffReason = components['schemas']['CalledOffReason'];

/** Why the club cancelled a game: the players are told it with their refund (§16.9). */
export type CancelReason = components['schemas']['ClubCancelReason'];

/** Which of the day's bookings the page shows: all, or one status. */
export type BookingsFilter = components['schemas']['ClubFilter'];

/**
 * The filters, in the order the page offers them. A `Record` over the wire's enum, so a fifth
 * fails to compile here until the page has a place for it.
 */
const KNOWN_FILTERS: Readonly<Record<BookingsFilter, true>> = {
  ALL: true,
  WAITING_FOR_YOU: true,
  SEAT_OPEN: true,
  CALLED_OFF: true,
};

export const FILTERS = Object.keys(KNOWN_FILTERS) as readonly BookingsFilter[];

/** The reasons a club cancels with, in the order the dialog offers them. */
const KNOWN_CANCEL_REASONS: Readonly<Record<CancelReason, true>> = {
  WEATHER: true,
  REPAIR: true,
  DOUBLE_BOOKING: true,
  OTHER: true,
};

export const CANCEL_REASONS = Object.keys(KNOWN_CANCEL_REASONS) as readonly CancelReason[];

export function isCancelReason(value: unknown): value is CancelReason {
  return typeof value === 'string' && value in KNOWN_CANCEL_REASONS;
}

/** **An hour at the club**: its local day and the wall clock it starts and ends at. */
export interface ClubHour {
  /** The local day, `2026-10-12`. */
  readonly day: string;
  /** `19:00`. */
  readonly from: string;
  /** `20:00`. */
  readonly until: string;
}

const CLOCK = new Intl.DateTimeFormat('en-GB', {
  timeZone: CLUB_ZONE,
  hourCycle: 'h23',
  hour: '2-digit',
  minute: '2-digit',
});

/** **The club's clock at an instant** the wire wrote: `18:52`. */
export function clubClock(instant: string): string {
  return CLOCK.format(Date.parse(instant));
}

/** The club's hour from the wire's two instants. */
export function clubHour(startsAt: string, endsAt: string): ClubHour {
  return {
    day: clubDay(Date.parse(startsAt)),
    from: clubClock(startsAt),
    until: clubClock(endsAt),
  };
}

/** A player on a game, as the club sees them: a name, and whether they paid and were checked in. */
export interface BookingPlayer {
  readonly id: string;
  /** `null` for an account that can no longer be named. */
  readonly name: string | null;
  readonly paid: boolean;
  readonly checkedIn: boolean;
}

/** The group a game was booked in: one of the club's official groups, or a player group. */
export interface BookedFrom {
  readonly name: string;
  readonly official: boolean;
}

/**
 * **A request's clock**: when its answer is due, and when the page read it. The countdown runs
 * from the difference, so a browser's clock set wrong cannot shorten or lengthen it.
 */
export interface AnswerBy {
  readonly at: number;
  readonly readAt: number;
}

/**
 * **The one payment the club's yes waits on** (the mechanics §16.8): due by `until` on the
 * club's clock, and never whose. When it is due, and when the page read it, are kept as a
 * request's clock is, so the page reads itself again once the time comes.
 */
export interface PaymentDue {
  /** `21:20`. */
  readonly until: string;
  readonly at: number;
  readonly readAt: number;
}

/** **One Raketa booking at the club**, as a row of the Bookings page draws it. */
export interface Booking {
  readonly id: string;
  readonly hour: ClubHour;
  readonly court: string;
  readonly sport: Sport;
  readonly kind: Kind;
  readonly status: BookingStatus;
  /** Why it is called off, and the club's reason when the club cancelled it. */
  readonly calledOff: {
    readonly reason: CalledOffReason;
    readonly cancel: CancelReason | null;
  } | null;
  /** The first side first. */
  readonly players: readonly BookingPlayer[];
  readonly openSeats: number;
  readonly money: {
    readonly priceGrosze: number;
    readonly collectedGrosze: number;
    readonly refundedGrosze: number;
  };
  /** `null` for a group that is gone. */
  readonly from: BookedFrom | null;
  /** While it waits for the club's answer; `null` otherwise. */
  readonly answerBy: AnswerBy | null;
  /** While the club's yes waits on one player's payment; `null` otherwise. */
  readonly paymentDue: PaymentDue | null;
  /** **Move** and **Cancel** are the club's: booked or with a seat open, and not started. */
  readonly mayMoveOrCancel: boolean;
}

/** **One day of the club's bookings**, under one filter, with every filter's count for the day. */
export interface BookingsDay {
  /** The local day read, `2026-10-12`. */
  readonly day: string;
  /** The local day at the club now: the page says *Today*, *Tomorrow* or *Yesterday* by it. */
  readonly today: string;
  readonly filter: BookingsFilter;
  readonly counts: Readonly<Record<BookingsFilter, number>>;
  /** Soonest first. */
  readonly bookings: readonly Booking[];
}

function toBooking(wire: WireBooking, readAt: number): Booking {
  return {
    id: wire.booking_id,
    hour: clubHour(wire.starts_at, wire.ends_at),
    court: wire.court_name,
    sport: wire.sport,
    kind: wire.kind,
    status: wire.status,
    calledOff:
      wire.called_off_reason === null
        ? null
        : { reason: wire.called_off_reason, cancel: wire.cancel_reason },
    players: wire.players.map((player) => ({
      id: player.player_id,
      name: player.name,
      paid: player.paid,
      checkedIn: player.checked_in_at !== null,
    })),
    openSeats: wire.open_seats,
    money: {
      priceGrosze: wire.money.price_grosze,
      collectedGrosze: wire.money.collected_grosze,
      refundedGrosze: wire.money.refunded_grosze,
    },
    from:
      wire.booked_from === null
        ? null
        : { name: wire.booked_from.name, official: wire.booked_from.official },
    answerBy: wire.answer_by === null ? null : { at: Date.parse(wire.answer_by), readAt },
    paymentDue:
      wire.payment_due_by === null
        ? null
        : {
            until: clubClock(wire.payment_due_by),
            at: Date.parse(wire.payment_due_by),
            readAt,
          },
    mayMoveOrCancel: wire.may_move_or_cancel,
  };
}

export function toBookingsDay(wire: WireDay, today: string): BookingsDay {
  const readAt = Date.parse(wire.read_at);
  return {
    day: wire.day,
    today,
    filter: wire.filter,
    counts: {
      ALL: wire.counts.all,
      WAITING_FOR_YOU: wire.counts.waiting_for_you,
      SEAT_OPEN: wire.counts.seat_open,
      CALLED_OFF: wire.counts.called_off,
    },
    bookings: wire.bookings.map((each) => toBooking(each, readAt)),
  };
}

/** **A full game asking for a court**, as Overview lists it: nobody has paid yet. */
export interface WaitingRequest {
  readonly id: string;
  readonly hour: ClubHour;
  readonly court: string;
  readonly sport: Sport;
  readonly kind: Kind;
  /** Their names; `null` for an account that can no longer be named. */
  readonly players: readonly (string | null)[];
  readonly priceGrosze: number;
  readonly shareGrosze: number;
  readonly answerBy: AnswerBy;
}

/** Everything waiting for the club's answer, the one due first, first. */
export function toRequests(wire: WireWaitingList): readonly WaitingRequest[] {
  const readAt = Date.parse(wire.read_at);
  return wire.bookings.map((each: WireWaiting) => ({
    id: each.booking_id,
    hour: clubHour(each.starts_at, each.ends_at),
    court: each.court_name,
    sport: each.sport,
    kind: each.kind,
    players: each.players.map((player) => player.name),
    priceGrosze: each.price_grosze,
    shareGrosze: each.share_grosze,
    answerBy: { at: Date.parse(each.answer_by), readAt },
  }));
}

/**
 * **What the club's yes came to**: booked, everybody paid, on that court; accepted and waiting
 * on one player's payment until a time on the club's clock, the court kept for it; called off,
 * because that payment had no time left to come; or a player who could no longer be on the
 * game, so nobody paid and it is looking for a player again.
 */
export type Accepted =
  | { readonly outcome: 'BOOKED'; readonly court: string }
  | { readonly outcome: 'WAITING_FOR_A_PAYMENT'; readonly until: string }
  | { readonly outcome: 'CALLED_OFF' }
  | { readonly outcome: 'SEAT_OPENED' };

/**
 * The court comes with `BOOKED` and the time with `WAITING_FOR_A_PAYMENT`, as the contract says.
 * A reply without one is a backend that broke it, and no sentence the desk could be told about
 * it is true: `null`.
 */
export function toAccepted(wire: WireAcceptance): Accepted | null {
  switch (wire.outcome) {
    case 'BOOKED':
      return wire.court_name === null ? null : { outcome: 'BOOKED', court: wire.court_name };
    case 'WAITING_FOR_A_PAYMENT':
      return wire.payment_due_by == null
        ? null
        : { outcome: 'WAITING_FOR_A_PAYMENT', until: clubClock(wire.payment_due_by) };
    case 'CALLED_OFF':
    case 'SEAT_OPENED':
      return { outcome: wire.outcome };
  }
}

/** A court a game can be moved to: another of its sport, free at its hour. */
export interface FreeCourt {
  readonly id: string;
  readonly name: string;
}

export function toFreeCourts(wire: WireFreeCourts): readonly FreeCourt[] {
  return wire.courts.map((each) => ({ id: each.court_id, name: each.name }));
}

/** A refusal's note, for the club's own records: blank is no note. */
export function toRefusalBody(note: string): WireRefusalBody {
  return { reason: note === '' ? null : note };
}

export function toMoveBody(courtId: string): WireMoveBody {
  return { court_id: courtId };
}

export function toCancelBody(reason: CancelReason): WireCancelBody {
  return { reason };
}
